"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

The skill's cost advice rests on two billing rules: every job is rounded up to a whole
minute, and a minute costs a different amount on each runner. If either stops being
applied here, a before/after table reports savings that the invoice will not show.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import billable_minutes  # noqa: E402

RUN = {
    "id": 1,
    "event": "pull_request",
    "conclusion": "success",
    "created_at": "2026-09-23T10:00:00Z",
    "run_started_at": "2026-09-23T10:00:00Z",
    "updated_at": "2026-09-23T10:01:11Z",
}


def job(name, label, seconds, conclusion="success", steps=None):
    return {
        "name": name,
        "labels": [label],
        "conclusion": conclusion,
        "started_at": "2026-09-23T10:00:00Z",
        "completed_at": f"2026-09-23T10:{seconds // 60:02d}:{seconds % 60:02d}Z",
        "steps": steps or [],
    }


class RunnerKind(unittest.TestCase):
    def test_standard_labels_map_to_their_price_class(self):
        cases = {
            "ubuntu-slim": "linux-slim",
            "ubuntu-24.04": "linux",
            "ubuntu-latest": "linux",
            "ubuntu-24.04-arm": "linux-arm",
            "windows-2025": "windows",
            "windows-11-arm": "windows",
            "macos-15": "macos",
        }
        for label, kind in cases.items():
            self.assertEqual(billable_minutes.runner_kind([label]), kind, label)

    def test_larger_and_self_hosted_runners_have_no_known_rate(self):
        self.assertIsNone(billable_minutes.runner_kind(["ubuntu-24.04-16core"]))
        self.assertIsNone(billable_minutes.runner_kind(["self-hosted", "linux"]))


class Summarize(unittest.TestCase):
    def test_every_job_rounds_up_to_a_whole_minute(self):
        jobs = [job("lint", "ubuntu-24.04", 9), job("test", "ubuntu-24.04", 61)]
        summary = billable_minutes.summarize(RUN, jobs)
        self.assertEqual(summary["minutes"], 1 + 2)
        self.assertEqual(summary["job_seconds"], 70)
        self.assertEqual(summary["wall_clock"], 71)

    def test_linux_equivalent_weighs_each_runner_by_its_price(self):
        jobs = [
            job("gate", "ubuntu-slim", 30),
            job("arm", "ubuntu-24.04-arm", 30),
            job("win", "windows-2025", 30),
            job("mac", "macos-15", 30),
        ]
        summary = billable_minutes.summarize(RUN, jobs)
        self.assertEqual(summary["minutes"], 4)
        self.assertAlmostEqual(summary["linux_equivalent"], (0.002 + 0.005 + 0.010 + 0.062) / 0.006)

    def test_skipped_jobs_are_not_billed(self):
        jobs = [job("api", "ubuntu-24.04", 30), job("web", "ubuntu-24.04", 0, conclusion="skipped")]
        summary = billable_minutes.summarize(RUN, jobs)
        self.assertEqual((summary["minutes"], summary["skipped"]), (1, 1))

    def test_unknown_rate_counts_minutes_but_is_reported_apart(self):
        summary = billable_minutes.summarize(RUN, [job("build", "ubuntu-24.04-16core", 90)])
        self.assertEqual(summary["minutes"], 2)
        self.assertEqual(summary["linux_equivalent"], 0)
        self.assertEqual(summary["unknown_rate_jobs"], 1)

    def test_dominant_step_is_the_longest_one(self):
        steps = [
            {"name": "checkout", "started_at": "2026-09-23T10:00:00Z", "completed_at": "2026-09-23T10:00:02Z"},
            {"name": "test", "started_at": "2026-09-23T10:00:02Z", "completed_at": "2026-09-23T10:00:40Z"},
            {"name": "never ran", "started_at": None, "completed_at": None},
        ]
        summary = billable_minutes.summarize(RUN, [job("ci", "ubuntu-24.04", 45, steps=steps)])
        self.assertEqual(summary["jobs"][0]["dominant"], ("test", 38))


if __name__ == "__main__":
    unittest.main()
