"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

review_context.py decides what the reviewer is warned about before running a stranger's
branch; post_review.py is the last check before a review becomes public and permanent.
A flag that stops firing lets an outside contributor's build script run unread; a check
that stops firing posts comments GitHub rejects, a review of code that has since
changed, or the same review twice.
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

import post_review  # noqa: E402
import review_context  # noqa: E402

PATCH = "\n".join([
    "@@ -10,4 +10,5 @@ fn a() {",
    " keep 10",
    "-old 11",
    "+new 11",
    "+new 12",
    " keep 12/13",
    "@@ -40,2 +41,2 @@ fn b() {",
    " keep 40/41",
    "+new 42",
])


def pull(**fields):
    base = {"number": 7, "title": "Add a cache", "state": "open", "draft": False,
            "html_url": "https://github.com/o/r/pull/7", "body": "Adds a cache.",
            "user": {"login": "contrib"}, "author_association": "CONTRIBUTOR",
            "head": {"ref": "feat/cache", "sha": "abc1234def567",
                     "repo": {"full_name": "contrib/r"}},
            "base": {"ref": "main", "repo": {"full_name": "o/r"}},
            "additions": 20, "deletions": 4, "changed_files": 2}
    base.update(fields)
    return base


def file(name, status="modified", patch=PATCH):
    item = {"filename": name, "status": status, "additions": 3, "deletions": 1}
    if patch is not None:
        item["patch"] = patch
    return item


class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.fixture = self.tmp / "fixture.json"
        self.gh = self.tmp / "gh"
        self.gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_gh.py"}" "$@"\n')
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        os.environ["FAKE_GH_FIXTURE"] = str(self.fixture)

    def call(self, module, args, fixture):
        self.fixture.write_text(json.dumps(fixture))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(["x", *args, "--gh", str(self.gh)])
        return code, out.getvalue() + err.getvalue()


class ReviewContextTest(Harness):
    def context(self, **fixture):
        fixture.setdefault("pr", pull())
        fixture.setdefault("files", [file("src/cache.rs"), file("tests/cache_test.rs")])
        return self.call(review_context, ["7", "-R", "o/r"], fixture)[1]

    def test_outside_author_changing_build_files_is_flagged(self):
        out = self.context(files=[file("src/cache.rs"), file("build.rs"),
                                  file(".github/workflows/ci.yml"), file("tests/c_test.rs")])
        self.assertIn("contrib (CONTRIBUTOR, outside the repository)", out)
        self.assertIn("from the fork contrib/r", out)
        self.assertIn("read them before running anything from this branch", out)
        self.assertIn("`build.rs`", out)
        self.assertIn("`.github/workflows/ci.yml`", out)

    def test_member_changing_build_files_is_noted_not_flagged(self):
        out = self.context(pr=pull(author_association="MEMBER"),
                           files=[file("package.json"), file("src/a.ts"), file("src/a.test.ts")])
        self.assertIn("Files that run on build, test, or install: `package.json`.", out)
        self.assertNotIn("read them before running", out)

    def test_code_without_tests_large_size_and_missing_description(self):
        out = self.context(pr=pull(additions=900, deletions=200, body=""),
                           files=[file("src/cache.rs"), file("README.md")])
        self.assertIn("code changes with no test change", out)
        self.assertIn("1100 changed lines: too large", out)
        self.assertIn("no description", out)
        self.assertIn("| `README.md` | modified | +3 −1 | doc |", out)

    def test_files_without_a_diff_and_own_pull_request(self):
        out = self.context(files=[file("assets/logo.png", patch=None), file("tests/t_test.rs")],
                           viewer="contrib")
        self.assertIn("no diff from the API for `assets/logo.png`", out)
        self.assertIn("you are the author", out)

    def test_issues_checks_and_earlier_reviews(self):
        view = {"closingIssuesReferences": [{"number": 3, "url": "u3"}],
                "statusCheckRollup": [{"__typename": "CheckRun", "name": "test",
                                       "status": "COMPLETED", "conclusion": "FAILURE"},
                                      {"__typename": "CheckRun", "name": "lint",
                                       "status": "IN_PROGRESS", "conclusion": ""}]}
        reviews = [{"user": {"login": "maint"}, "state": "CHANGES_REQUESTED",
                    "submitted_at": "2026-10-10T00:00:00Z", "body": "Please add a test."}]
        out = self.context(view=view, reviews=reviews)
        self.assertIn("- #3 u3", out)
        self.assertIn("(2: 1 failing, 1 pending)", out)
        self.assertIn("**maint** CHANGES_REQUESTED 2026-10-10: Please add a test.", out)
        self.assertIn("none: find what asked for this change", self.context())


class DiffLinesTest(unittest.TestCase):
    def test_sides_follow_the_hunk_numbering(self):
        sides = post_review.diff_lines(PATCH)
        self.assertEqual(sorted(sides["RIGHT"]), [10, 11, 12, 13, 41, 42])
        self.assertEqual(sorted(sides["LEFT"]), [10, 11, 12, 40])
        self.assertEqual(sides["RIGHT"][13], 0)
        self.assertEqual(sides["RIGHT"][42], 1)


class PostReviewTest(Harness):
    def draft(self, **fields):
        data = {"repo": "o/r", "pr": 7, "commit_id": "abc1234", "event": "COMMENT",
                "body": "Summary.", "comments": [{"path": "src/cache.rs", "line": 12,
                                                  "body": "**issue:** x"}]}
        data.update(fields)
        path = self.tmp / "review.json"
        path.write_text(json.dumps(data))
        return path

    def post(self, path, *extra, **fixture):
        fixture.setdefault("pr", pull())
        fixture.setdefault("files", [file("src/cache.rs")])
        code, out = self.call(post_review, [str(path), *extra], fixture)
        return code, out, json.loads(self.fixture.read_text())

    def test_valid_review_is_posted_once_and_recorded(self):
        path = self.draft(comments=[{"path": "src/cache.rs", "line": 12, "start_line": 10,
                                     "body": "a"},
                                    {"path": "src/cache.rs", "line": 11, "side": "LEFT",
                                     "body": "b"}])
        code, out, state = self.post(path)
        self.assertEqual(code, 0, out)
        sent = state["posted"][0]
        self.assertEqual(sent["event"], "COMMENT")
        self.assertEqual(sent["comments"][0]["start_line"], 10)
        self.assertEqual(sent["comments"][1]["side"], "LEFT")
        self.assertEqual(json.loads(path.read_text())["posted"]["url"], "https://g/review/99")
        code, out, state = self.post(path)
        self.assertEqual(code, 1)
        self.assertIn("already posted", out)
        self.assertEqual(len(state.get("posted", [])), 0)

    def test_dry_run_posts_nothing(self):
        code, out, state = self.post(self.draft(), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("would post a COMMENT review on o/r#7", out)
        self.assertNotIn("posted", state)

    def test_line_outside_the_diff_or_file_outside_the_pull_request_is_refused(self):
        bad = self.draft(comments=[{"path": "src/cache.rs", "line": 30, "body": "x"},
                                   {"path": "src/other.rs", "line": 1, "body": "y"},
                                   {"path": "src/cache.rs", "line": 42, "start_line": 12,
                                    "body": "z"}])
        code, out, state = self.post(bad)
        self.assertEqual(code, 1)
        self.assertIn("line 30 is not on the RIGHT side", out)
        self.assertIn("the file is not in this pull request's diff", out)
        self.assertIn("lines 12–42 span two hunks", out)
        self.assertNotIn("posted", state)

    def test_new_push_since_the_draft_is_refused(self):
        code, out, _ = self.post(self.draft(), pr=pull(head={"ref": "f", "sha": "fff0000",
                                                             "repo": {"full_name": "contrib/r"}}))
        self.assertEqual(code, 1)
        self.assertIn("the head is now `fff0000`", out)

    def test_own_pull_request_can_only_be_commented(self):
        code, out, _ = self.post(self.draft(event="APPROVE"), viewer="contrib")
        self.assertIn("GitHub refuses APPROVE on your own pull request", out)
        code, _, _ = self.post(self.draft(event="COMMENT"), viewer="contrib")
        self.assertEqual(code, 0)

    def test_event_and_body_are_checked(self):
        self.assertIn("`event` must be one of", self.post(self.draft(event="LGTM"))[1])
        self.assertIn("needs a `body`", self.post(self.draft(event="REQUEST_CHANGES", body=""))[1])
        self.assertEqual(self.post(self.draft(event="APPROVE", body="", comments=[]))[0], 0)

    def test_failed_post_keeps_the_draft_unposted(self):
        path = self.draft()
        code, out, _ = self.post(path, post_fails=1)
        self.assertEqual(code, 1)
        self.assertNotIn("posted", json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
