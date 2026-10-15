"""
Protocol verification test: assert Python HIDDriver builds 100% identical packets
to the reference JavaScript driver.
"""

import json
import pytest
from typing import List, Dict, Any
from mk1300.driver import HIDDriver
from mk1300.layout import KEY_COUNT


class MockDevice:
    """Mock device that captures 64-byte reports and provides mock responses."""

    def __init__(self, responses=None):
        self.reports = []
        self.responses = responses or []
        self._read_idx = 0

    def send_report(self, report_id: int, data: bytearray):
        self.reports.append({"reportId": report_id, "data": list(data)})

    def read(self, length: int, timeout_ms: int = 1000):
        if self._read_idx < len(self.responses):
            resp = self.responses[self._read_idx]
            self._read_idx += 1
            return resp
        return [0] * length


def test_protocol_packets_match_reference():
    with open("tests/reference_protocol_packets.json", "r") as f:
        ref = json.load(f)

    # Test 1: Single key writes
    mock_dev = MockDevice()
    driver = HIDDriver(device=mock_dev)
    driver.set_key_color(0, 255, 0, 0)
    driver.set_key_color(21, 128, 64, 32)
    driver.set_key_color(43, 0, 255, 0)
    driver.set_key_color(118, 10, 20, 30)

    assert mock_dev.reports == ref["singleKeyPackets"], "Single key packets mismatch!"

    # Test 2: Bulk all-key write
    mock_dev = MockDevice()
    driver = HIDDriver(device=mock_dev)
    test_colors = [(i * 7) % 256 for i in range(KEY_COUNT * 3)]
    driver.set_all_key_colors(test_colors, KEY_COUNT)

    assert len(mock_dev.reports) == len(ref["bulkKeyPackets"]), "Bulk chunk count mismatch!"
    for i, (py_pkt, js_pkt) in enumerate(zip(mock_dev.reports, ref["bulkKeyPackets"])):
        assert py_pkt["data"] == js_pkt["data"], f"Bulk packet chunk {i} mismatch!"

    # Test 3: Hardware animation (multi / rainbow)
    mock_global = [0] * 64
    mock_global[5] = 0
    mock_global[6] = 5
    for i in range(7, 16):
        mock_global[i] = i

    mock_tpl = [0] * 64
    mock_tpl[5] = 1
    mock_tpl[6] = 5
    for i in range(7, 16):
        mock_tpl[i] = i

    mock_dev = MockDevice(responses=[mock_global, [0] * 64, mock_tpl, [0] * 64])
    driver = HIDDriver(device=mock_dev)
    driver.set_hardware_animation(3, 4, 2, 0, 0, None)

    assert len(mock_dev.reports) == len(ref["hwAnimMultiPackets"]), "HW multi animation packet count mismatch!"
    for i, (py_pkt, js_pkt) in enumerate(zip(mock_dev.reports, ref["hwAnimMultiPackets"])):
        assert py_pkt["data"] == js_pkt["data"], f"HW multi packet {i} mismatch!"

    # Test 4: Hardware animation (custom single color HSV)
    mock_dev = MockDevice(responses=[mock_global, [0] * 64, mock_tpl, [0] * 64])
    driver = HIDDriver(device=mock_dev)
    driver.set_hardware_animation(6, 2, 3, 1, 0, {"h": 180, "s": 220, "v": 200})

    assert len(mock_dev.reports) == len(ref["hwAnimCustomPackets"]), "HW custom animation packet count mismatch!"
    for i, (py_pkt, js_pkt) in enumerate(zip(mock_dev.reports, ref["hwAnimCustomPackets"])):
        assert py_pkt["data"] == js_pkt["data"], f"HW custom packet {i} mismatch!"

    print("ALL PROTOCOL PACKETS MATCH REFERENCE 1:1!")


def test_safety_blocks():
    mock_dev = MockDevice()
    driver = HIDDriver(device=mock_dev)

    # Command 85 blocked
    try:
        driver.send_command(85, [0, 1, 2])
        assert False, "Should have raised ValueError on command 85"
    except ValueError as e:
        assert "BLOCKED: cmd 85" in str(e)

    # Sub-command [15, 255] blocked
    try:
        driver.send_command(6, [15, 255, 0])
        assert False, "Should have raised ValueError on factory reset sub-command"
    except ValueError as e:
        assert "BLOCKED: sub-command" in str(e)


if __name__ == "__main__":
    test_protocol_packets_match_reference()
    test_safety_blocks()
    print("Self-test passed!")
