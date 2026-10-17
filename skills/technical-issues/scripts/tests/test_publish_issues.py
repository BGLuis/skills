"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

Publishing is the one step that cannot be undone, so these tests run publish_issues.py
against fake_gh.py and pin what protects the user: a rerun after a failure creates no
duplicate, the visibility seen live wins over the manifest, every key becomes `#N`
outside code, blockers become native links once, and the read-back catches what GitHub
did not apply.
"""

import contextlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import publish_issues  # noqa: E402

EXAMPLE = HERE.parent.parent / "examples" / "audit-to-issues"


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.drafts = self.tmp / "drafts"
        shutil.copytree(EXAMPLE, self.drafts)
        self.state_path = self.tmp / "state.json"
        self.set_state(visibility="private")
        self.gh = self.tmp / "gh"
        self.gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_gh.py"}" "$@"\n')
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        os.environ["FAKE_GH_STATE"] = str(self.state_path)

    def set_state(self, **values):
        state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
        state.update(values)
        self.state_path.write_text(json.dumps(state))

    def state(self):
        return json.loads(self.state_path.read_text())

    def manifest(self):
        return json.loads((self.drafts / "manifest.json").read_text())

    def numbers(self):
        return {i["key"]: i.get("number") for i in self.manifest()["issues"]}

    def publish(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = publish_issues.main(["publish", str(self.drafts), "--gh", str(self.gh), *extra])
        return code, out.getvalue() + err.getvalue()

    def creates(self):
        return [c for c in self.state()["log"] if c[:2] == ["issue", "create"]]

    def test_creates_in_order_with_parents_and_saves_numbers(self):
        code, output = self.publish()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.numbers(), {"epic": 100, "P-02": 101, "P-01": 102})
        issues = self.state()["issues"]
        self.assertIsNone(issues["100"]["parent"])
        self.assertEqual(issues["101"]["parent"], 100)
        self.assertEqual(issues["102"]["labels"], ["performance"])

    def test_keys_become_issue_numbers_in_every_body(self):
        self.publish()
        issues = self.state()["issues"]
        self.assertIn("| 1 | #101 |", issues["100"]["body"])
        self.assertIn("| 2 | #102 |", issues["100"]["body"])
        self.assertIn("**Depends on:** #101", issues["102"]["body"])
        self.assertNotIn("P-02", issues["102"]["body"].split("```ts")[0])

    def test_blockers_become_native_links_once(self):
        self.publish()
        self.assertEqual(self.state()["blocked_by"], {"102": [101]})
        code, output = self.publish()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.state()["blocked_by"], {"102": [101]})

    def test_rerun_after_a_failure_creates_only_the_missing_issues(self):
        self.set_state(fail_on_create=2)
        code, output = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("created so far: epic #100", output)
        self.assertEqual(self.numbers(), {"epic": 100, "P-02": None, "P-01": None})
        self.set_state(fail_on_create=None)
        code, output = self.publish()
        self.assertEqual(code, 0, output)
        titles = [c[c.index("--title") + 1] for c in self.creates()]
        self.assertEqual(len(titles), 4)  # 3 issues + the one failed attempt
        self.assertEqual(titles.count(titles[0]), 1, "the epic was created twice")
        self.assertEqual(self.numbers(), {"epic": 100, "P-02": 101, "P-01": 102})

    def test_live_visibility_overrides_the_manifest(self):
        self.set_state(visibility="public")
        code, output = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("redo the security triage", output)
        self.assertEqual(self.creates(), [])

    def test_old_gh_is_refused_before_creating(self):
        self.set_state(version="2.60.0")
        code, output = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("gh ≥ 2.94.0", output)
        self.assertEqual(self.creates(), [])

    def test_dry_run_calls_nothing_and_changes_nothing(self):
        before = (self.drafts / "manifest.json").read_text()
        code, output = self.publish("--dry-run")
        self.assertEqual(code, 0, output)
        self.assertNotIn("log", self.state())
        self.assertEqual((self.drafts / "manifest.json").read_text(), before)
        self.assertIn("--parent '<epic>'", output)

    def test_read_back_reports_what_github_did_not_apply(self):
        self.set_state(drop_label="performance")
        code, output = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("missing labels ['performance']", output)

    def test_invalid_drafts_publish_nothing(self):
        (self.drafts / "p-02.md").write_text("no evidence here\n")
        code, output = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("nothing was published", output)
        self.assertNotIn("log", self.state())


class ResolveKeysTest(unittest.TestCase):
    def test_code_and_longer_keys_are_left_alone(self):
        text = ("Depends on T1 and P-01+P-02.\n`T1` stays\n```\nT1\n```\nT10 stays\n")
        out = publish_issues.resolve_keys(text, {"T1": 5, "P-01+P-02": 7, "P-01": 6})
        self.assertEqual(out, "Depends on #5 and #7.\n`T1` stays\n```\nT1\n```\nT10 stays\n")

    def test_epic_keys_are_not_replaced(self):
        issues = [{"key": "epic", "kind": "epic", "number": 1},
                  {"key": "T1", "kind": "task", "number": 2}]
        self.assertEqual(publish_issues.key_numbers(issues), {"T1": 2})


if __name__ == "__main__":
    unittest.main()
