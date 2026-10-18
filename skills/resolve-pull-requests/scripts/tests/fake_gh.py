"""Stand-in for `gh` in the pr_context tests: answers the four reads pr_context.py makes from
the JSON fixture named by FAKE_GH_FIXTURE (`repo`, `pr`, `threads` pages, `rest` pages).
"""

import json
import os
import sys


def main(args):
    with open(os.environ["FAKE_GH_FIXTURE"], encoding="utf-8") as f:
        fixture = json.load(f)
    if args[:2] == ["repo", "view"]:
        reply = {"nameWithOwner": fixture.get("repo", "o/r")}
    elif args[:2] == ["pr", "view"]:
        if args[2] != str(fixture["pr"]["number"]):
            print("GraphQL: Could not resolve to a PullRequest", file=sys.stderr)
            return 1
        reply = fixture["pr"]
    elif args[:2] == ["api", "graphql"]:
        reply = [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": page}}}}}
                 for page in fixture.get("threads", [[]])]
    elif args[:2] == ["api", "user"]:
        reply = {"login": fixture.get("viewer", "me")}
    elif args[0] == "api" and args[1].endswith("/comments"):
        reply = fixture.get("rest", [[]])
    else:
        print(f"fake gh: unsupported call {args}", file=sys.stderr)
        return 2
    print(json.dumps(reply))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
