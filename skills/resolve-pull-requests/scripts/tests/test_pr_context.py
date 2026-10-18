"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

pr_context.py is the list of what a pull request is waiting on. A comment it drops is a
reviewer ignored; a resolved thread it shows as open is work redone; a fork it does not
flag is a push that fails after the fixes are done. Each test pins one of those.
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

import pr_context  # noqa: E402

LAST_COMMIT = "2026-10-10T12:00:00Z"


def pr(**fields):
    base = {"number": 7, "title": "Fix the cache", "state": "OPEN", "isDraft": False,
            "url": "https://github.com/o/r/pull/7", "body": "## Problem\n\nslow",
            "author": {"login": "me"}, "baseRefName": "main", "headRefName": "fix/7",
            "headRefOid": "abc1234def", "headRepository": {"nameWithOwner": "o/r"},
            "headRepositoryOwner": {"login": "o"}, "isCrossRepository": False,
            "maintainerCanModify": False, "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN", "reviewDecision": "", "statusCheckRollup": [],
            "closingIssuesReferences": [], "reviews": [], "comments": [],
            "commits": [{"committedDate": LAST_COMMIT}]}
    base.update(fields)
    return base


def comment(login, body, url, created="2026-10-09T00:00:00Z", typename="User"):
    return {"databaseId": 1, "url": url, "createdAt": created, "body": body,
            "author": {"login": login, "__typename": typename}}


def thread(tid, comments, resolved=False, can_resolve=True, outdated=False, path="src/a.rs",
           line=12):
    return {"id": tid, "isResolved": resolved, "isOutdated": outdated, "path": path,
            "line": line, "originalLine": line, "viewerCanResolve": can_resolve,
            "viewerCanReply": True, "comments": {"nodes": comments}}


class PrContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.fixture = self.tmp / "fixture.json"
        self.gh = self.tmp / "gh"
        self.gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_gh.py"}" "$@"\n')
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        os.environ["FAKE_GH_FIXTURE"] = str(self.fixture)

    def run_with(self, data, ref="7", repo="o/r"):
        self.fixture.write_text(json.dumps({"pr": data.pop("pr", pr()), **data}))
        out, err = io.StringIO(), io.StringIO()
        args = ["pr_context", ref, "--gh", str(self.gh)] + (["-R", repo] if repo else [])
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pr_context.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_only_unresolved_threads_are_listed_across_pages(self):
        pages = [[thread("T1", [comment("rev", "rename this", "u1")]),
                  thread("T2", [comment("rev", "fixed already", "u2")], resolved=True)],
                 [thread("T3", [comment("rev", "add a test", "u3")])]]
        code, out, _ = self.run_with({"threads": pages})
        self.assertEqual(code, 0)
        self.assertIn("## Unresolved review threads (2 of 3)", out)
        self.assertIn("`T1`", out)
        self.assertIn("`T3`", out)
        self.assertNotIn("`T2`", out)

    def test_thread_says_who_it_waits_for_and_what_is_new(self):
        answered = thread("T1", [comment("rev", "why?", "u1"),
                                 comment("me", "because", "u2", created="2026-10-11T00:00:00Z")])
        pending = thread("T2", [comment("rev", "rename", "u3", created="2026-10-11T00:00:00Z")])
        _, out, _ = self.run_with({"threads": [[answered, pending]]})
        self.assertIn("`T1` · waiting for the reviewer", out)
        self.assertIn("`T2` · waiting for an answer from the PR side · **new since the last "
                      "commit**", out)

    def test_inline_comment_missing_from_every_thread_is_shown(self):
        threads = [[thread("T1", [comment("rev", "x", "https://g/c1")])]]
        rest = [[{"id": 11, "html_url": "https://g/c1", "user": {"login": "rev"}, "path": "a",
                  "line": 1, "body": "x", "created_at": "2026-10-09T00:00:00Z"},
                 {"id": 12, "html_url": "https://g/c2", "user": {"login": "bot[bot]"},
                  "path": "src/b.rs", "line": 4, "body": "use a const",
                  "created_at": "2026-10-09T00:00:00Z"}]]
        _, out, _ = self.run_with({"threads": threads, "rest": rest})
        self.assertIn("## Inline comments outside any thread (1)", out)
        self.assertIn("`src/b.rs:4` · id `12`", out)

    def test_failing_check_points_to_its_log_and_pending_one_is_flagged(self):
        checks = [{"__typename": "CheckRun", "name": "test", "workflowName": "CI",
                   "status": "COMPLETED", "conclusion": "FAILURE",
                   "detailsUrl": "https://github.com/o/r/actions/runs/55/job/66"},
                  {"__typename": "CheckRun", "name": "lint", "status": "IN_PROGRESS",
                   "conclusion": "", "detailsUrl": ""},
                  {"__typename": "StatusContext", "context": "ci/legacy", "state": "SUCCESS"}]
        _, out, _ = self.run_with({"pr": pr(statusCheckRollup=checks)})
        self.assertIn("(1 failing, 1 pending, 1 passing, 0 skipped)", out)
        self.assertIn("**fail** CI / test — log: `gh run view 55 --job 66 --log-failed`", out)
        self.assertIn("1 check(s) still running", out)

    def test_conflict_fork_and_closed_state_are_flagged(self):
        data = pr(mergeable="CONFLICTING", isCrossRepository=True, maintainerCanModify=False,
                  state="MERGED")
        _, out, _ = self.run_with({"pr": data})
        self.assertIn("conflicts with `main`", out)
        self.assertIn("you cannot push to this branch", out)
        self.assertIn("the pull request is MERGED", out)
        _, out, _ = self.run_with({"pr": pr(isCrossRepository=True, maintainerCanModify=True)})
        self.assertNotIn("you cannot push", out)

    def test_thread_the_viewer_cannot_resolve_is_flagged(self):
        threads = [[thread("T1", [comment("rev", "x", "u1")], can_resolve=False)]]
        _, out, _ = self.run_with({"threads": threads})
        self.assertIn("`T1` · waiting for an answer from the PR side · you cannot resolve it", out)
        self.assertIn("you cannot resolve 1 open thread(s)", out)

    def test_review_summaries_and_conversation_keep_only_text(self):
        reviews = [{"author": {"login": "rev"}, "state": "CHANGES_REQUESTED",
                    "submittedAt": "2026-10-09T00:00:00Z", "body": "Split this function."},
                   {"author": {"login": "rev2"}, "state": "APPROVED", "submittedAt": "", "body": ""}]
        comments = [{"author": {"login": "rev"}, "createdAt": "2026-10-11T00:00:00Z",
                     "url": "u9", "body": "Any update?"}]
        _, out, _ = self.run_with({"pr": pr(reviews=reviews, comments=comments,
                                            reviewDecision="CHANGES_REQUESTED")})
        self.assertIn("## Review summaries (1 with text)", out)
        self.assertIn("> Split this function.", out)
        self.assertNotIn("rev2", out)
        self.assertIn("**rev** · 2026-10-11 · u9 · **new since the last commit**", out)
        self.assertIn("changes requested", out)

    def test_someone_elses_pull_request_and_own_review_are_flagged(self):
        threads = [[thread("T1", [comment("me", "rename this", "u1")]),
                    thread("T2", [comment("rev", "add a test", "u2")])]]
        _, out, _ = self.run_with({"pr": pr(author={"login": "colleague"}), "threads": threads,
                                   "viewer": "me"})
        self.assertIn("you (me) are not the author: commits go to colleague's branch", out)
        self.assertIn("you opened 1 of the unresolved thread(s)", out)
        _, out, _ = self.run_with({"threads": threads, "viewer": "me"})
        self.assertNotIn("are not the author", out)

    def test_description_headings_do_not_become_sections(self):
        _, out, _ = self.run_with({})
        self.assertIn("> ## Problem", out)
        self.assertIn("## Flags\n\n- none", out)

    def test_url_names_the_repository_and_bad_refs_fail(self):
        code, out, _ = self.run_with({}, ref="https://github.com/o/r/pull/7", repo=None)
        self.assertEqual(code, 0)
        self.assertIn("# PR #7 Fix the cache", out)
        self.assertEqual(self.run_with({}, ref="8")[0], 1)
        self.assertEqual(self.run_with({}, ref="abc")[0], 1)


if __name__ == "__main__":
    unittest.main()
