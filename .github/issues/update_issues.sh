#!/usr/bin/env bash
# Push the local issue markdown back onto existing GitHub issues, matched by title.
# Issues that do not exist yet are reported and left to create_issues.sh.
#
#   ./update_issues.sh [owner/repo] [file ...]   default repo: NoraStoklasa/robotics
#   DRY_RUN=1 ./update_issues.sh                 show what would change
#
# Labels and milestone are re-applied from the front matter as well, so a change
# there is not silently lost. Run link_dependencies.sh afterwards to turn the
# appended "## Depends on" titles back into #N references.

set -euo pipefail

REPO="${1:-NoraStoklasa/robotics}"; shift || true
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN="${DRY_RUN:-0}"

command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }
gh repo view "$REPO" >/dev/null 2>&1 || { echo "cannot access repo $REPO"; exit 1; }

FILES=("$@")
if [[ ${#FILES[@]} -eq 0 ]]; then
  FILES=("$DIR"/[0-9][0-9]-*.md)
fi

MAP="$(mktemp)"; trap 'rm -f "$MAP"' EXIT
gh issue list --repo "$REPO" --state all --limit 500 --json number,title \
  --jq '.[] | "\(.number)\t\(.title)"' > "$MAP"

fm() { sed -n '/^---$/,/^---$/p' "$1" | grep -m1 "^$2:" | cut -d: -f2- | sed 's/^ *//; s/^"//; s/"$//'; }
body_of() { awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$1"; }

updated=0; missing=0
for file in "${FILES[@]}"; do
  [[ -f "$file" ]] || continue
  title="$(fm "$file" title)"
  num="$(awk -F'\t' -v t="$title" '$2==t{print $1; exit}' "$MAP")"
  if [[ -z "$num" ]]; then
    echo "  ? $(basename "$file") — no issue titled \"$title\" (run create_issues.sh)"
    missing=$((missing+1)); continue
  fi

  tmp="$(mktemp)"
  body_of "$file" > "$tmp"
  deps="$(sed -n '/^depends_on:/p' "$file" | sed 's/^depends_on: *\[//; s/\] *$//')"
  if [[ -n "$deps" ]]; then
    {
      echo
      echo "## Depends on"
      sed 's/", *"/\n/g' <<<"$deps" | sed 's/^"//; s/"$//' | while IFS= read -r d; do
        [[ -n "$d" ]] && echo "- $d"
      done
    } >> "$tmp"
  fi

  labels="$(sed -n '/^labels:/p' "$file" | sed 's/^labels: *\[//; s/\]$//; s/, */,/g')"
  milestone="$(fm "$file" milestone)"

  echo "  #$num $title"
  if [[ "$DRY_RUN" == "1" ]]; then
    diff <(gh issue view "$num" --repo "$REPO" --json body --jq .body) "$tmp" | sed 's/^/      /' || true
  else
    gh issue edit "$num" --repo "$REPO" --body-file "$tmp" \
      --add-label "$labels" --milestone "$milestone" >/dev/null
  fi
  rm -f "$tmp"
  updated=$((updated+1))
done

echo "==> Done. updated=$updated, not-yet-created=$missing"
