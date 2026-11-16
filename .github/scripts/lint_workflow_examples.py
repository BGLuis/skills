#!/usr/bin/env python3
"""Lints the complete workflows embedded in a skill's Markdown files.

The github-actions skill states that its examples pass actionlint and zizmor. This
extracts every fenced `yaml` block that is a whole workflow, writes it under a
temporary `.github/workflows/`, and runs both linters on it with the images that the
skill's references/versions.md names, so the claim is checked on every change.

Usage: python3 .github/scripts/lint_workflow_examples.py skills/github-actions
Needs Docker. Exit code 1 on any finding outside the documented false positives.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

FENCE = re.compile(r"^( *)```yaml\n(.*?)^\1```", re.M | re.S)

# Files whose workflows are wrong on purpose.
EXPECTED_BAD = {"anti-patterns.md"}

# actionlint predates these keys (references/review-checklist.md §2). The `parallel:`
# message is only accepted on a line that really is a `parallel:` step.
ACTIONLINT_FALSE_POSITIVES = (
    'unexpected key "cache-mode" for "job" section',
    'unexpected key "queue" for "concurrency" section',
)
PARALLEL_MESSAGE = 'step must run script with "run" section or run action with "uses" section'


def workflows_in(markdown: Path) -> list[str]:
    found = []
    for indent, body in FENCE.findall(markdown.read_text(encoding="utf-8")):
        text = "\n".join(line[len(indent):] for line in body.split("\n"))
        if not (re.search(r"^on:", text, re.M) and re.search(r"^jobs:", text, re.M)):
            continue
        jobs = yaml.safe_load(text).get("jobs") or {}
        # A snippet that elides its steps ("# ... the release matrix") is not lintable.
        if all(isinstance(job, dict) and ("steps" in job or "uses" in job) for job in jobs.values()):
            found.append(text)
    return found


def linter_images(skill_dir: Path) -> tuple[str, str]:
    versions = (skill_dir / "references" / "versions.md").read_text(encoding="utf-8")
    actionlint = re.search(r"`(rhysd/actionlint:[\w.]+)`", versions)
    zizmor = re.search(r"`(ghcr\.io/zizmorcore/zizmor:[\w.]+)`", versions)
    if not actionlint or not zizmor:
        sys.exit(f"{skill_dir}/references/versions.md does not name the linter images")
    return actionlint.group(1), zizmor.group(1)


def docker(root: Path, image: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "run", "--rm", "-v", f"{root}:/repo:ro", "-w", "/repo", image, *args],
        capture_output=True,
        text=True,
    )


def actionlint_errors(root: Path, image: str) -> list[str]:
    files = sorted(str(p.relative_to(root)) for p in (root / ".github" / "workflows").glob("*.yml"))
    result = docker(root, image, "-oneline", "-no-color", *files)
    # actionlint exits 1 when it finds problems; anything higher means it did not run.
    # stderr is not scanned for findings: `docker run` writes its image-pull progress there.
    errors = [result.stderr.strip()] if result.returncode > 1 else []
    for line in result.stdout.splitlines():
        if not line.strip() or any(known in line for known in ACTIONLINT_FALSE_POSITIVES):
            continue
        location = re.match(r"(?P<file>[^:]+):(?P<line>\d+):\d+: ", line)
        if PARALLEL_MESSAGE in line and location:
            source = (root / location["file"]).read_text(encoding="utf-8").splitlines()
            if "parallel:" in source[int(location["line"]) - 1]:
                continue
        errors.append(line)
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    skill_dir = Path(sys.argv[1])
    actionlint_image, zizmor_image = linter_images(skill_dir)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The linter images run as another user; the temporary directory is 0700 by default.
        root.chmod(0o755)
        target = root / ".github" / "workflows"
        target.mkdir(parents=True)
        for markdown in sorted(skill_dir.rglob("*.md")):
            if markdown.name in EXPECTED_BAD:
                continue
            for index, text in enumerate(workflows_in(markdown)):
                (target / f"{markdown.stem}-{index}.yml").write_text(text, encoding="utf-8")
        count = len(list(target.glob("*.yml")))
        if count == 0:
            sys.exit(f"no complete workflow found under {skill_dir}")
        print(f"{count} workflows extracted from {skill_dir}")

        failed = False
        errors = actionlint_errors(root, actionlint_image)
        for error in errors:
            print(f"::error::actionlint: {error}")
        failed = failed or bool(errors)

        zizmor = docker(root, zizmor_image, "--offline", "--no-progress", ".")
        if zizmor.returncode != 0:
            print(zizmor.stdout)
            print(zizmor.stderr, file=sys.stderr)
            print("::error::zizmor reported findings in the workflow examples")
            failed = True

    print("Workflow examples: " + ("FAILED" if failed else "clean"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
