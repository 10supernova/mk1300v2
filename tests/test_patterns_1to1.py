"""
1:1 Verification test for all 90 static patterns:
Asserts every single key's RGB value computed in Python matches the original JavaScript effects.js.
"""

import json
from mk1300.effects import PATTERNS, RGBColor
from mk1300.layout import KEYBOARD_LAYOUT


def test_all_90_patterns_match_reference():
    with open("tests/reference_patterns_90.json", "r") as f:
        ref_patterns = json.load(f)

    assert len(PATTERNS) == len(ref_patterns) == 90, f"Expected 90 patterns, got {len(PATTERNS)} vs {len(ref_patterns)}"

    mismatches = []
    total_keys_tested = 0

    for py_pat, js_pat in zip(PATTERNS, ref_patterns):
        assert py_pat.id == js_pat["id"], f"ID mismatch: {py_pat.id} vs {js_pat['id']}"
        assert py_pat.name == js_pat["name"], f"Name mismatch: {py_pat.name} vs {js_pat['name']}"

        py_colors: list[RGBColor] = py_pat.fn(KEYBOARD_LAYOUT)
        js_colors: list[dict] = js_pat["colors"]

        assert len(py_colors) == len(js_colors) == len(KEYBOARD_LAYOUT), (
            f"Color count mismatch in {py_pat.id}: {len(py_colors)} vs {len(js_colors)}"
        )

        for key_idx, (py_c, js_c) in enumerate(zip(py_colors, js_colors)):
            total_keys_tested += 1
            key = KEYBOARD_LAYOUT[key_idx]
            if (py_c.r, py_c.g, py_c.b) != (js_c["r"], js_c["g"], js_c["b"]):
                mismatches.append({
                    "pattern": py_pat.id,
                    "key_idx": key_idx,
                    "key_name": key.name,
                    "key_hw_index": key.index,
                    "py": (py_c.r, py_c.g, py_c.b),
                    "js": (js_c["r"], js_c["g"], js_c["b"]),
                })

    if mismatches:
        print(f"FAILED: Found {len(mismatches)} mismatches across {total_keys_tested} keys:")
        for m in mismatches[:20]:
            print(f"  Pattern {m['pattern']} key {m['key_name']} (hw={m['key_hw_index']}): PY={m['py']} != JS={m['js']}")
        assert False, f"{len(mismatches)} RGB mismatches found!"

    print(f"SUCCESS: All 90 patterns ({total_keys_tested} key RGB calculations) match reference 1:1!")


def test_extra_50_patterns_match_reference():
    from mk1300.extra_effects import EXTRA_PATTERNS
    with open("tests/reference_extra_patterns_50.json", "r") as f:
        ref_patterns = json.load(f)

    assert len(EXTRA_PATTERNS) == len(ref_patterns) == 50, f"Expected 50 extra patterns, got {len(EXTRA_PATTERNS)} vs {len(ref_patterns)}"

    mismatches = []
    total_keys_tested = 0

    for py_pat, js_pat in zip(EXTRA_PATTERNS, ref_patterns):
        assert py_pat.id == js_pat["id"], f"ID mismatch: {py_pat.id} vs {js_pat['id']}"

        py_colors = py_pat.fn(KEYBOARD_LAYOUT)
        js_colors = js_pat["colors"]

        for key_idx, (py_c, js_c) in enumerate(zip(py_colors, js_colors)):
            total_keys_tested += 1
            key = KEYBOARD_LAYOUT[key_idx]
            if (py_c.r, py_c.g, py_c.b) != (js_c["r"], js_c["g"], js_c["b"]):
                mismatches.append({
                    "pattern": py_pat.id,
                    "key_idx": key_idx,
                    "key_name": key.name,
                    "py": (py_c.r, py_c.g, py_c.b),
                    "js": (js_c["r"], js_c["g"], js_c["b"]),
                })

    if mismatches:
        print(f"FAILED: Found {len(mismatches)} mismatches across {total_keys_tested} extra keys:")
        for m in mismatches[:10]:
            print(f"  Extra pattern {m['pattern']} key {m['key_name']}: PY={m['py']} != JS={m['js']}")
        assert False, f"{len(mismatches)} extra RGB mismatches found!"

    print(f"SUCCESS: All 50 extra patterns ({total_keys_tested} key RGB calculations) match reference 1:1!")


if __name__ == "__main__":
    test_all_90_patterns_match_reference()
    test_extra_50_patterns_match_reference()
