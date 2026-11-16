"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

A pin whose SHA is not the commit of its tag must never be reported as usable, and a
release younger than the cooldown must never be offered as an update: that window is
what keeps a freshly published malicious release out of the workflows.
"""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import check_pins  # noqa: E402

NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
OTHER_SHA = "0" * 40
PIN = check_pins.Pin("actions/checkout", "v7.0.1", SHA)


def classify(tag_sha=SHA, latest="v7.0.1", age_days=30, cooldown=7):
    return check_pins.classify(PIN, tag_sha, latest, NOW - timedelta(days=age_days), NOW, cooldown)


class ParseTable(unittest.TestCase):
    def test_reads_action_version_and_sha_and_ignores_other_rows(self):
        text = "\n".join(
            [
                "| Action | Version | SHA | Notes |",
                "|---|---|---|---|",
                f"| `actions/checkout` | v7.0.1 | `{SHA}` | refuses fork-PR checkout |",
                f"| `actions/cache` (also `/restore`, `/save`) | v6.1.0 | `{OTHER_SHA}` | |",
                "| `ubuntu-slim` | 1 / 5 GB | same | not a pin |",
            ]
        )
        self.assertEqual(
            check_pins.parse_table(text),
            [PIN, check_pins.Pin("actions/cache", "v6.1.0", OTHER_SHA)],
        )

    def test_the_shipped_table_has_only_full_length_shas(self):
        table = HERE.parent.parent / "references" / "versions.md"
        pins = check_pins.parse_table(table.read_text(encoding="utf-8"))
        self.assertGreater(len(pins), 20)
        self.assertEqual(len({pin.repo for pin in pins}), len(pins))


class Classify(unittest.TestCase):
    def test_sha_that_is_not_the_tag_commit_is_a_mismatch_even_when_up_to_date(self):
        self.assertEqual(classify(tag_sha=OTHER_SHA), "MISMATCH")

    def test_latest_release_already_pinned_is_ok(self):
        self.assertEqual(classify(), "OK")

    def test_newer_release_inside_the_cooldown_is_not_offered(self):
        self.assertEqual(classify(latest="v7.1.0", age_days=6), "COOLDOWN")

    def test_newer_release_past_the_cooldown_is_an_update(self):
        self.assertEqual(classify(latest="v7.1.0", age_days=7), "UPDATE")


if __name__ == "__main__":
    unittest.main()
