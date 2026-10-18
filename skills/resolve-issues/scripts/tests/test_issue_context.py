"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

issue_context.py decides what the agent sees before it touches code. A flag that stops
firing lets it start on an issue someone else's open pull request already closes, or on
one whose blocker is still open; a wrong work order makes a sub-issue land before the one
it depends on. Each test pins one of those.
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

import issue_context  # noqa: E402


def issue(number, state="OPEN", **fields):
    return {"number": number, "title": f"Issue {number}", "state": state, "stateReason": None,
            "url": f"https://github.com/o/r/issues/{number}", "body": f"Body of {number}.",
            "labels": [], "milestone": None, "issueType": None, "parent": None,
            "subIssues": {"nodes": []}, "blockedBy": {"nodes": []},
            "closedByPullRequestsReferences": [], "comments": [], **fields}


def ref(number, state="OPEN"):
    return {"number": number, "title": f"Issue {number}", "state": state}


def pr_ref(number):
    return {"number": number, "repository": {"name": "r", "owner": {"login": "o"}}}


class IssueContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.fixture = self.tmp / "fixture.json"
        self.gh = self.tmp / "gh"
        self.gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_gh.py"}" "$@"\n')
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        os.environ["FAKE_GH_FIXTURE"] = str(self.fixture)

    def run_with(self, issues, *refs, prs=None, repo="o/r"):
        data = {"issues": {f"{repo}#{i['number']}": i for i in issues},
                "prs": {f"{repo}#{p['number']}": p for p in prs or []}}
        self.fixture.write_text(json.dumps(data))
        out, err = io.StringIO(), io.StringIO()
        args = ["issue_context", *refs, "--gh", str(self.gh)] + (["-R", repo] if repo else [])
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = issue_context.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_sub_issues_are_ordered_after_their_sibling_blockers(self):
        epic = issue(1, subIssues={"nodes": [ref(4), ref(2), ref(3), ref(5, "CLOSED")]})
        children = [issue(4, blockedBy={"nodes": [ref(2), ref(3)]}),
                    issue(2), issue(3, blockedBy={"nodes": [ref(2)]})]
        code, out, _ = self.run_with([epic, *children], "1")
        self.assertEqual(code, 0)
        self.assertIn("1. #2 Issue 2 (OPEN)\n2. #3 Issue 3 (OPEN) — after #2\n"
                      "3. #4 Issue 4 (OPEN) — after #2, #3", out)
        self.assertIn("#5 Issue 5 (CLOSED) — done", out)

    def test_a_closed_sibling_no_longer_holds_the_order(self):
        epic = issue(1, subIssues={"nodes": [ref(3), ref(2, "CLOSED")]})
        code, out, _ = self.run_with([epic, issue(3, blockedBy={"nodes": [ref(2, "CLOSED")]})],
                                     "1")
        self.assertIn("1. #3 Issue 3 (OPEN)\n", out)

    def test_cycle_and_outside_blocker_are_flagged(self):
        epic = issue(1, subIssues={"nodes": [ref(2), ref(3)]})
        children = [issue(2, blockedBy={"nodes": [ref(3), ref(9)]}),
                    issue(3, blockedBy={"nodes": [ref(2)]})]
        _, out, _ = self.run_with([epic, *children], "1")
        self.assertIn("blocked-by cycle among sub-issues #2, #3", out)
        self.assertIn("sub-issue #2 waits for open #9, outside this tree", out)

    def test_open_blocker_stops_the_work_and_closed_one_does_not(self):
        _, out, _ = self.run_with([issue(1, blockedBy={"nodes": [ref(7), ref(8, "CLOSED")]})], "1")
        self.assertIn("open blocker #7", out)
        self.assertNotIn("open blocker #8", out)

    def test_open_closing_pull_request_is_flagged_and_merged_one_is_not(self):
        prs = [{"number": 40, "state": "OPEN", "isDraft": True, "headRefName": "feat/1",
                "url": "u40"},
               {"number": 41, "state": "MERGED", "isDraft": False, "headRefName": "fix/1",
                "url": "u41"}]
        _, out, _ = self.run_with([issue(1, closedByPullRequestsReferences=[pr_ref(40),
                                                                            pr_ref(41)])],
                                  "1", prs=prs)
        self.assertIn("#40 OPEN draft (`feat/1`)", out)
        self.assertIn("pull request #40 already closes this issue and is open", out)
        self.assertNotIn("pull request #41 already", out)

    def test_closed_issue_is_flagged(self):
        _, out, _ = self.run_with([issue(1, "CLOSED", stateReason="COMPLETED")], "#1")
        self.assertIn("**State:** CLOSED (COMPLETED)", out)
        self.assertIn("the issue is closed", out)

    def test_clean_issue_has_no_flags(self):
        _, out, _ = self.run_with([issue(1)], "1")
        self.assertIn("## Flags\n\n- none", out)

    def test_issue_url_names_its_repository_over_the_flag(self):
        self.fixture.write_text(json.dumps({"issues": {"o/r#3": issue(3)}}))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = issue_context.main(["issue_context", "https://github.com/o/r/issues/3",
                                       "-R", "x/y", "--gh", str(self.gh)])
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("# #3 Issue 3", out.getvalue())

    def test_relations_between_the_given_issues(self):
        issues = [issue(1, parent=ref(9)), issue(2, parent=ref(9)),
                  issue(3, parent=ref(1), blockedBy={"nodes": [ref(2)]})]
        _, out, _ = self.run_with(issues, "1", "2", "3")
        self.assertIn("- #3 is a sub-issue of #1", out)
        self.assertIn("- #3 is blocked by #2", out)
        self.assertIn("- #1, #2 share the parent #9", out)

    def test_unreadable_issue_fails(self):
        code, _, err = self.run_with([issue(1)], "1", "2")
        self.assertEqual(code, 1)
        self.assertIn("Could not resolve", err)
        self.assertEqual(self.run_with([], "abc")[0], 1)


if __name__ == "__main__":
    unittest.main()
