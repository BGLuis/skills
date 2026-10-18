"""Stand-in for `gh` in the review tests: answers from the JSON fixture named by
FAKE_GH_FIXTURE and records every POST payload in it under `posted`.
"""

import json
import os
import sys


def main(args):
    path = os.environ["FAKE_GH_FIXTURE"]
    with open(path, encoding="utf-8") as f:
        fixture = json.load(f)
    reply = answer(fixture, args)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f)
    if reply is None:
        print(f"fake gh: unsupported call {args}", file=sys.stderr)
        return 2
    if isinstance(reply, int):
        print("HTTP 422: Unprocessable Entity", file=sys.stderr)
        return reply
    print(json.dumps(reply))
    return 0


def answer(fixture, args):
    if args[:2] == ["api", "user"]:
        return {"login": fixture.get("viewer", "me")}
    if args[:2] == ["pr", "view"]:
        return fixture.get("view", {})
    if args[:3] == ["api", "-X", "POST"]:
        with open(args[args.index("--input") + 1], encoding="utf-8") as f:
            fixture.setdefault("posted", []).append(json.load(f))
        return fixture.get("post_fails") or {"id": 99, "html_url": "https://g/review/99"}
    if args[0] != "api":
        return None
    endpoint = args[1]
    if endpoint.endswith("/files"):
        return [fixture.get("files", [])]
    if endpoint.endswith("/reviews"):
        return [fixture.get("reviews", [])]
    if "/pulls/" in endpoint:
        return fixture["pr"]
    return None


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
