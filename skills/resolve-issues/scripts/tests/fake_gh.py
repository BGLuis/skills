"""Stand-in for `gh` in the issue_context tests: answers `issue view` and `pr view` from the
JSON fixture named by FAKE_GH_FIXTURE, keyed `owner/repo#N` (`-` when no -R is given).
"""

import json
import os
import sys


def main(args):
    with open(os.environ["FAKE_GH_FIXTURE"], encoding="utf-8") as f:
        fixture = json.load(f)
    repo = args[args.index("-R") + 1] if "-R" in args else "-"
    kind = {"issue": "issues", "pr": "prs"}.get(args[0])
    if not kind or args[1] != "view":
        print(f"fake gh: unsupported call {args}", file=sys.stderr)
        return 2
    item = fixture.get(kind, {}).get(f"{repo}#{args[2]}")
    if item is None:
        print(f"GraphQL: Could not resolve to an issue or pull request with the number of "
              f"{args[2]}.", file=sys.stderr)
        return 1
    print(json.dumps(item))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
