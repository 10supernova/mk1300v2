#!/usr/bin/env python3
"""
Comprehensive test runner for mk1300-linux.
Runs:
1. Safety Tests
2. 1:1 Static Pattern Verification Tests (90 primary + 50 extra)
3. 1:1 Protocol Byte Packet Verification Tests
"""

import sys
from tests.test_safety import test_blocked_command_85, test_blocked_factory_reset_subcommand, test_build_report_safety
from tests.test_patterns_1to1 import test_all_90_patterns_match_reference, test_extra_50_patterns_match_reference
from tests.test_protocol_1to1 import test_protocol_packets_match_reference, test_safety_blocks


def main():
    print("=" * 70)
    print("RUNNING ALL MK1300-LINUX VERIFICATION TEST SUITES")
    print("=" * 70)

    # 1. Safety Tests
    print("\n[Suite 1/3] Safety & Command Blocking Tests...")
    test_blocked_command_85()
    test_blocked_factory_reset_subcommand()
    test_build_report_safety()
    test_safety_blocks()
    print("  ✓ Safety tests passed! (Cmd 85 and Sub-cmd [15, 255] strictly hard-blocked)")

    # 2. 1:1 Pattern Verification
    print("\n[Suite 2/3] 1:1 Pattern Match Verification...")
    test_all_90_patterns_match_reference()
    test_extra_50_patterns_match_reference()
    print("  ✓ 1:1 Pattern calculations passed! (All 140 patterns / 8,540 key RGBs match JS)")

    # 3. 1:1 Protocol Verification
    print("\n[Suite 3/3] 1:1 Protocol Byte Packet Verification...")
    test_protocol_packets_match_reference()
    print("  ✓ 1:1 Protocol packet tests passed! (Every command, chunk, offset matches JS)")

    print("\n" + "=" * 70)
    print("ALL TEST SUITES PASSED (100% 1:1 COMPLIANCE WITH UPSTREAM REFERENCE)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
