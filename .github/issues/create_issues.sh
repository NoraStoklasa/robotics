#!/usr/bin/env bash
# Create labels, milestones and issues for the 3006ICT group project.
# Idempotent: re-running skips milestones and issues that already exist.
#
#   ./create_issues.sh [owner/repo]        default: NoraStoklasa/robotics
#   DRY_RUN=1 ./create_issues.sh           print actions without calling gh

set -euo pipefail

REPO="${1:-NoraStoklasa/robotics}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN="${DRY_RUN:-0}"

run() {
  if [[ "$DRY_RUN" == "1" ]]; then printf '  [dry-run] %s\n' "$*"; else "$@"; fi
}

command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh not authenticated: run 'gh auth login'"; exit 1; }
gh repo view "$REPO" >/dev/null 2>&1 || { echo "cannot access repo $REPO"; exit 1; }

echo "==> Target repository: $REPO"

# ----------------------------------------------------------------------
# Labels  (gh label create --force updates an existing label)
# ----------------------------------------------------------------------
echo "==> Labels"
create_label() {
  echo "  $1"
  run gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force
}
create_label "stream:vision"        "1D76DB" "Camera, target identification, distractor rejection, vision evaluation"
create_label "stream:navigation"    "0E8A16" "Occupancy grid, A*, waypoints, obstacle avoidance, motion"
create_label "stream:integration"   "5319E7" "State machine, telemetry, testing, report, presentation, submission"
create_label "type:feature"         "A2EEEF" "New capability in the controller"
create_label "type:research"        "FBCA04" "Investigation or measurement producing a decision record"
create_label "type:test"            "BFD4F2" "Evaluation, test harness or test matrix"
create_label "type:docs"            "D4C5F9" "Report, presentation or documentation"
create_label "type:chore"           "EDEDED" "Repo, environment or tooling setup"
create_label "priority:P0"          "B60205" "Blocks the mission or a graded deliverable"
create_label "priority:P1"          "D93F0B" "Important but not blocking"
create_label "needs-tutor-approval" "E99695" "Requires a technique outside the Weeks 1-8 toolbox"

# ----------------------------------------------------------------------
# Milestones  (skip when the title already exists)
# ----------------------------------------------------------------------
echo "==> Milestones"
existing_ms="$(gh api --paginate "repos/$REPO/milestones?state=all" --jq '.[].title' 2>/dev/null || true)"

create_milestone() {
  local title="$1" desc="$2"
  if grep -Fxq "$title" <<<"$existing_ms"; then
    echo "  = $title (exists)"
  else
    echo "  + $title"
    run gh api "repos/$REPO/milestones" -f title="$title" -f description="$desc" >/dev/null
  fi
}
create_milestone "M0 - Setup"                      "Repo, environment and team working agreement"
create_milestone "M1 - Sensing and motion baseline" "Devices, motion primitives, pose helpers, proximity safety"
create_milestone "M2 - Target identification"       "Camera-based identification of the mission target"
create_milestone "M3 - Navigation"                  "Occupancy grid, A*, waypoint following, obstacle avoidance"
create_milestone "M4 - Mission integration"         "State machine, stopping rule, telemetry and time budget"
create_milestone "M5 - Evaluation and deliverables" "Test matrix, failure analysis, report, presentation, submission"

# ----------------------------------------------------------------------
# Issues, in dependency order
# ----------------------------------------------------------------------
echo "==> Issues"

# Titles already present, so a re-run does not duplicate them.
existing_titles="$(gh issue list --repo "$REPO" --state all --limit 500 --json title --jq '.[].title' 2>/dev/null || true)"

# Read a YAML front-matter scalar from an issue file.
fm() { sed -n '/^---$/,/^---$/p' "$1" | grep -m1 "^$2:" | cut -d: -f2- | sed 's/^ *//; s/^"//; s/"$//'; }

# Body = everything after the closing front-matter delimiter.
body_of() { awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$1"; }

create_issue() {
  local file="$DIR/$1"
  [[ -f "$file" ]] || { echo "  ! missing $1"; return 1; }

  local title labels milestone
  title="$(fm "$file" title)"
  milestone="$(fm "$file" milestone)"
  labels="$(sed -n '/^labels:/p' "$file" | sed 's/^labels: *\[//; s/\]$//; s/, */,/g')"

  if grep -Fxq "$title" <<<"$existing_titles"; then
    echo "  = $title (exists)"
    return 0
  fi

  echo "  + $title"
  local tmp; tmp="$(mktemp)"
  body_of "$file" > "$tmp"

  # Append dependencies as titles; link_dependencies.sh rewrites them to #N later.
  local deps
  deps="$(sed -n '/^depends_on:/p' "$file" | sed 's/^depends_on: *\[//; s/\] *$//')"
  if [[ -n "$deps" ]]; then
    {
      echo
      echo "## Depends on"
      # Split on '", "' so titles containing commas survive intact.
      sed 's/", *"/\n/g' <<<"$deps" | sed 's/^"//; s/"$//' | while IFS= read -r d; do
        [[ -n "$d" ]] && echo "- $d"
      done
    } >> "$tmp"
  fi

  run gh issue create --repo "$REPO" \
    --title "$title" \
    --body-file "$tmp" \
    --label "$labels" \
    --milestone "$milestone"

  rm -f "$tmp"
}

create_issue 01-repo-environment-working-agreement.md
create_issue 26-architecture-and-component-contracts.md
create_issue 27-decision-and-failure-logs.md
create_issue 28-ai-usage-and-external-resources.md
create_issue 02-verify-worlds-device-baseline.md
create_issue 03-motion-primitives-pose-utilities.md
create_issue 04-calibrate-proximity-thresholds.md
create_issue 05-measure-poster-appearance-vs-standoff.md
create_issue 06-choose-identification-approach.md
create_issue 07-isolate-poster-region.md
create_issue 08-identify-target-with-confidence.md
create_issue 09-evaluate-accuracy-distractor-rejection.md
create_issue 10-load-grid-verify-conversion.md
create_issue 29-early-end-to-end-skeleton.md
create_issue 11-obstacle-clearance-strategy.md
create_issue 12-implement-astar.md
create_issue 13-waypoint-following-p-control.md
create_issue 14-reactive-avoidance-with-recovery.md
create_issue 15-station-visit-ordering.md
create_issue 16-mission-state-machine.md
create_issue 17-final-stop-rule.md
create_issue 18-telemetry-and-time-budget.md
create_issue 19-shuffled-assignment-worlds.md
create_issue 20-run-full-test-matrix.md
create_issue 21-failure-cases-and-fixes.md
create_issue 22-report-vision-chapters.md
create_issue 23-report-navigation-chapters.md
create_issue 24-presentation-and-demo-rehearsal.md
create_issue 25-assemble-report-and-package-submission.md

echo
echo "==> Done."
echo "Next: run ./link_dependencies.sh $REPO to rewrite depends_on titles as #N references."
