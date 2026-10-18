"""Run: python3 -m unittest discover -s scripts/tests   (from the skill directory)

dependency_diff.py is how a review notices that a pull request brings in a vulnerable,
yanked, deprecated, or outdated version. A parser that misreads a lockfile hides the
change; a flag that stops firing lets the version through unremarked.
"""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import dependency_diff  # noqa: E402

CARGO = """version = 4

[[package]]
name = "styx"
version = "{own}"

[[package]]
name = "serde"
version = "{serde}"
source = "registry+https://github.com/rust-lang/crates.io-index"
{extra}"""
TOKIO = """
[[package]]
name = "tokio"
version = "1.40.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
"""


def npm_lock(packages):
    return json.dumps({"lockfileVersion": 3, "packages": {
        "": {"name": "app"}, **{f"node_modules/{n}": {"version": v} for n, v in packages.items()},
        "node_modules/local": {"link": True}}})


UV = """version = 1

[[package]]
name = "app"
version = "0.1.0"
source = {{ editable = "." }}

[[package]]
name = "Requests"
version = "{requests}"
source = {{ registry = "https://pypi.org/simple" }}
"""


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class DependencyDiffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = cls.root = Path(cls.tmp.name)
        git(root, "init", "-q", "-b", "main")
        files = {
            "Cargo.lock": CARGO.format(own="0.1.0", serde="1.0.200", extra=TOKIO),
            "web/package-lock.json": npm_lock({"lodash": "4.17.21", "left-pad": "1.3.0"}),
            "py/uv.lock": UV.format(requests="2.31.0"),
            "go.sum": "github.com/BurntSushi/toml v1.3.0 h1:x\n"
                      "github.com/BurntSushi/toml v1.3.0/go.mod h1:y\n",
            "requirements.txt": "flask==3.0.0\n",
        }
        cls.commit(files, "base")
        files.update({
            "Cargo.lock": CARGO.format(own="0.2.0", serde="1.0.150", extra=""),
            "web/package-lock.json": npm_lock({"lodash": "4.17.15", "request": "2.88.2",
                                               "@scope/pkg": "0.2.0"}),
            "py/uv.lock": UV.format(requests="2.32.0"),
            "go.sum": "github.com/BurntSushi/toml v1.4.0 h1:z\n",
            "requirements.txt": "flask==3.0.0\nanes==0.1.6  # pinned\n",
            "yarn.lock": "# yarn\n",
            "crates/x/Cargo.toml": "[package]\n",
            "web/package.json": "{}\n",
        })
        cls.commit(files, "head")
        cls.commit({"crates/x/Cargo.toml": "[package]\nname = \"x\"\n"}, "manifest-only")

    @classmethod
    def commit(cls, files, message):
        for name, text in files.items():
            path = cls.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        git(cls.root, "add", ".")
        git(cls.root, "commit", "-q", "-m", message)
        git(cls.root, "tag", message)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_script(self, *extra, facts=None, osv=None, fail=None, base="base", head="head"):
        facts = facts or {}

        def fake_fetch(url, body=None):
            if fail and fail in url:
                raise urllib.error.URLError("down")
            if "osv.dev" in url:
                return {"results": [{"vulns": [{"id": i} for i in (osv or {}).get(
                    (q["package"]["name"], q["version"]), [])]} for q in body["queries"]]}
            for key, value in facts.items():
                if key in url:
                    return value
            raise urllib.error.URLError("no fixture")

        out = io.StringIO()
        with mock.patch.object(dependency_diff, "fetch_json", fake_fetch), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = dependency_diff.main(["x", "--repo", str(self.root), "--base", base,
                                         "--head", head, *extra])
        return code, out.getvalue()

    def test_each_lockfile_kind_is_read(self):
        code, out = self.run_script("--offline")
        self.assertEqual(code, 0)
        self.assertIn("crates.io `serde` | 1.0.200 → 1.0.150 (downgraded)", out)
        self.assertIn("crates.io `tokio` | − 1.40.0", out)
        self.assertNotIn("`styx`", out)
        self.assertIn("npm `lodash` | 4.17.21 → 4.17.15 (downgraded)", out)
        self.assertIn("npm `request` | + 2.88.2", out)
        self.assertIn("npm `@scope/pkg` | + 0.2.0", out)
        self.assertIn("npm `left-pad` | − 1.3.0", out)
        self.assertNotIn("`local`", out)
        self.assertIn("PyPI `requests` | 2.31.0 → 2.32.0 (upgraded)", out)
        self.assertNotIn("PyPI `app`", out)
        self.assertIn("Go `github.com/BurntSushi/toml` | v1.3.0 → v1.4.0 (upgraded)", out)
        self.assertIn("PyPI `anes` | + 0.1.6", out)
        self.assertNotIn("`flask`", out)

    def test_unparsed_lockfile_manifest_without_lock_and_offline_are_flagged(self):
        _, out = self.run_script("--offline")
        self.assertIn("read by hand (not parsed): `yarn.lock`", out)
        self.assertNotIn("manifest changed", out)
        self.assertIn("offline: latest versions", out)
        self.assertIn("is downgraded 1.0.200 → 1.0.150", out)
        _, out = self.run_script("--offline", base="head", head="manifest-only")
        self.assertIn("manifest changed but no lockfile did: `crates/x/Cargo.toml`", out)

    def test_advisories_yanked_deprecated_and_breaking_lag_are_flagged(self):
        facts = {
            "registry.npmjs.org/request/latest": {"version": "2.88.2"},
            "registry.npmjs.org/request/2.88.2": {"deprecated": "request has been deprecated"},
            "registry.npmjs.org/lodash/latest": {"version": "4.17.21"},
            "registry.npmjs.org/lodash/4.17.15": {},
            "pypi.org/pypi/requests/json": {"info": {"version": "2.34.2"}},
            "pypi.org/pypi/requests/2.32.0/json": {"info": {"yanked": True,
                                                            "yanked_reason": "CVE mitigation"}},
            "pypi.org/pypi/anes/json": {"info": {"version": "0.2.1"}},
            "pypi.org/pypi/anes/0.1.6/json": {"info": {"yanked": False}},
        }
        _, out = self.run_script(facts=facts, osv={("lodash", "4.17.15"): ["GHSA-p6mc-m468-83gw"]})
        self.assertIn("npm `lodash` 4.17.15 has known advisories: GHSA-p6mc-m468-83gw", out)
        self.assertIn("npm `request` 2.88.2 is deprecated: request has been deprecated", out)
        self.assertIn("PyPI `requests` 2.32.0 is yanked: CVE mitigation", out)
        self.assertIn("PyPI `anes` 0.1.6 is added a breaking release behind the latest (0.2.1)", out)
        self.assertNotIn("`request` 2.88.2 is added a breaking", out)

    def test_a_registry_or_osv_failure_is_reported_not_fatal(self):
        code, out = self.run_script(fail="osv.dev")
        self.assertEqual(code, 0)
        self.assertIn("OSV could not be queried", out)
        self.assertIn("lookup failed: URLError", out)

    def test_lookups_are_capped_but_advisories_cover_everything(self):
        _, out = self.run_script("--max-lookups", "1", osv={("request", "2.88.2"): ["X-1"]})
        self.assertIn("registry lookups capped at 1", out)
        self.assertIn("`request` 2.88.2 has known advisories: X-1", out)

    def test_bad_ref_fails(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = dependency_diff.main(["x", "--repo", str(self.root), "--base", "nope",
                                         "--head", "head", "--offline"])
        self.assertEqual(code, 1)

    def test_breaking_part_follows_semver_zero(self):
        self.assertEqual(dependency_diff.breaking_part("1.4.2"), (1,))
        self.assertEqual(dependency_diff.breaking_part("0.3.9"), (0, 3))
        self.assertEqual(dependency_diff.go_escape("github.com/BurntSushi/toml"),
                         "github.com/!burnt!sushi/toml")


if __name__ == "__main__":
    unittest.main()
