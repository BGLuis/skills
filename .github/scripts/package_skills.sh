#!/usr/bin/env bash
# Packages skills/ into dist/: all-skills.zip, one <skill>.zip per skill (bundling
# any dependent skills) and SHA256SUMS.txt. Usage: package_skills.sh [git-ref]   (default: HEAD)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REF="${1:-HEAD}"
OUT="dist"

rm -rf "$OUT"
mkdir -p "$OUT"

# git archive packs tracked files only, so local junk never leaks into a release.
git archive --format=zip -o "$OUT/all-skills.zip" "$REF:skills"

count=0
for dir in skills/*/; do
  skill="$(basename "$dir")"
  [ -f "${dir}SKILL.md" ] || { echo "::error::skills/$skill has no SKILL.md" >&2; exit 1; }

  python3 "$SCRIPT_DIR/skill_deps.py" bundle "$REF" "$skill" "$OUT/$skill.zip"
  deps="$(python3 "$SCRIPT_DIR/skill_deps.py" deps "$REF" "$skill")"

  zip_list="$(unzip -Z1 "$OUT/$skill.zip")"
  for item in $skill $deps; do
    printf '%s\n' "$zip_list" | grep -qx "$item/SKILL.md" \
      || { echo "::error::$skill.zip is missing $item/SKILL.md" >&2; exit 1; }
  done
  count=$((count + 1))
done

zips="$(find "$OUT" -maxdepth 1 -name '*.zip' ! -name all-skills.zip | wc -l)"
[ "$zips" -eq "$count" ] || { echo "::error::expected $count skill zips, got $zips" >&2; exit 1; }

(cd "$OUT" && sha256sum -- *.zip > SHA256SUMS.txt)

echo "Packaged $count skills + all-skills.zip into $OUT/"
