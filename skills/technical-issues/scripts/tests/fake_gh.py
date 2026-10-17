"""Stand-in for `gh` in the publish tests: answers only the calls publish_issues.py makes.

State lives in the JSON file named by FAKE_GH_STATE; every call is appended to its `log`.
Knobs set by the tests: `visibility`, `version`, `fail_on_create` (the nth create fails),
and `drop_label` (a label GitHub "loses", to exercise the read-back).
"""

import json
import os
import sys


def main(args):
    path = os.environ["FAKE_GH_STATE"]
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("issues", {})
    state.setdefault("blocked_by", {})
    state.setdefault("log", []).append(args)
    code = handle(state, args)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)
    return code


def opt(args, name):
    return args[args.index(name) + 1] if name in args else None


def opts(args, name):
    return [args[i + 1] for i, a in enumerate(args) if a == name]


def handle(state, args):
    if args == ["--version"]:
        print(f"gh version {state.get('version', '2.102.0')} (2026-09-30)")
        return 0
    if args[:2] == ["repo", "view"]:
        print(json.dumps({"visibility": state.get("visibility", "private").upper()}))
        return 0
    if args[:2] == ["issue", "create"]:
        state["creates"] = state.get("creates", 0) + 1
        if state.get("fail_on_create") == state["creates"]:
            print("HTTP 502: Bad Gateway", file=sys.stderr)
            return 1
        number = state.get("next", 100)
        state["next"] = number + 1
        with open(opt(args, "--body-file"), encoding="utf-8") as f:
            body = f.read()
        parent = opt(args, "--parent")
        state["issues"][str(number)] = {
            "title": opt(args, "--title"),
            "labels": [x for x in opts(args, "--label") if x != state.get("drop_label")],
            "milestone": opt(args, "--milestone"),
            "parent": int(parent) if parent else None,
            "body": body,
        }
        print(f"https://github.com/{opt(args, '-R')}/issues/{number}")
        return 0
    if args[:2] == ["issue", "view"]:
        issue = state["issues"][args[2]]
        fields = opt(args, "--json").split(",")
        out = {}
        for field in fields:
            if field == "labels":
                out["labels"] = [{"name": x} for x in issue["labels"]]
            elif field == "milestone":
                out["milestone"] = {"title": issue["milestone"]} if issue["milestone"] else None
            else:
                out[field] = issue[field]
        print(json.dumps(out))
        return 0
    if args[:2] == ["issue", "edit"]:
        with open(opt(args, "--body-file"), encoding="utf-8") as f:
            state["issues"][args[2]]["body"] = f.read()
        return 0
    if args[:2] == ["api", "graphql"]:
        number = opt(args, "-F").split("=", 1)[1]
        parent = state["issues"][number]["parent"]
        print(json.dumps({"data": {"repository": {"issue": {
            "parent": {"number": parent} if parent else None}}}}))
        return 0
    if args[0] == "api":
        endpoint = next(a for a in args[1:] if a.startswith("repos/"))
        number = endpoint.split("/")[4]
        if endpoint.endswith("/dependencies/blocked_by"):
            if "POST" in args:
                blocker = int(opt(args, "-F").split("=", 1)[1]) - 1000
                state["blocked_by"].setdefault(number, []).append(blocker)
                return 0
            page = [{"number": n} for n in state["blocked_by"].get(number, [])]
            print(json.dumps([page]))
            return 0
        print(json.dumps({"id": 1000 + int(number), "number": int(number)}))
        return 0
    print(f"fake gh: unhandled call {args}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
