"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

The fixtures pair every deprecated pattern with its modern replacement. A rule
that stops firing on old code, or starts firing on the replacement, defeats the
scanner's purpose: the first hides a real breakage, the second trains users to
ignore it.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import scan_deprecated  # noqa: E402

FIXTURES = HERE / "fixtures"


def findings(subdir):
    return [f for p in scan_deprecated.iter_files([FIXTURES / subdir]) for f in scan_deprecated.scan_file(p)]


class ScanDeprecatedTest(unittest.TestCase):
    def test_every_rule_fires_on_deprecated_code(self):
        fired = {r.id for _, _, r in findings("deprecated")}
        missing = {r.id for r in scan_deprecated.RULES} - fired
        self.assertEqual(missing, set(), f"rules with no deprecated fixture hit: {sorted(missing)}")

    def test_modern_replacements_produce_no_findings(self):
        hits = [f"{p.name}:{n} [{r.id}]" for p, n, r in findings("modern")]
        self.assertEqual(hits, [])

    def test_r3f_rules_ignore_user_components_with_same_name(self):
        hits = {r.id for p, _, r in findings("modern") if p.suffix == ".tsx"}
        self.assertNotIn("r3f-xr-removed", hits)

    def test_finding_points_at_the_offending_line(self):
        by_rule = {r.id: (p.name, n) for p, n, r in findings("deprecated")}
        self.assertEqual(by_rule["three-webgl1"], ("three-legacy.js", 11))

    def test_two_controller_slots_not_flagged_when_loop_creates_more(self):
        hits = {r.id for _, _, r in findings("modern")}
        self.assertNotIn("xr-two-controller-slots", hits)


if __name__ == "__main__":
    unittest.main()
