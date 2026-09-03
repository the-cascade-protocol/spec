#!/bin/sh
# test-check-contexts.sh
#
# Regression suite for check-contexts.mjs.
#
# The defect under test: a JSON-LD context term whose value is prose (a section
# divider written as a term, "__comment_core": "=== Core ... ===") makes the
# reference processor refuse the WHOLE document, so no conformant consumer can
# apply the context. Three published contexts carried eight such keys for
# months and every hand-rolled in-house reader read past them
# (jayostis/spec#48, 2026-09-03).
#
# This suite REINTRODUCES a prose-valued key into a scratch copy and requires a
# named refusal, pairs it with a positive control, and checks that the two ways
# the check could become vacuous (processor missing, nothing to check) are hard
# errors rather than green.
#
# Usage: ./scripts/test-check-contexts.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK="$SCRIPT_DIR/check-contexts.mjs"
NODE="${NODE:-node}"

PASSED=0
FAILED=0

pass() { PASSED=$((PASSED + 1)); echo "  PASS  $1"; }
fail() { FAILED=$((FAILED + 1)); echo "  FAIL  $1"; echo "        $2"; }

# A missing processor is a hard failure, never a skip: skipping the suite
# because a dependency is absent reports green while testing nothing.
if ! "$NODE" -e "require('$SCRIPT_DIR/node_modules/jsonld')" 2>/dev/null; then
  echo "ERROR: $NODE cannot load jsonld from scripts/node_modules; run: npm ci --prefix scripts" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "check-contexts regression suite"
echo ""

# 1. Positive control: a clean copy of a published context is accepted.
mkdir -p "$TMP/clean"
cp "$SPEC_ROOT/contexts/v1/clinical.jsonld" "$TMP/clean/"
if CONTEXTS_DIR="$TMP/clean" "$NODE" "$CHECK" >"$TMP/out1" 2>&1; then
  pass "a clean context is accepted"
else
  fail "a clean context is accepted" "$(cat "$TMP/out1")"
fi

# 2. Negative control: reintroduce the prose-valued divider. Must fail, and the
#    failure must NAME the file and the term.
mkdir -p "$TMP/prose"
"$NODE" -e "
const fs = require('fs');
const src = process.argv[1], dst = process.argv[2];
const d = JSON.parse(fs.readFileSync(src, 'utf8'));
d['@context']['__comment_core'] = '=== Core Vocabulary (cascade:) ===';
fs.writeFileSync(dst, JSON.stringify(d, null, 2));
" "$SPEC_ROOT/contexts/v1/clinical.jsonld" "$TMP/prose/clinical.jsonld"
if CONTEXTS_DIR="$TMP/prose" "$NODE" "$CHECK" >"$TMP/out2" 2>&1; then
  fail "a prose-valued term is refused" "check exited 0 on a context the processor must refuse"
else
  if grep -q "FAIL: clinical.jsonld" "$TMP/out2" && grep -q "__comment_core" "$TMP/out2"; then
    pass "a prose-valued term is refused, naming the file and the term"
  else
    fail "a prose-valued term is refused, naming the file and the term" "$(cat "$TMP/out2")"
  fi
fi

# 3. A file that is not JSON fails with the file named.
mkdir -p "$TMP/notjson"
printf '{ not json' > "$TMP/notjson/broken.jsonld"
if CONTEXTS_DIR="$TMP/notjson" "$NODE" "$CHECK" >"$TMP/out3" 2>&1; then
  fail "a non-JSON file fails" "check exited 0"
else
  if grep -q "FAIL: broken.jsonld" "$TMP/out3"; then
    pass "a non-JSON file fails, naming the file"
  else
    fail "a non-JSON file fails, naming the file" "$(cat "$TMP/out3")"
  fi
fi

# 4. Nothing to check is a hard error (exit 2), not a vacuous green.
mkdir -p "$TMP/empty"
CONTEXTS_DIR="$TMP/empty" "$NODE" "$CHECK" >"$TMP/out4" 2>&1
rc=$?
if [ "$rc" -eq 2 ]; then
  pass "an empty directory is a hard error, not a pass"
else
  fail "an empty directory is a hard error, not a pass" "exit code $rc"
fi

# 5. The repository's own published contexts are accepted. This assertion was
#    RED against the tree before the eight prose keys were removed.
if "$NODE" "$CHECK" >"$TMP/out5" 2>&1; then
  pass "every published context under contexts/v1/ is accepted"
else
  fail "every published context under contexts/v1/ is accepted" "$(cat "$TMP/out5")"
fi

echo ""
echo "$PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ]
