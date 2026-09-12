#!/usr/bin/env bash
# Phase 2 follow-up: rewrite the "## Depends on" titles in each created issue
# into real #N references. Run after create_issues.sh.
#
#   ./link_dependencies.sh [owner/repo]     default: NoraStoklasa/robotics
#   DRY_RUN=1 ./link_dependencies.sh        show the rewrite without applying it
#
# Idempotent: a line already rewritten to "- #12 Title" is left alone.
#
# The rewrite is done in awk with literal string lookup. Bash's ${var//a/b} is
# not usable here: its pattern is a glob, and titles such as "[Vision] ..."
# would be read as a character class and never match.

set -euo pipefail

REPO="${1:-NoraStoklasa/robotics}"
DRY_RUN="${DRY_RUN:-0}"

command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }
gh repo view "$REPO" >/dev/null 2>&1 || { echo "cannot access repo $REPO"; exit 1; }

echo "==> Linking dependencies in $REPO"

MAP="$(mktemp)"; BODY="$(mktemp)"; OUT="$(mktemp)"
trap 'rm -f "$MAP" "$BODY" "$OUT"' EXIT

# number<TAB>title for every issue in the repo
gh issue list --repo "$REPO" --state all --limit 500 --json number,title \
  --jq '.[] | "\(.number)\t\(.title)"' > "$MAP"

linked=0; skipped=0; unresolved=0

while IFS=$'\t' read -r num title; do
  gh issue view "$num" --repo "$REPO" --json body --jq .body > "$BODY"
  grep -q '^## Depends on' "$BODY" || { skipped=$((skipped+1)); continue; }

  awk -v mapfile="$MAP" '
    BEGIN {
      FS = "\t"
      while ((getline line < mapfile) > 0) {
        split(line, a, "\t")
        num[a[2]] = a[1]
      }
      close(mapfile)
    }
    /^## Depends on/ { inDeps = 1; print; next }
    inDeps && /^- / {
      t = substr($0, 3)
      if (t ~ /^#/)        { print; next }   # already linked
      if (t in num)        { print "- #" num[t] " " t; changed = 1; next }
      print "- " t
      print "UNRESOLVED\t" t > "/dev/stderr"
      next
    }
    { print }
    END { exit(changed ? 0 : 9) }
  ' "$BODY" > "$OUT" 2>/tmp/link_err.$$ && rc=0 || rc=$?

  if [[ -s /tmp/link_err.$$ ]]; then
    while IFS=$'\t' read -r _ bad; do
      echo "  ! #$num: no issue titled \"$bad\""
      unresolved=$((unresolved+1))
    done < /tmp/link_err.$$
  fi
  rm -f /tmp/link_err.$$

  if [[ "$rc" == "9" ]]; then
    skipped=$((skipped+1))
    continue
  fi

  echo "  #$num $title"
  if [[ "$DRY_RUN" == "1" ]]; then
    awk '/^## Depends on/{f=1} f' "$OUT" | sed 's/^/      /'
  else
    gh issue edit "$num" --repo "$REPO" --body-file "$OUT" >/dev/null
  fi
  linked=$((linked+1))
done < "$MAP"

echo "==> Done. linked=$linked, unchanged=$skipped, unresolved=$unresolved"
