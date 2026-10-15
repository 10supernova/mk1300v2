"""
Safety test suite: Verify that forbidden opcodes and dangerous commands are hard-blocked.
"""

import pytest
from mk1300.driver import HIDDriver, BLOCKED_COMMANDS, BLOCKED_SUBCOMMANDS


class DummyDevice:
    def __init__(self):
        self.sent = []

    def send_report(self, report_id, data):
        self.sent.append(list(data))

    def write(self, data):
        self.sent.append(list(data))

    def read(self, length, timeout_ms=1000):
        return [0] * length


def test_blocked_command_85():
    dev = DummyDevice()
    driver = HIDDriver(device=dev)

    with pytest.raises(ValueError, match="BLOCKED: cmd 85"):
        driver.send_command(85, [0, 1, 2])

    assert len(dev.sent) == 0, "Blocked command 85 must never reach device"


def test_blocked_factory_reset_subcommand():
    dev = DummyDevice()
    driver = HIDDriver(device=dev)

    with pytest.raises(ValueError, match="BLOCKED: sub-command"):
        driver.send_command(6, [15, 255, 0])

    assert len(dev.sent) == 0, "Factory reset sub-command [15, 255] must never reach device"


def test_build_report_safety():
    driver = HIDDriver()

    # Direct report building check
    with pytest.raises(ValueError):
        driver.build_report(85, [])

    with pytest.raises(ValueError):
        driver.build_report(6, [15, 255])


if __name__ == "__main__":
    test_blocked_command_85()
    test_blocked_factory_reset_subcommand()
    test_build_report_safety()
    print("All safety tests passed!")
