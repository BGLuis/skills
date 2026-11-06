"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

A diagram in a report, a pull request, or ARCHITECTURE.md is a set of claims about the
code. validate_diagrams.py is what keeps those claims checkable: a node with no anchor,
an anchor that points at a line the file does not have, or a figure too big to read must
fail; a render check that could not run must say so instead of passing.
"""

import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import validate_diagrams  # noqa: E402

VALID = """\
    # Login

    ```mermaid
    flowchart LR
      accTitle: Login flow
      %% @browser: external
      %% @api: src/api.py:2-3
      %% @db: src/api.py#SELECT
      browser([Browser]) -->|"POST /login"| api[Auth API]
      api --> db[("users table")]
    ```
"""

API = "def login(user):\n    return SELECT\n# 3 lines\n"


class ValidateDiagramsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "api.py").write_text(API)

    def tearDown(self):
        self.tmp.cleanup()

    def run_on(self, markdown, *flags):
        doc = self.root / "doc.md"
        doc.write_text(textwrap.dedent(markdown))
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = validate_diagrams.main([*flags, str(doc)])
        return code, stdout.getvalue()

    def errors(self, output):
        return [l for l in output.splitlines() if l and ": warning: " not in l]

    def test_anchored_diagram_within_budget_passes(self):
        code, out = self.run_on(VALID, "--repo-root", str(self.root))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])

    def test_node_without_anchor_fails(self):
        code, out = self.run_on(VALID.replace("      %% @db: src/api.py#SELECT\n", ""))
        self.assertEqual(code, 1)
        self.assertIn("`db` has no anchor", out)

    def test_anchor_for_a_node_not_drawn_fails(self):
        code, out = self.run_on(VALID.replace("%% @browser: external",
                                              "%% @browser: external\n      %% @cache: external"))
        self.assertEqual(code, 1)
        self.assertIn("`cache`, which the diagram does not draw", out)

    def test_line_past_the_end_of_the_file_fails(self):
        code, out = self.run_on(VALID.replace("api.py:2-3", "api.py:2-40"),
                                "--repo-root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("outside the file's 3 lines", out)

    def test_missing_file_and_missing_symbol_fail(self):
        md = VALID.replace("src/api.py:2-3", "src/gone.py:1").replace("#SELECT", "#INSERT")
        code, out = self.run_on(md, "--repo-root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("`src/gone.py` does not exist", out)
        self.assertIn("`INSERT` does not occur in the file", out)

    def test_locations_unchecked_without_repo_root_is_reported(self):
        md = VALID.replace("api.py:2-3", "api.py:2-40")
        code, out = self.run_on(md)
        self.assertEqual(code, 0)
        self.assertIn("warning: locations not checked against the code", out)

    def test_diagram_above_the_maximum_fails(self):
        nodes = "\n".join(f"      n{i} --> n{i + 1}" for i in range(13))
        anchors = "\n".join(f"      %% @n{i}: external" for i in range(14))
        md = f"```mermaid\nflowchart LR\n  accTitle: big\n{anchors}\n{nodes}\n```\n"
        code, out = self.run_on(md)
        self.assertEqual(code, 1)
        self.assertIn("14 nodes / 13 edges exceeds the 12/16 maximum", out)

    def test_diagram_above_the_target_only_warns(self):
        nodes = "\n".join(f"  n{i} --> n{i + 1}" for i in range(10))
        anchors = "\n".join(f"  %% @n{i}: external" for i in range(11))
        code, out = self.run_on(f"```mermaid\nflowchart TD\n  accTitle: mid\n{anchors}\n{nodes}\n```\n")
        self.assertEqual(code, 0, out)
        self.assertIn("warning: 11 nodes / 10 edges is above the 9/12 target", out)

    def test_fan_out_counts_every_edge(self):
        md = ("```mermaid\nflowchart LR\n  accTitle: fan\n" +
              "".join(f"  %% @{x}: external\n" for x in "abcd") +
              "  a --> b & c & d\n```\n")
        code, out = self.run_on(md, "--max-edges", "2")
        self.assertEqual(code, 1)
        self.assertIn("4 nodes / 3 edges", out)

    def test_reserved_word_as_id_fails(self):
        md = VALID.replace("db[(", "end[(").replace("@db:", "@end:")
        code, out = self.run_on(md)
        self.assertEqual(code, 1)
        self.assertIn("`end` is a reserved word", out)

    def test_unquoted_label_with_parentheses_fails(self):
        code, out = self.run_on(VALID.replace("api[Auth API]", "api[Auth (v2)]"))
        self.assertEqual(code, 1)
        self.assertIn("quote it", out)
        code, _ = self.run_on(VALID.replace("api[Auth API]", 'api["Auth (v2)"]'))
        self.assertEqual(code, 0)

    def test_missing_acc_title_html_and_emoji_fail(self):
        md = VALID.replace("      accTitle: Login flow\n", "").replace("Auth API", "Auth <b>API</b> ✅")
        code, out = self.run_on(md)
        self.assertEqual(code, 1)
        self.assertIn("missing `accTitle:`", out)
        self.assertIn("HTML tag", out)
        self.assertIn("emoji", out)

    def test_beta_and_c4_types_fail(self):
        for kind in ("architecture-beta", "C4Context", "block-beta"):
            code, out = self.run_on(f"```mermaid\n{kind}\n  accTitle: x\n```\n")
            self.assertEqual(code, 1, kind)
            self.assertIn("does not render reliably on GitHub", out)

    def test_sequence_participants_need_anchors(self):
        md = textwrap.dedent("""\
            ```mermaid
            sequenceDiagram
              accTitle: Refresh
              participant C as Client
              %% @C: external
              C->>S: refresh token
              S-->>C: 200
            ```
        """)
        code, out = self.run_on(md)
        self.assertEqual(code, 1)
        self.assertIn("`S` has no anchor", out)

    def test_state_and_er_entities_need_anchors(self):
        md = textwrap.dedent("""\
            ```mermaid
            stateDiagram-v2
              accTitle: Order
              %% @Pending: src/api.py
              [*] --> Pending
              Pending --> Paid : payment confirmed
            ```

            ```mermaid
            erDiagram
              accTitle: Schema
              %% @USER: src/api.py
              USER ||--o{ ORDER : places
            ```
        """)
        code, out = self.run_on(md, "--repo-root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("`Paid` has no anchor", out)
        self.assertIn("`ORDER` has no anchor", out)

    def test_mermaid_inside_another_code_block_is_a_sample_not_a_figure(self):
        md = "````markdown\n```mermaid\nflowchart LR\n  a --> b\n```\n````\n"
        code, out = self.run_on(md)
        self.assertEqual(code, 0)
        self.assertIn("no mermaid blocks found", out)

    def test_render_without_a_renderer_is_reported_as_skipped(self):
        with mock.patch.object(validate_diagrams.shutil, "which", return_value=None):
            code, out = self.run_on(VALID, "--render")
        self.assertEqual(code, 0)
        self.assertIn("warning: render skipped", out)

    def test_render_failure_is_an_error(self):
        def fake_run(cmd, **kwargs):
            return mock.Mock(returncode=1, stderr="Error: Parse error on line 3:\n...a --> -->\n", stdout="")
        with mock.patch.object(validate_diagrams.subprocess, "run", side_effect=fake_run):
            code, out = self.run_on(VALID, "--render", "--mmdc", "mmdc")
        self.assertEqual(code, 1)
        self.assertIn("render failed: Error: Parse error on line 3:", out)


if __name__ == "__main__":
    unittest.main()
