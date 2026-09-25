#!/bin/sh
# test-check-no-internal-references.sh
#
# Regression suite for check-no-internal-references.py.
#
# The defect under test: a private-tracker reference (a root-ecosystem backlog
# item, an app-internal path or slug, a private planning-repo path) written
# into a comment or a decision document reaches this PUBLIC repository and,
# from there, every downstream sync -- which is exactly what happened on
# 2026-09-25, when four files carried this class of reference and tripped
# cascade-cli's own equivalent check only after a routine shapes sync.
#
# Every assertion below is paired with a NEGATIVE CONTROL: a planted violation
# in a throwaway scratch directory, which the check must catch and must name.
# A check that has only ever been observed passing is not evidence that it can
# fail. The suite also proves the check is not vacuous in both directions: an
# empty result on THIS repository must mean "scanned and clean", and a scan
# that finds nothing to walk at all must be a hard error, not a silent PASS.
#
# Every planted sample below is built from split fragments (adjacent quoted
# strings with no space, which the shell concatenates at RUN time but which
# are not contiguous in this file's own SOURCE text) for the same reason
# check-no-internal-references.py assembles its own patterns from fragments:
# written out whole, this suite file would itself be flagged by the check it
# tests, and excluding this file from the scan to work around that would
# create the one place in the repository a real reference could hide instead.
#
# Usage: ./scripts/test-check-no-internal-references.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK="$SCRIPT_DIR/check-no-internal-references.py"
PYTHON="${PYTHON:-python3}"

PASSED=0
FAILED=0

pass() { PASSED=$((PASSED + 1)); echo "  PASS  $1"; }
fail() { FAILED=$((FAILED + 1)); echo "  FAIL  $1"; echo "        $2"; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "check-no-internal-references.py regression suite"
echo ""

# ── 1. The repository itself passes ────────────────────────────────────────
if (cd "$SPEC_ROOT" && "$PYTHON" "$CHECK" >/dev/null 2>&1); then
  pass "this repository, as committed, carries no internal reference"
else
  (cd "$SPEC_ROOT" && "$PYTHON" "$CHECK" 2>&1 | tail -20)
  fail "this repository, as committed, carries no internal reference" \
       "the check reports a hit against unmodified sources"
fi

# ── 2. Negative control: a root-ecosystem backlog reference, with its noun ──
mkdir -p "$WORK/dirty1"
printf '%s\n' "tracked under root back""log 3.14 for follow-up" > "$WORK/dirty1/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty1" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "root_backlog"; then
  pass "a root-ecosystem backlog reference, named with its noun, is caught"
else
  fail "a root-ecosystem backlog reference, named with its noun, is caught" "$OUT"
fi

# ── 3. Negative control: a bare backlog id, no noun ──────────────────────────
mkdir -p "$WORK/dirty2"
printf '%s\n' "the day boundary is not yet measured (root ""3.484), so it warns" > "$WORK/dirty2/a.ttl"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty2" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "bare_root_num"; then
  pass "a bare backlog id with no noun is caught"
else
  fail "a bare backlog id with no noun is caught" "$OUT"
fi

# ── 3b. Negative control: the same, wrapped across a line break ─────────────
# A real instance, missed by an earlier per-line version of this check:
# decisions/2026-09-24-canonical-layer-location.md wrapped "root" onto one
# line and its number onto the next, ordinary Markdown prose reflow.
mkdir -p "$WORK/dirty2b"
printf '%s\n' "a citation (root" "3.501) that prose-wrapped across a line" > "$WORK/dirty2b/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty2b" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "bare_root_num"; then
  pass "a bare backlog id wrapped across a line break is still caught"
else
  fail "a bare backlog id wrapped across a line break is still caught" "$OUT"
fi

# ── 4. Negative control: an app-internal backlog slug in brackets ───────────
mkdir -p "$WORK/dirty3"
printf '%s\n' "filed against the app while scoping [SOME-INTERNAL""-SLUG]" > "$WORK/dirty3/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty3" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "bracket_slug"; then
  pass "a bracketed app-internal backlog slug is caught"
else
  fail "a bracketed app-internal backlog slug is caught" "$OUT"
fi

# ── 5. Negative control: an app repo name and its internal planning subpath ─
mkdir -p "$WORK/dirty4"
printf '%s\n' "see cascade-""workbench/docs""/plan""ning/2026-01-01-scope.md" > "$WORK/dirty4/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty4" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "workbench_repo_name" && echo "$OUT" | grep -q "docs_planning_path"; then
  pass "an app repo name and its planning subpath are both caught"
else
  fail "an app repo name and its planning subpath are both caught" "$OUT"
fi

# ── 6. Negative control: a private partner-facing planning-repo path ────────
mkdir -p "$WORK/dirty5"
printf '%s\n' "write-up in plan""ning/spikes/2026-09-23-measurement.md" > "$WORK/dirty5/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty5" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "planning_repo_path"; then
  pass "a private planning-repo path is caught"
else
  fail "a private planning-repo path is caught" "$OUT"
fi

# ── 7. Negative control: a company-only local drafts-folder path ────────────
mkdir -p "$WORK/dirty6"
printf '%s\n' "Jed-only analysis lives in Dev-root""-docs, never in the tracker" > "$WORK/dirty6/a.md"
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty6" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "dev_root_docs_path"; then
  pass "a company-only local drafts-folder path is caught"
else
  fail "a company-only local drafts-folder path is caught" "$OUT"
fi

# ── 8. Clean negative control: prose that must NOT match ─────────────────────
# Adjacent-but-different text the patterns must not false-positive on: a FHIR
# root OID, a pod being "re-rooted", an ordinary version-with-decimal string,
# and an unrelated bracketed all-caps acronym with no hyphen.
mkdir -p "$WORK/clean1"
cat > "$WORK/clean1/a.md" <<'EOF'
The C-CDA <id> root OID is not a tracker reference. A Pod is copied, exported
and re-rooted; that is not one either. Release 3.10 shipped fine. See [FHIR]
for the standard. Root cause analysis is unrelated to any of this.
EOF
OUT="$("$PYTHON" "$CHECK" "$WORK/clean1" 2>&1)"
if [ $? -eq 0 ] && echo "$OUT" | grep -q "PASS"; then
  pass "ordinary prose that merely resembles the patterns does not false-positive"
else
  fail "ordinary prose that merely resembles the patterns does not false-positive" "$OUT"
fi

# ── 9. Non-vacuity: an empty tree must be a hard error, not a silent PASS ────
mkdir -p "$WORK/empty"
OUT="$("$PYTHON" "$CHECK" "$WORK/empty" 2>&1)"
if [ $? -eq 2 ] && echo "$OUT" | grep -q "ERROR"; then
  pass "a tree with nothing to scan is a hard error, not a silent PASS"
else
  fail "a tree with nothing to scan is a hard error, not a silent PASS" "$OUT"
fi

# ── 10. An unstaged file inside a real git tree is still scanned ────────────
# A .gitignore'd file is correctly invisible, but an ordinary untracked file
# that simply has not been `git add`ed yet must still be caught -- it will be
# committed, and a scan that only sees staged/committed content would miss it
# right up until the commit that ships it.
mkdir -p "$WORK/dirty7" && cd "$WORK/dirty7"
git init -q
printf '%s\n' "tracked, and unremarkable" > tracked.md
git add -A && git commit -q -m init
printf '%s\n' "not yet added: root back""log 9.9" > untracked.md
OUT="$("$PYTHON" "$CHECK" "$WORK/dirty7" 2>&1)"
if [ $? -ne 0 ] && echo "$OUT" | grep -q "untracked.md"; then
  pass "an unstaged file in a git tree is still scanned"
else
  fail "an unstaged file in a git tree is still scanned" "$OUT"
fi

echo ""
echo "passed: $PASSED   failed: $FAILED"
[ "$FAILED" -eq 0 ] || exit 1
