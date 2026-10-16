"""
MK1300 V2 HID Protocol Driver for Linux.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: JS/WebHID to Python/hidapi port for mk1300-linux

SAFETY: Command byte 85 (0x55) and factory reset sub-command [15, 255] are hard-blocked.
Only per-key RGB and hardware-animation commands are permitted.
"""

import ctypes
import glob
import math
import os
import select
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import hid
except ImportError:
    hid = None

from .layout import KEY_COUNT, KEYBOARD_LAYOUT

# Safety blocks
BLOCKED_COMMANDS = {85}  # 0x55: firmware / bootloader
BLOCKED_SUBCOMMANDS = [(15, 255)]  # factory reset

TARGET_VIDS = [
    0x36AE,
    0x6D7B,
    0x6D7C,
    0x6D7D,
    0x6D7E,
    0x6D7F,
    0x6D80,
    0x6D81,
    0x6D82,
    0x6D83,
    0x68BD,
    0x0816,
    0x0817,
    0x0818,
    0x0819,
    0x7DFA,
    0x08A3,
    0x342D,
    0x9A9A,
]
TARGET_PID = 0xFE9C
VENDOR_USAGE_PAGE = 0xFF00
VENDOR_USAGE = 0x02

# ── Native libhidapi-hidraw.so support via ctypes ────────────────────────────
_hidraw_lib = None
try:
    for candidate in ("/usr/lib/libhidapi-hidraw.so.0", "/usr/lib/libhidapi-hidraw.so", "libhidapi-hidraw.so"):
        try:
            _hidraw_lib = ctypes.cdll.LoadLibrary(candidate)
            _hidraw_lib.hid_init()
            break
        except Exception:
            pass
except Exception:
    _hidraw_lib = None


class _CtypesHidDeviceInfo(ctypes.Structure):
    pass


if _hidraw_lib:
    _CtypesHidDeviceInfo._fields_ = [
        ("path", ctypes.c_char_p),
        ("vendor_id", ctypes.c_ushort),
        ("product_id", ctypes.c_ushort),
        ("serial_number", ctypes.c_wchar_p),
        ("release_number", ctypes.c_ushort),
        ("manufacturer_string", ctypes.c_wchar_p),
        ("product_string", ctypes.c_wchar_p),
        ("usage_page", ctypes.c_ushort),
        ("usage", ctypes.c_ushort),
        ("interface_number", ctypes.c_int),
        ("next", ctypes.POINTER(_CtypesHidDeviceInfo)),
    ]
    _hidraw_lib.hid_enumerate.argtypes = [ctypes.c_ushort, ctypes.c_ushort]
    _hidraw_lib.hid_enumerate.restype = ctypes.POINTER(_CtypesHidDeviceInfo)
    _hidraw_lib.hid_free_enumeration.argtypes = [ctypes.POINTER(_CtypesHidDeviceInfo)]
    _hidraw_lib.hid_free_enumeration.restype = None
    _hidraw_lib.hid_open_path.argtypes = [ctypes.c_char_p]
    _hidraw_lib.hid_open_path.restype = ctypes.c_void_p
    _hidraw_lib.hid_write.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
    _hidraw_lib.hid_write.restype = ctypes.c_int
    _hidraw_lib.hid_read_timeout.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t, ctypes.c_int]
    _hidraw_lib.hid_read_timeout.restype = ctypes.c_int
    _hidraw_lib.hid_close.argtypes = [ctypes.c_void_p]
    _hidraw_lib.hid_close.restype = None
    _hidraw_lib.hid_error.argtypes = [ctypes.c_void_p]
    _hidraw_lib.hid_error.restype = ctypes.c_wchar_p


class LinuxHidrawDirectDevice:
    """Robust native Linux /dev/hidraw character device using POSIX system calls."""

    def __init__(self, path: str):
        self.path = path
        self.fd: Optional[int] = os.open(path, os.O_RDWR | os.O_NONBLOCK)

    def write(self, data: bytes) -> int:
        if self.fd is None:
            raise OSError("Device closed")
        try:
            return os.write(self.fd, data)
        except (BlockingIOError, InterruptedError):
            _, w, _ = select.select([], [self.fd], [], 1.0)
            if w:
                return os.write(self.fd, data)
            raise TimeoutError("Write timeout on hidraw")

    def read(self, length: int = 64, timeout_ms: int = 1000) -> bytes:
        if self.fd is None:
            return b""
        timeout_sec = max(0.001, timeout_ms / 1000.0)
        r, _, _ = select.select([self.fd], [], [], timeout_sec)
        if r:
            try:
                return os.read(self.fd, length)
            except Exception:
                return b""
        return b""

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None


class HidrawNativeDevice:
    """Device wrapper around native libhidapi-hidraw.so."""

    def __init__(self, lib, handle: int, path: bytes):
        self.lib = lib
        self.handle = handle
        self.path = path

    def write(self, data: bytes) -> int:
        buf = (ctypes.c_ubyte * len(data))(*data)
        res = self.lib.hid_write(self.handle, buf, len(data))
        if res < 0:
            err = ""
            if hasattr(self.lib, "hid_error"):
                try:
                    err = self.lib.hid_error(self.handle) or ""
                except Exception:
                    pass
            raise OSError(f"hid_write failed on native hidraw ({err or 'write error'})")
        return res

    def read(self, length: int = 64, timeout_ms: int = 1000) -> bytes:
        buf = (ctypes.c_ubyte * length)()
        res = self.lib.hid_read_timeout(self.handle, buf, length, timeout_ms)
        if res < 0:
            return b""
        return bytes(buf[:res])

    def close(self):
        if self.handle:
            self.lib.hid_close(self.handle)
            self.handle = None


class HIDDriver:
    """HID Driver for Ant Esports MK1300 V2 vendor configuration interface."""

    def __init__(self, device=None, on_log: Optional[Callable[[str], None]] = None):
        self.device = device
        self.connected = device is not None
        self.on_log = on_log
        self.device_info: Dict[str, Any] = {}
        self._io_lock = threading.RLock()

    def log(self, msg: str) -> None:
        if self.on_log:
            self.on_log(msg)

    @classmethod
    def enumerate_all(cls) -> List[Dict[str, Any]]:
        """Enumerate HID devices using native libhidapi-hidraw.so or python-hidapi."""
        results = []

        # Try native libhidapi-hidraw first
        if _hidraw_lib:
            try:
                cur = _hidraw_lib.hid_enumerate(0, 0)
                p = cur
                while p:
                    d = p.contents
                    results.append({
                        "path": d.path,
                        "vendor_id": d.vendor_id,
                        "product_id": d.product_id,
                        "serial_number": d.serial_number or "",
                        "release_number": d.release_number,
                        "manufacturer_string": d.manufacturer_string or "",
                        "product_string": d.product_string or "",
                        "usage_page": d.usage_page,
                        "usage": d.usage,
                        "interface_number": d.interface_number,
                        "backend": "hidraw",
                    })
                    p = d.next
                if cur:
                    _hidraw_lib.hid_free_enumeration(cur)
                if results:
                    return results
            except Exception:
                pass

        # Fallback to python-hidapi
        if hid is not None:
            try:
                for dev in hid.enumerate():
                    d = dict(dev)
                    d["backend"] = "python-hid"
                    results.append(d)
                return results
            except Exception:
                pass

        return []

    @classmethod
    def find_device_info(cls) -> Optional[Dict[str, Any]]:
        """Enumerate HID devices and find the vendor config interface (0xFF00/0x02)."""
        devices = cls.enumerate_all()

        # Pass 1: Exact match on usagePage 0xFF00 and usage 0x02
        for dev in devices:
            vid = dev.get("vendor_id", 0)
            up = dev.get("usage_page", 0)
            u = dev.get("usage", 0)
            if vid in TARGET_VIDS and up == VENDOR_USAGE_PAGE and u == VENDOR_USAGE:
                return dev

        for dev in devices:
            up = dev.get("usage_page", 0)
            u = dev.get("usage", 0)
            if up == VENDOR_USAGE_PAGE and u == VENDOR_USAGE:
                return dev

        # Pass 2: Look at sysfs report descriptors for b'\x06\x00\xff\x09\x02'
        vendor_hidraws = set()
        for rdesc in glob.glob("/sys/class/hidraw/hidraw*/device/report_descriptor"):
            try:
                with open(rdesc, "rb") as f:
                    data = f.read()
                if b"\x06\x00\xff\x09\x02" in data:
                    h_name = rdesc.split("/")[4]
                    dev_link = os.path.realpath(os.path.join(rdesc, "../.."))
                    if any(f"{vid:04X}".lower() in dev_link.lower() for vid in TARGET_VIDS):
                        vendor_hidraws.add(h_name)
            except Exception:
                pass

        if vendor_hidraws:
            for dev in devices:
                if dev.get("vendor_id") in TARGET_VIDS:
                    path_str = dev.get("path", b"").decode("utf-8", errors="ignore")
                    for h_name in vendor_hidraws:
                        if h_name in path_str or f"/dev/{h_name}" in path_str:
                            return dev

        # Pass 3: Interface 2 is vendor config on MK1300 V2
        target_devs = [d for d in devices if d.get("vendor_id") in TARGET_VIDS]
        for dev in target_devs:
            if dev.get("interface_number") == 2:
                return dev

        # Pass 4: Fallback to non-keyboard interface
        for dev in target_devs:
            if dev.get("interface_number", 0) != 0:
                return dev

        return None

    def connect(self, dev_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Connect to the keyboard on the vendor config interface (0xFF00/0x02)."""
        self.log("Searching for MK1300 V2 vendor config interface (0xFF00/0x02)...")
        if dev_info is None:
            dev_info = self.find_device_info()

        if not dev_info:
            raise ConnectionError(
                "MK1300 V2 vendor config interface (0xFF00/0x02) not found.\n"
                "Ensure the keyboard is plugged in and udev rules are installed."
            )

        raw_path = dev_info.get("path")
        path = raw_path if isinstance(raw_path, bytes) else str(raw_path).encode("utf-8")
        self.log(f"Opening device path: {path.decode('utf-8', errors='ignore')} (VID: 0x{dev_info.get('vendor_id', 0):04X}, PID: 0x{dev_info.get('product_id', 0):04X})")

        device = None

        p_str = path.decode("utf-8", errors="ignore")

        # Strategy 1: Direct Linux /dev/hidraw character device (fastest, most reliable)
        if p_str.startswith("/dev/hidraw") and os.path.exists(p_str):
            try:
                device = LinuxHidrawDirectDevice(p_str)
                self.log(f"Opened via Linux direct hidraw I/O: {p_str}")
            except Exception as e:
                self.log(f"Direct hidraw open notice: {e}")

        # Strategy 2: Native libhidapi-hidraw.so
        if device is None and _hidraw_lib and dev_info.get("backend") == "hidraw":
            handle = _hidraw_lib.hid_open_path(path)
            if handle:
                device = HidrawNativeDevice(_hidraw_lib, handle, path)
                self.log(f"Opened via libhidapi-hidraw: {p_str}")

        # Strategy B: Use python-hid module
        if device is None and hid is not None:
            try:
                h_dev = hid.device()
                h_dev.open_path(path)
                h_dev.set_nonblocking(False)
                device = h_dev
            except Exception as e:
                p_str = path.decode("utf-8", errors="ignore")
                err_msg = (
                    f"Failed to open {p_str}: {e}.\n"
                    "Please install the udev rule to grant access without root:\n"
                    "  sudo cp udev/99-mk1300.rules /etc/udev/rules.d/\n"
                    "  sudo udevadm control --reload-rules && sudo udevadm trigger\n"
                )
                raise PermissionError(err_msg) from e

        if device is None:
            raise ConnectionError("No working HID backend could open the device.")

        self.device = device
        self.connected = True
        self.device_info = {
            "vendor_id": dev_info.get("vendor_id", 0),
            "product_id": dev_info.get("product_id", 0),
            "product_name": dev_info.get("product_string", "MK1300 V2 Gaming Keyboard"),
            "manufacturer": dev_info.get("manufacturer_string", ""),
            "path": path.decode("utf-8", errors="ignore"),
        }
        self.log("✓ Device opened successfully on vendor config interface!")
        return self.device_info

    def disconnect(self) -> None:
        """Close connection to the device."""
        with self._io_lock:
            if self.device:
                try:
                    self.device.close()
                except Exception:
                    pass
            self.device = None
            self.connected = False
            self.log("Disconnected")

    def _safety_check(self, cmd_byte: int, payload: List[int]) -> None:
        """Block any dangerous or disallowed commands."""
        if cmd_byte in BLOCKED_COMMANDS:
            raise ValueError(f"BLOCKED: cmd {cmd_byte} (0x{cmd_byte:02X}) - firmware/bootloader/flash")

        for blocked in BLOCKED_SUBCOMMANDS:
            if len(payload) >= len(blocked) and all(payload[i] == blocked[i] for i in range(len(blocked))):
                raise ValueError(f"BLOCKED: sub-command {blocked} - factory reset")

    def build_report(self, cmd_byte: int, payload: List[int]) -> bytearray:
        """Build the 64-byte HID report from command byte and payload."""
        self._safety_check(cmd_byte, payload)
        report = bytearray(64)
        report[0] = cmd_byte & 0xFF
        for i, b in enumerate(payload[:63]):
            report[i + 1] = b & 0xFF
        return report

    def send_command(self, cmd_byte: int, payload: Optional[List[int]] = None, read_response: bool = True) -> List[int]:
        """
        Send a 64-byte command report to the device.
        On Linux hidapi, prepend report-ID 0x00 (65 bytes total).
        Thread-safe with automatic reconnect retry on broken pipes.
        """
        if payload is None:
            payload = []

        report = self.build_report(cmd_byte, payload)

        with self._io_lock:
            if not self.device or not self.connected:
                raise ConnectionError("Device not connected")

            data_to_send = b"\x00" + bytes(report)

            try:
                if hasattr(self.device, "send_report"):
                    self.device.send_report(0, report)
                elif hasattr(self.device, "write"):
                    self.device.write(data_to_send)
                else:
                    raise TypeError("Unsupported device interface")

                if read_response:
                    if hasattr(self.device, "read"):
                        resp = self.device.read(64, timeout_ms=1000)
                        return list(resp) if resp else []
                    return []

                time.sleep(0.002)
                return []
            except (OSError, ConnectionError) as ex:
                self.log(f"HID write/read notice: {ex}. Attempting auto-reconnect...")
                try:
                    self.connect()
                    if hasattr(self.device, "write"):
                        self.device.write(data_to_send)
                    if read_response and hasattr(self.device, "read"):
                        resp = self.device.read(64, timeout_ms=1000)
                        return list(resp) if resp else []
                    time.sleep(0.002)
                    return []
                except Exception:
                    raise ex

    def send_device_data(self, payload: Optional[List[int]] = None) -> List[int]:
        """Send command 6 device data with response."""
        return self.send_command(6, payload if payload is not None else [], read_response=True)

    def get_keyboard_config(self) -> Dict[str, Any]:
        """Query keyboard hardware configuration."""
        self.log("Reading keyboard config...")
        resp = self.send_device_data([5])
        self.log(f"Config response: {resp[:20]}")
        if len(resp) < 19:
            raise RuntimeError(f"Config response too short: {len(resp)} bytes")

        d = resp[4:19]
        config = {
            "version": d[1] << 8 | d[0],
            "pid": d[3] << 8 | d[2],
            "firmware": d[5] << 8 | d[4],
            "battery": d[8],
            "profileCount": d[10],
            "profile": d[11],
            "layerCount": d[12],
            "layer": d[13],
        }
        self.log(f"Version: {config['version']}, Firmware: {config['firmware']}, Profile: {config['profile']}")
        return config

    def get_light_config(self) -> Dict[str, Any]:
        """Query light configuration."""
        resp = self.send_device_data([10])
        if len(resp) < 16:
            raise RuntimeError(f"Light config response too short: {len(resp)} bytes")
        d = resp[4:16]
        return {
            "type": d[0],
            "mode": d[2],
            "brightness": d[3],
            "speed": d[4],
            "direction": d[5],
            "color": d[6],
        }

    def get_key_mappings(self, layer: int = 0, count: int = 126) -> List[Tuple[int, int, int, int]]:
        """
        Read key function mappings for all keys on the specified layer (0=Base, 1=Fn).
        Replicates official app getKeyInfos protocol byte-for-byte.
        Reads all 126 matrix slots from hardware table by default.
        """
        keys: List[Tuple[int, int, int, int]] = []
        total_bytes = count * 4
        chunk_size = 56
        chunks = math.ceil(total_bytes / chunk_size)

        for c in range(chunks):
            offset = c * chunk_size
            payload = [0] * 63
            payload[0] = 8
            payload[1] = 58
            payload[2] = offset & 0xFF
            payload[3] = (offset >> 8) & 0xFF
            payload[5] = layer & 0xFF
            resp = self.send_command(6, payload, read_response=True)
            chunk_data = resp[8:8 + chunk_size]
            for i in range(0, len(chunk_data), 4):
                if len(keys) < count:
                    t = tuple(chunk_data[i:i + 4])
                    keys.append((t[0], t[1], t[2], t[3]))

        return keys

    def get_layout_key_mappings(self, layer: int = 0) -> List[Tuple[int, int, int, int]]:
        """
        Read the live mappings for all 61 physical keys defined in KEYBOARD_LAYOUT,
        indexed by each key's hardware matrix slot (k.index).
        """
        table = self.get_key_mappings(layer=layer, count=126)
        result: List[Tuple[int, int, int, int]] = []
        for k in KEYBOARD_LAYOUT:
            if k.index < len(table):
                result.append(table[k.index])
            else:
                result.append((0, 0, 0, 0))
        return result

    def set_key_mapping(
        self,
        matrix_index: int,
        key_type: int,
        code1: int,
        code2: int = 0,
        code3: int = 0,
        layer: int = 0,
    ) -> None:
        """
        Set mapping for a single key matrix slot on specified layer.
        Replicates official app setKeyInfo protocol with synchronous response reading.
        """
        payload = [0] * 63
        byte_offset = matrix_index * 4
        payload[0] = 16
        payload[1] = 7
        payload[2] = byte_offset & 0xFF
        payload[3] = (byte_offset >> 8) & 0xFF
        payload[5] = layer & 0xFF
        payload[7] = key_type & 0xFF
        payload[8] = code1 & 0xFF
        payload[9] = code2 & 0xFF
        payload[10] = code3 & 0xFF
        self.send_command(6, payload, read_response=True)
        self.log(f"Remapped hardware slot {matrix_index} on layer {layer}: type={key_type}, c1={code1}, c2={code2}")

    def set_all_key_mappings(
        self,
        mappings: List[Tuple[int, int, int, int]],
        layer: int = 0,
    ) -> None:
        """
        Set mappings for all keys in bulk on specified layer using 56-byte chunked writes.
        If mappings is length 61 (KEYBOARD_LAYOUT size), it merges them into the 126-entry
        matrix table at each key's k.index, then writes the full table to hardware.
        """
        if len(mappings) == len(KEYBOARD_LAYOUT):
            full_table = self.get_key_mappings(layer=layer, count=126)
            if len(full_table) < 126:
                full_table.extend([(0, 0, 0, 0)] * (126 - len(full_table)))
            for i, k in enumerate(KEYBOARD_LAYOUT):
                if k.index < len(full_table):
                    full_table[k.index] = mappings[i]
            target_mappings = full_table
        else:
            target_mappings = mappings

        total_keys = len(target_mappings)
        total_bytes = total_keys * 4
        raw = [0] * (total_bytes + 64)
        for i, (kt, c1, c2, c3) in enumerate(target_mappings):
            raw[4 * i + 0] = kt & 0xFF
            raw[4 * i + 1] = c1 & 0xFF
            raw[4 * i + 2] = c2 & 0xFF
            raw[4 * i + 3] = c3 & 0xFF

        chunk_size = 56
        chunks = math.ceil(total_bytes / chunk_size)
        sent = 0

        for c in range(chunks):
            offset = c * chunk_size
            remaining = total_bytes - sent
            this_chunk = min(chunk_size, remaining)
            is_last = (c == chunks - 1)

            payload = [0] * 63
            payload[0] = 9
            payload[1] = (remaining % chunk_size + 3) if (is_last and remaining % chunk_size > 0) else (chunk_size + 3)
            payload[2] = offset & 0xFF
            payload[3] = (offset >> 8) & 0xFF
            payload[5] = layer & 0xFF

            for j in range(this_chunk):
                payload[7 + j] = raw[sent + j]

            self.send_command(6, payload, read_response=True)
            sent += this_chunk
            time.sleep(0.010)

        self.log(f"Applied {total_keys} key mappings in bulk to layer {layer}")

    def switch_num_to_fn_layer(self, layer: int = 0, enable_f_keys: bool = True) -> None:
        """
        Switch the number row keys (1..=, HW 22..33) to F1..F12 (or back to numbers 1..=).
        Useful for instant testing of key remapping behavior.
        """
        # HW 22..33 correspond to keys 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, -, =
        if enable_f_keys:
            # F1..F12 keycodes: 58..69
            f_codes = [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]
            for i, fcode in enumerate(f_codes):
                self.set_key_mapping(matrix_index=22 + i, key_type=32, code1=0, code2=fcode, code3=0, layer=layer)
            self.log(f"Switched Layer {layer} number row (HW 22-33) to Function Keys F1-F12")
        else:
            # Standard numbers 1..0, -, =: 30..39, 45, 46
            num_codes = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 45, 46]
            for i, ncode in enumerate(num_codes):
                self.set_key_mapping(matrix_index=22 + i, key_type=32, code1=0, code2=ncode, code3=0, layer=layer)
            self.log(f"Restored Layer {layer} number row (HW 22-33) to standard numbers (1-0, -, =)")

    def set_current_profile(self, profile: int) -> None:
        """Switch hardware active profile (0-2)."""
        self.send_command(6, [251, profile & 0xFF], read_response=True)
        self.log(f"Switched profile to {profile}")

    def set_auto_sleep_time(self, seconds: int) -> None:
        """Set keyboard sleep timeout in seconds."""
        payload = [252, 2, 0, 0, seconds & 0xFF, (seconds >> 8) & 0xFF]
        self.send_command(6, payload, read_response=True)
        self.log(f"Set auto sleep time to {seconds}s")
    def set_hardware_animation(
        self,
        mode: int,
        brightness: int = 4,
        speed: int = 2,
        color_mode: int = 0,
        direction: int = 0,
        hsv: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        Set hardware animation mode, brightness, speed, direction and color.
        Replicates 2-step flow: global config (Type 0) + mode template (Type 1).
        """
        self.log(f"Setting hardware animation: mode={mode}, brightness={brightness}, speed={speed}, colorMode={color_mode}")

        brightness_to_v = [30, 80, 140, 200, 236]
        v_value = brightness_to_v[brightness] if 0 <= brightness < len(brightness_to_v) else 236

        def apply_color(config: List[int]) -> None:
            config[2] = mode
            config[3] = brightness
            config[4] = speed
            if color_mode == 1 and hsv:
                config[5] = 1
                config[6] = 1
                config[7] = 0
                config[8] = hsv["h"]
                config[9] = hsv["s"]
                config[10] = v_value
            else:
                config[5] = direction
                config[6] = 0
                config[7] = 8
                config[8] = 255
                config[9] = 255
                config[10] = v_value

        # Step 1: Query and update the GLOBAL config (Type 0)
        global_resp = self.send_device_data([10])
        self.log(f"Global query response: {global_resp[:20]}")
        if global_resp and len(global_resp) >= 16:
            config = list(global_resp[5:16])
            config[0] = 0  # Type 0 = Global / Active
            apply_color(config)
            self.log(f"Applying Global Config: {config}")
            self.send_device_data([11, len(config), 0, 0] + config)

        # Step 2: Query and update the Mode Template (Type 1)
        tpl_resp = self.send_device_data([22, 0, 0, 0, 1, 0, mode])
        if tpl_resp and len(tpl_resp) >= 16:
            tpl_config = list(tpl_resp[5:16])
            tpl_config[0] = 1  # Type 1 = Mode Template
            apply_color(tpl_config)
            self.log(f"Applying Template Config: {tpl_config}")
            self.send_device_data([11, len(tpl_config), 0, 0] + tpl_config)

        time.sleep(0.050)
        self.log("Hardware animation set!")

    def set_key_color(self, key_index: int, r: int, g: int, b: int) -> None:
        """Set the RGB color of a single key by key index."""
        offset = 3 * key_index
        packet = [0] * 63
        packet[0] = 20
        packet[1] = 3
        packet[2] = offset & 0xFF
        packet[3] = (offset >> 8) & 0xFF
        packet[7] = r & 0xFF
        packet[8] = g & 0xFF
        packet[9] = b & 0xFF
        self.send_command(6, packet, read_response=False)

    def set_all_key_colors(self, color_array: List[int], key_count: int = KEY_COUNT) -> None:
        """
        Send all key colors using chunked 56-byte packets.
        Replicates hid-driver.js setAllKeyColors byte-for-byte.
        """
        total_bytes = key_count * 3
        chunk_size = 56
        chunks = math.ceil(total_bytes / chunk_size)

        for i in range(chunks):
            offset = chunk_size * i
            remaining = total_bytes - offset
            this_chunk = min(chunk_size, remaining)
            is_last = (i == chunks - 1)

            packet = [0] * 63
            packet[0] = 18
            packet[1] = ((remaining % chunk_size) + 3) if (is_last and remaining % chunk_size > 0) else (chunk_size + 3)
            packet[2] = offset & 0xFF
            packet[3] = (offset >> 8) & 0xFF

            for j in range(this_chunk):
                idx = offset + j
                packet[7 + j] = color_array[idx] if idx < len(color_array) else 0

            # Read response for reliability instead of fire-and-forget
            self.send_command(6, packet, read_response=True)

    def test_single_key(self) -> None:
        """Smoke test keys matching reference: Esc red, Q green, W blue."""
        self.log("Testing: Setting key 0 (Esc) to RED...")
        self.set_key_color(0, 255, 0, 0)
        time.sleep(0.100)
        self.log("Testing: Setting key 43 (Q) to GREEN...")
        self.set_key_color(43, 0, 255, 0)
        time.sleep(0.100)
        self.log("Testing: Setting key 44 (W) to BLUE...")
        self.set_key_color(44, 0, 0, 255)
        self.log("Test complete - check Esc=Red, Q=Green, W=Blue on your keyboard")
