"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

Each test pairs a draft that breaks one rule with the message that names it. A rule that
stops firing lets an issue reach GitHub with fake evidence, a leaked secret, a dangling
`T1`, or a shape the repository forbids; a rule that fires on a good draft trains people
to ignore the validator. The shipped examples must stay clean.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import validate_issues  # noqa: E402

EXAMPLES = HERE.parent.parent / "examples"

TASK = """**Goal:** the list scrolls without rendering the rows off screen.

**Evidence:** `src/list.ts:10-20` · **Base commit:** `abc1234`

**Feasibility:** `src/hook.ts:4-30` already windows a fixed-height list.

**Implementation:** reuse the window hook.
**Acceptance criteria:** `npm test -- list` passes.

**Not verified:** nothing ran on a device.
"""

PT_TASK = """**Objetivo:** a lista rola sem renderizar as linhas fora da tela.

**Evidência:** `src/list.ts:10-20` · **Commit base:** `abc1234`

**Viabilidade:** `src/hook.ts:4-30` já faz a janela com altura fixa.

**Implementação:** reutilizar o hook de janela.
**Critério de aceite:** `npm test -- lista` passa.

**Não verificado:** nada rodou em aparelho.
"""

FINDING = """**Goal:** two exports fit in the container at once.

**Evidence:** `src/export.ts:22-40` · **Base commit:** `abc1234`

**Baseline:** peak RSS 1.1 GB median, n = 10.

**Reproduction:** export a month and watch `VmHWM`.

**Fix:** stream the rows.
**Acceptance criteria:** peak RSS ≤ 100 MB on the same reproduction (`VmHWM`).

**Not verified:** nothing beyond the epic.
"""

EPIC = """**Base commit:** `abc1234`

**Verdict:** memory grows with the month.

| Order | Key | Sub-issue |
|---|---|---|
| 1 | P-01 | Stream the rows |

**Not verified:** nothing ran in production.
"""


def run(issues, bodies, profile=None, repo=None, **top):
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        manifest = {"repo": "o/r", "language": "en", "mode": "audit",
                    "visibility": "private", **top, "issues": issues}
        if profile is not None:
            manifest["profile"] = "profile.json"
            (d / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
        (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        for name, text in bodies.items():
            (d / name).write_text(text, encoding="utf-8")
        errors, warnings = validate_issues.validate(d, repo)
        return "\n".join(errors), "\n".join(warnings)


def task(body=TASK, **fields):
    issue = {"key": "T1", "kind": "task", "file": "t1.md", "title": "List: window the rows"}
    issue.update(fields)
    return [issue], {"t1.md": body}


def errors_of(body=TASK, **fields):
    return run(*task(body, **fields))[0]


class ExamplesTest(unittest.TestCase):
    def test_every_shipped_example_is_clean(self):
        dirs = [p for p in EXAMPLES.iterdir() if (p / "manifest.json").is_file()]
        self.assertGreaterEqual(len(dirs), 3)
        for d in dirs:
            errors, _ = validate_issues.validate(d)
            self.assertEqual(errors, [], d.name)

    def test_minimal_task_is_clean(self):
        self.assertEqual(errors_of(), "")


class EvidenceTest(unittest.TestCase):
    def evidence(self, text):
        return errors_of(TASK.replace("`src/list.ts:10-20`", text))

    def test_host_and_port_is_not_file_evidence(self):
        self.assertIn("has no `file:line`", self.evidence("the server at `localhost:3000`"))
        self.assertIn("has no `file:line`", self.evidence("`api.example.com:443`"))
        self.assertIn("has no `file:line`", self.evidence("`127.0.0.1:8080`"))

    def test_file_permalink_and_zero_result_search_are_evidence(self):
        self.assertEqual(self.evidence("`Dockerfile:3`"), "")
        self.assertEqual(self.evidence("`deploy/api.yaml:31`"), "")
        self.assertEqual(self.evidence(
            "https://github.com/o/r/blob/abc1234/src/list.ts#L10-L20"), "")
        body = TASK.replace("`src/list.ts:10-20`", "nothing yet\n\n```bash\n"
                            "grep -rn useWindow src/\n# → 0 results\n```\n")
        self.assertEqual(errors_of(body), "")

    def test_location_outside_the_evidence_field_does_not_count(self):
        body = TASK.replace("`src/list.ts:10-20`", "slow list").replace(
            "reuse the window hook.", "reuse `src/hook.ts:4`.")
        self.assertIn("has no `file:line`", errors_of(body))

    def test_base_commit_or_sha_permalink_is_required(self):
        self.assertIn("no **Base commit:**",
                      errors_of(TASK.replace(" · **Base commit:** `abc1234`", "")))


class SafetyTest(unittest.TestCase):
    def test_secret_in_body_is_rejected(self):
        body = TASK + '\n```ts\nconst key = "AKIAZ7Q2M4K8P1R6T3WX";\n```\n'
        self.assertIn("possible AWS access key", errors_of(body))
        body = TASK + "\nToken: ghp_" + "a" * 36 + "\n"
        self.assertIn("possible GitHub token", errors_of(body))

    def test_redacted_credential_is_accepted(self):
        self.assertEqual(errors_of(TASK + '\n`password = "<redacted>"`\n'), "")

    def test_body_over_the_github_limit_is_rejected(self):
        self.assertIn("GitHub rejects more than 65536", errors_of(TASK + "x" * 66000))

    def test_security_finding_is_never_filed_on_a_public_repository(self):
        issues, bodies = task(security=True)
        self.assertIn("route it through SECURITY.md", run(issues, bodies, visibility="public")[0])
        self.assertEqual(run(issues, bodies, visibility="private")[0], "")


class ShapeTest(unittest.TestCase):
    def test_hard_wrapped_paragraph_and_list_item_are_rejected(self):
        wrapped = TASK.replace("reuse the window hook.", "reuse the window\nhook.")
        self.assertIn("hard-wrapped paragraph", errors_of(wrapped))
        item = TASK + "\n- [ ] a criterion that\n  wraps onto a second line\n"
        self.assertIn("hard-wrapped paragraph", errors_of(item))

    def test_label_lines_and_lists_are_not_wrapping(self):
        body = TASK.replace("`npm test -- list` passes.", "\n- [ ] `npm test` passes\n"
                            "- [ ] `npm run lint` passes")
        self.assertEqual(errors_of(body), "")

    def test_acceptance_must_follow_implementation_directly(self):
        body = TASK.replace("hook.\n**Acceptance", "hook.\n\n**Acceptance")
        self.assertIn("must come right below `**Implementation:**`", errors_of(body))

    def test_title_length(self):
        self.assertIn("max 100", errors_of(title="List: " + "x" * 100))
        _, warnings = run(*task(title="List: " + "x" * 80))
        self.assertIn("board card shows about 80", warnings)



def criterion(text, extra=""):
    return errors_of(TASK.replace("`npm test -- list` passes.", text) + extra)


class CriteriaTest(unittest.TestCase):
    """A criterion that cannot fail, or that nobody knows how to check, closes nothing."""

    def test_criterion_must_name_its_check(self):
        self.assertIn("names no check", criterion("the rows render."))
        self.assertIn("names no check", criterion("2 rows render."))
        self.assertEqual(criterion("the rows render (`npm test -- list`)."), "")
        self.assertEqual(criterion("the rows follow the spec [F1].",
                                   "\n| # | Source |\n|---|---|\n| F1 | spec |\n"), "")

    def test_each_checklist_item_is_a_criterion(self):
        errors = criterion("\n- [ ] `npm test` passes\n- [ ] the list feels smooth")
        self.assertIn("'the list feels smooth' names no check", errors)
        self.assertNotIn("'`npm test` passes'", errors)

    def test_vague_term_needs_a_threshold(self):
        self.assertIn("rests on 'faster'", criterion("scrolling is faster (`npm run bench`)."))
        self.assertIn("rests on 'as expected'", criterion("`npm test` behaves as expected."))
        self.assertEqual(criterion("a frame takes ≤ 16 ms, faster than today (`npm run bench`).",
                                   "\n**Baseline:** 41 ms median, n = 10.\n"), "")

    def test_vague_term_in_portuguese(self):
        body = PT_TASK.replace("`npm test -- lista` passa.",
                               "a rolagem fica mais rápida (`npm run bench`).")
        self.assertIn("rests on 'mais rápida'", run(*task(body), language="pt-BR")[0])
        self.assertEqual(run(*task(PT_TASK), language="pt-BR")[0], "")

    def test_threshold_needs_a_baseline(self):
        text = "`npm run bench` shows at most 16 ms per frame."
        self.assertIn("needs **Baseline:**", criterion(text))
        self.assertEqual(criterion(text, "\n**Baseline:** 41 ms median, n = 10.\n"), "")
        self.assertEqual(criterion(text, "\n**Baseline:** [modeled] from the node count.\n"), "")
        self.assertIn("needs **Baseline:**", criterion(text, "\n**Baseline:** slow today.\n"))

    def test_numbers_inside_code_are_not_thresholds(self):
        self.assertEqual(criterion('`parse("x < 5")` returns an error.'), "")


class FeasibilityTest(unittest.TestCase):
    """A task with no proof that it can be built is a guess that gets estimated as work."""

    def feasibility(self, text, extra=""):
        return errors_of(TASK.replace("`src/hook.ts:4-30` already windows a fixed-height list.",
                                      text) + extra)

    def test_task_needs_feasibility_unless_it_is_the_spike(self):
        body = TASK.replace("**Feasibility:** `src/hook.ts:4-30` already windows a fixed-height "
                            "list.\n\n", "")
        self.assertIn("task without the **Feasibility:**", errors_of(body))
        self.assertEqual(errors_of(body, spike=True), "")

    def test_feasibility_needs_a_proof(self):
        self.assertIn("names no proof", self.feasibility("it should be possible."))
        self.assertIn("names no proof", self.feasibility("use `ResizeObserver`."))
        self.assertEqual(self.feasibility("a probe: https://gist.github.com/o/1a2b."), "")
        self.assertEqual(self.feasibility("the API supports it [F1].",
                                          "\n| # | Source |\n|---|---|\n| F1 | docs |\n"), "")
        self.assertEqual(self.feasibility("a probe against turso 0.8.1:\n\n```sh\n$ cargo run\n"
                                          "FOREIGN KEY constraint failed\n```"), "")

    def test_feasibility_resting_on_a_spike_waits_for_it(self):
        issues = [{"key": "S1", "kind": "task", "file": "s1.md", "title": "A: probe",
                   "spike": True},
                  {"key": "T2", "kind": "task", "file": "t2.md", "title": "A: build"}]
        t2 = TASK.replace("`src/hook.ts:4-30` already windows a fixed-height list.",
                          "answered by S1.")
        self.assertIn("rests on 'S1', which is not in `blocked_by`",
                      run(issues, {"s1.md": TASK, "t2.md": t2})[0])
        issues[1]["blocked_by"] = ["S1"]
        t2 = t2.replace("\n\n**Implementation:**", "\n\n**Depends on:** S1\n\n**Implementation:**")
        self.assertEqual(run(issues, {"s1.md": TASK, "t2.md": t2})[0], "")

    def test_only_a_task_can_be_a_spike(self):
        issues = [{"key": "P-01", "kind": "finding", "file": "p.md", "title": "A: x",
                   "spike": True}]
        self.assertIn("only a task can be a spike", run(issues, {"p.md": FINDING})[0])


class StandaloneTest(unittest.TestCase):
    """An issue is read alone: in a notification, on a board card, months later."""

    def test_goal_is_a_field_or_a_heading(self):
        no_goal = TASK.replace("**Goal:** the list scrolls without rendering the rows off "
                               "screen.\n\n", "")
        self.assertIn("task without the **Goal:**", errors_of(no_goal))
        self.assertEqual(errors_of("## Goal\n\nWindowed list.\n\n" + no_goal), "")

    def test_sub_issue_states_what_was_not_verified(self):
        issues = [{"key": "epic", "kind": "epic", "file": "e.md", "title": "Audit: export"},
                  {"key": "P-01", "kind": "finding", "file": "p.md", "parent": "epic",
                   "title": "Export: stream the rows"}]
        bare = FINDING.replace("\n**Not verified:** nothing beyond the epic.\n", "")
        self.assertIn("finding without the **Not verified:**",
                      run(issues, {"e.md": EPIC, "p.md": bare})[0])

    def test_open_questions_are_an_unchecked_checklist(self):
        self.assertIn("is an unchecked `- [ ]` question",
                      errors_of(TASK + "\n### Open questions\n\n- **Keys.** Which ones?\n"))
        self.assertIn("lists no question", errors_of(TASK + "\n### Open questions\n\nNone.\n"))
        self.assertEqual(errors_of(TASK + "\n### Open questions\n\n- [ ] **Keys.** Which?\n"
                                   "  - for example Ctrl+Tab\n"), "")


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class GitTest(unittest.TestCase):
    """With --repo, a location that does not exist at the base commit is caught before
    anyone opens the issue and finds nothing there."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        git(cls.root, "init", "-q")
        (cls.root / "src").mkdir()
        (cls.root / "src" / "list.ts").write_text("".join(f"line {i}\n" for i in range(25)))
        (cls.root / "src" / "hook.ts").write_text("".join(f"line {i}\n" for i in range(30)))
        git(cls.root, "add", ".")
        git(cls.root, "commit", "-q", "-m", "init")
        cls.sha = subprocess.run(["git", "-C", str(cls.root), "rev-parse", "HEAD"], check=True,
                                 capture_output=True, text=True).stdout.strip()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, body):
        return run(*task(body.replace("abc1234", self.sha[:9])), repo=self.root)[0]

    def test_location_inside_the_file_is_clean(self):
        self.assertEqual(self.check(TASK), "")

    def test_line_past_the_end_is_rejected(self):
        self.assertIn("line 40 is past the end of `src/list.ts` (25 lines",
                      self.check(TASK.replace("src/list.ts:10-20", "src/list.ts:10-40")))

    def test_missing_file_is_rejected(self):
        self.assertIn("`src/gone.ts` does not exist",
                      self.check(TASK.replace("src/list.ts:10-20", "src/gone.ts:3")))

    def test_unknown_base_commit_is_rejected(self):
        body = TASK.replace("`abc1234`", "`deadbee`")
        self.assertIn("commit `deadbee` is not in", run(*task(body), repo=self.root)[0])

    def test_permalink_of_this_repository_is_checked_and_others_are_not(self):
        link = f"https://github.com/o/r/blob/{self.sha}/src/list.ts#L10-L90"
        self.assertIn("line 90 is past the end",
                      self.check(TASK.replace("`src/list.ts:10-20`", link)))
        other = link.replace("/o/r/", "/x/y/")
        self.assertEqual(self.check(TASK.replace("`src/list.ts:10-20`", other)), "")

    def test_without_repo_nothing_is_read_from_git(self):
        self.assertEqual(errors_of(TASK.replace("src/list.ts:10-20", "src/gone.ts:3")), "")


class HierarchyTest(unittest.TestCase):
    def epic(self, epic_body, mode="audit"):
        issues = [{"key": "epic", "kind": "epic", "file": "e.md", "title": "Audit: export"},
                  {"key": "P-01", "kind": "finding", "file": "p.md", "parent": "epic",
                   "title": "Export: stream the rows"}]
        return run(issues, {"e.md": epic_body, "p.md": FINDING}, mode=mode)[0]

    def test_epic_lists_each_sub_issue_in_a_table_body_row_or_checklist(self):
        self.assertEqual(self.epic(EPIC), "")
        checklist = EPIC.split("| Order")[0] + "- [ ] P-01 Stream the rows\n\n**Not verified:** x\n"
        self.assertEqual(self.epic(checklist), "")
        header_only = EPIC.replace("| Order | Key | Sub-issue |", "| Fonte | P-01 | x |").replace(
            "| 1 | P-01 | Stream the rows |\n", "")
        self.assertIn("'P-01' is not a row of the epic's table", self.epic(header_only))

    def test_verdict_is_required_in_an_audit_epic_only(self):
        no_verdict = EPIC.replace("**Verdict:** memory grows with the month.\n", "")
        self.assertIn("epic without the **Verdict:**", self.epic(no_verdict))
        self.assertEqual(self.epic(no_verdict, mode="proposal"), "")

    def test_parent_can_be_an_existing_issue(self):
        self.assertEqual(errors_of(parent="#98"), "")
        self.assertEqual(errors_of(parent="https://github.com/o/r/issues/98"), "")
        self.assertIn("neither an epic of the manifest", errors_of(parent="epic-x"))


class DependsOnTest(unittest.TestCase):
    def pair(self, t2_body, **t2):
        issues = [{"key": "T1", "kind": "task", "file": "t1.md", "title": "A: one"},
                  {"key": "T2", "kind": "task", "file": "t2.md", "title": "A: two", **t2}]
        return run(issues, {"t1.md": TASK, "t2.md": t2_body})[0]

    def with_depends(self, refs):
        return TASK.replace("\n\n**Implementation:**",
                            f"\n\n**Effort:** 1 d · **Depends on:** {refs}\n\n**Implementation:**")

    def test_depends_on_mirrors_blocked_by(self):
        self.assertEqual(self.pair(self.with_depends("T1, #92"), blocked_by=["T1", "#92"]), "")

    def test_reference_without_native_link_is_rejected(self):
        self.assertIn("'T1' is under Depends on but not in `blocked_by`",
                      self.pair(self.with_depends("T1")))

    def test_unknown_key_is_rejected(self):
        self.assertIn("'T9' is under Depends on but is not a key",
                      self.pair(self.with_depends("T9")))

    def test_blocked_by_must_be_written_in_the_body(self):
        self.assertIn("not mirrored", self.pair(TASK, blocked_by=["T1"]))

    def test_cycle_is_rejected(self):
        issues = [{"key": "T1", "kind": "task", "file": "t1.md", "title": "A: one",
                   "blocked_by": ["T2"]},
                  {"key": "T2", "kind": "task", "file": "t2.md", "title": "A: two",
                   "blocked_by": ["T1"]}]
        self.assertIn("blocked-by cycle", run(issues, {"t1.md": TASK, "t2.md": TASK})[0])


PROFILE = {
    "sources": ["AGENTS.md section 10"],
    "title_pattern": "^(feat|fix|chore): .+$",
    "labels": [{"pattern": "^type:", "min": 1, "max": 1}, {"pattern": "^area:", "min": 1}],
    "require_milestone": True,
    "require_parent": True,
    "heading_level": 2,
    "sections": {"task": ["Goal"]},
    "required_text": {"task": ["`just check` passes"]},
    "forbidden_fields": ["**Effort:**"],
}
PROFILED = "## Goal\n\nWindowed list.\n\n" + TASK + "\n- [ ] `just check` passes\n"
GOOD = {"title": "feat: window the list", "labels": ["type:feat", "area:reader"],
        "milestone": "v1", "parent": "#98"}


class ProfileTest(unittest.TestCase):
    def check(self, body=PROFILED, profile=PROFILE, **changes):
        return run(*task(body, **{**GOOD, **changes}), profile=profile)[0]

    def test_compliant_issue_is_clean(self):
        self.assertEqual(self.check(), "")

    def test_title_labels_milestone_and_parent(self):
        self.assertIn("does not match the profile pattern", self.check(title="Window the list"))
        self.assertIn("2 label(s) match `^type:`",
                      self.check(labels=["type:feat", "type:fix", "area:reader"]))
        self.assertIn("0 label(s) match `^area:`", self.check(labels=["type:feat"]))
        issues, bodies = task(PROFILED, **{k: v for k, v in GOOD.items()
                                           if k not in ("milestone", "parent")})
        errors = run(issues, bodies, profile=PROFILE)[0]
        self.assertIn("requires a milestone", errors)
        self.assertIn("requires a parent", errors)

    def test_sections_required_text_and_forbidden_fields(self):
        self.assertIn("missing the `## Goal` section",
                      self.check(PROFILED.replace("## Goal", "### Goal")))
        self.assertIn("missing the required text", self.check("## Goal\n\nx\n\n" + TASK))
        self.assertIn("`**Effort:**` does not go in the body",
                      self.check(PROFILED + "\n**Effort:** 3\n"))

    def test_profile_needs_sources_and_known_keys(self):
        bad = {**PROFILE, "sources": [], "label_rules": []}
        errors = self.check(profile=bad)
        self.assertIn("`sources` must list", errors)
        self.assertIn("unknown key 'label_rules'", errors)


if __name__ == "__main__":
    unittest.main()
