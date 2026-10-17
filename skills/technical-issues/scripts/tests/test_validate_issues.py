"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

Each test pairs a draft that breaks one rule with the message that names it. A rule that
stops firing lets an issue reach GitHub with fake evidence, a leaked secret, a dangling
`T1`, or a shape the repository forbids; a rule that fires on a good draft trains people
to ignore the validator. The shipped examples must stay clean.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import validate_issues  # noqa: E402

EXAMPLES = HERE.parent.parent / "examples"

TASK = """**Evidence:** `src/list.ts:10-20` · **Base commit:** `abc1234`

**Implementation:** reuse the window hook.
**Acceptance criteria:** `npm test -- list` passes.

**Not verified:** nothing ran on a device.
"""

FINDING = """**Evidence:** `src/export.ts:22-40` · **Base commit:** `abc1234`

**Reproduction:** export a month and watch `VmHWM`.

**Fix:** stream the rows.
**Acceptance criteria:** peak RSS ≤ 100 MB.
"""

EPIC = """**Base commit:** `abc1234`

**Verdict:** memory grows with the month.

| Order | Key | Sub-issue |
|---|---|---|
| 1 | P-01 | Stream the rows |

**Not verified:** nothing ran in production.
"""


def run(issues, bodies, profile=None, **top):
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
        errors, warnings = validate_issues.validate(d)
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

    def test_vague_acceptance_criterion_warns(self):
        body = TASK.replace("`npm test -- list` passes.", "it is faster.")
        errors, warnings = run(*task(body))
        self.assertEqual(errors, "")
        self.assertIn("names no command, number, or source", warnings)


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
