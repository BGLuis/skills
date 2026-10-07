#!/usr/bin/env bash
# Packages skills/ into dist/: all-skills.zip, one <skill>.zip per skill and
# SHA256SUMS.txt. Usage: package_skills.sh [git-ref]   (default: HEAD)
set -euo pipefail

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
  git archive --format=zip --prefix="$skill/" -o "$OUT/$skill.zip" "$REF:skills/$skill"
  unzip -Z1 "$OUT/$skill.zip" | grep -qx "$skill/SKILL.md" \
    || { echo "::error::$skill.zip is missing $skill/SKILL.md" >&2; exit 1; }
  count=$((count + 1))
done

zips="$(find "$OUT" -maxdepth 1 -name '*.zip' ! -name all-skills.zip | wc -l)"
[ "$zips" -eq "$count" ] || { echo "::error::expected $count skill zips, got $zips" >&2; exit 1; }

(cd "$OUT" && sha256sum -- *.zip > SHA256SUMS.txt)

echo "Packaged $count skills + all-skills.zip into $OUT/"
