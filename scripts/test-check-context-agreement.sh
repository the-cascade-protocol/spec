#!/bin/sh
# test-check-context-agreement.sh
#
# Regression suite for check-context-agreement.py.
#
# The defect under test: a published JSON-LD context is a dictionary from JSON
# keys to IRIs, and nothing until now compared it against the ontologies and
# shapes it claims to describe. A context can therefore name a predicate no
# vocabulary declares, drop the @type on a date whose range is xsd:dateTime (so
# every consumer writes an untyped string), publish an enumerated value as
# "@type": "@id" (so a bare token resolves against the DOCUMENT BASE and means
# something different for every consumer), or offer an array on a path the
# shapes constrain to one value. All four are present in the contexts as
# published and were found by hand, one issue at a time.
#
# Every assertion is paired with a negative control that REINTRODUCES the defect
# into a scratch copy of contexts/v1 and requires a failure NAMING the term and
# the finding class. The baseline is tested in both directions: an unlisted
# finding must fail, and a baselined finding that has been FIXED must also fail,
# so the file can only shrink by a deliberate edit. The two ways this check
# could go vacuous -- no contexts to read, no ontologies to read it against --
# are required to be hard errors rather than green.
#
# No file under contexts/ or ontologies/ is modified: every case runs against a
# copy in a temp directory, with the check pointed at it by CONTEXTS_DIR.
#
# Usage: ./scripts/test-check-context-agreement.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK="$SCRIPT_DIR/check-context-agreement.py"
BASE="scripts/known-context-disagreements.json"
PYTHON="${PYTHON:-python3}"

PASSED=0
FAILED=0

pass() { PASSED=$((PASSED + 1)); echo "  PASS  $1"; }
fail() { FAILED=$((FAILED + 1)); echo "  FAIL  $1"; echo "        $2"; }

# A missing parser is a hard failure, never a skip: skipping the suite because
# a dependency is absent reports green while testing nothing.
if ! "$PYTHON" -c "import rdflib" 2>/dev/null; then
  echo "ERROR: $PYTHON cannot import rdflib, so this suite would test nothing."
  echo "       Install it:  $PYTHON -m pip install -r scripts/requirements.txt"
  exit 2
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# A scratch copy of the contexts directory and the baseline, free to mutate.
scratch() {
  dir="$WORK/$1"
  mkdir -p "$dir"
  cp -R "$SPEC_ROOT/contexts/v1" "$dir/contexts"
  cp "$SPEC_ROOT/$BASE" "$dir/baseline.json"
  echo "$dir"
}

# edit <dir> <context file> <python statements operating on the dict `c`>
edit() {
  "$PYTHON" - "$1/contexts/$2" <<PYEOF
import json, sys
path = sys.argv[1]
with open(path) as handle:
    doc = json.load(handle)
c = doc["@context"]
$3
with open(path, "w") as handle:
    json.dump(doc, handle, indent=2)
PYEOF
}

# baseline_add <dir> <key>  -- list a finding in the scratch baseline that the
# contexts as published no longer produce, i.e. a disagreement already fixed.
baseline_add() {
  "$PYTHON" - "$1/baseline.json" "$2" <<PYEOF
import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path) as handle:
    doc = json.load(handle)
doc["entries"][key] = "fabricated by the regression suite; the context no longer disagrees"
with open(path, "w") as handle:
    json.dump(doc, handle, indent=2)
PYEOF
}

# run <dir>  -> output on stdout, exit status in $STATUS
run() {
  OUT="$(CONTEXTS_DIR="$1/contexts" CONTEXT_AGREEMENT_BASELINE="$1/baseline.json" \
        "$PYTHON" "$CHECK" "$SPEC_ROOT" 2>&1)"
  STATUS=$?
}

# expect_finding <label> <dir> <term> <finding class>
expect_finding() {
  run "$2"
  if [ $STATUS -eq 0 ]; then
    fail "$1" "check PASSED; it should have reported $3 [$4]"
    return
  fi
  if echo "$OUT" | grep -q "$3:$4"; then
    pass "$1"
  else
    fail "$1" "failed, but did not name $3:$4 -- $(echo "$OUT" | tail -20)"
  fi
}

echo ""
echo "=========================================================="
echo "  check-context-agreement.py regression suite"
echo "  spec root: $SPEC_ROOT"
echo "=========================================================="

# ---------------------------------------------------------------------------
echo ""
echo "1. Positive control: the repository as committed must pass"

DIR="$(scratch positive)"
run "$DIR"
if [ $STATUS -eq 0 ]; then
  pass "contexts as published agree with the ontologies, modulo the baseline"
else
  fail "contexts as published pass with the committed baseline" "$OUT"
fi

# ---------------------------------------------------------------------------
echo ""
echo "2. Negative control: a term naming a property no vocabulary declares"

DIR="$(scratch undeclared)"
edit "$DIR" health.jsonld 'c["phantomReading"] = "health:phantomReading"'
expect_finding "an undeclared @id is reported by term and class" \
  "$DIR" phantomReading undeclared-term

# ---------------------------------------------------------------------------
echo ""
echo "3. Negative control: a bare term whose range is xsd:dateTime"

DIR="$(scratch bare-date)"
edit "$DIR" clinical.jsonld 'c["performedDate"] = "clinical:performedDate"'
expect_finding "a date term stripped of its @type is reported" \
  "$DIR" performedDate missing-datatype

# ---------------------------------------------------------------------------
echo ""
echo "4. Negative control: a term whose @type contradicts the declared range"

DIR="$(scratch wrong-type)"
edit "$DIR" clinical.jsonld \
  'c["performedDate"] = {"@id": "clinical:performedDate", "@type": "xsd:string"}'
expect_finding "an @type disagreeing with rdfs:range is reported" \
  "$DIR" performedDate datatype-mismatch

# ---------------------------------------------------------------------------
echo ""
echo "5. Negative control: @set on a path the shapes cap at sh:maxCount 1"

DIR="$(scratch container)"
edit "$DIR" clinical.jsonld \
  'c["rxNormCode"] = {"@id": "clinical:rxNormCode", "@container": "@set"}'
expect_finding "a container on a maxCount-1 path is reported" \
  "$DIR" rxNormCode container-vs-cardinality

# ---------------------------------------------------------------------------
echo ""
echo "6. Negative control: an enumerated range published as \"@type\": \"@id\""

DIR="$(scratch enumeration)"
edit "$DIR" core.jsonld \
  'c["provenance"] = {"@id": "cascade:dataProvenance", "@type": "@id"}'
expect_finding "an enumeration term typed @id is reported" \
  "$DIR" provenance enumeration-not-vocab

# ---------------------------------------------------------------------------
echo ""
echo "7. Negative control: a structured range with neither class nor scope"

DIR="$(scratch structured)"
edit "$DIR" core.jsonld \
  'c["homeAddress"] = {"@id": "cascade:address", "@type": "@id"}'
expect_finding "a structured term with no class and no scoped @context is reported" \
  "$DIR" homeAddress structured-term-unscoped

# ---------------------------------------------------------------------------
echo ""
echo "8. Negative control: a term borrowed from another Cascade vocabulary"

DIR="$(scratch foreign)"
edit "$DIR" pots.jsonld 'c["clinical"] = "https://ns.cascadeprotocol.org/clinical/v1#"; c["clinicalNotes"] = "clinical:notes"'
expect_finding "a foreign-vocabulary term is reported" \
  "$DIR" clinicalNotes foreign-vocabulary-term

# ---------------------------------------------------------------------------
echo ""
echo "9. Negative control: a term in a namespace on no allow-list"

DIR="$(scratch unknown-ns)"
edit "$DIR" pots.jsonld 'c["inventedTerm"] = "http://example.org/invented#thing"'
expect_finding "a term outside every known namespace is reported" \
  "$DIR" inventedTerm unknown-namespace

# ---------------------------------------------------------------------------
echo ""
echo "10. Baseline, other direction: a FIXED disagreement must fail as stale"

# health:performedDate carries its xsd:dateTime in the published context, so
# listing it as a missing-datatype finding describes a disagreement that has
# been fixed. The case is written this way rather than by repairing a still
# baselined term so that fixing any further term cannot make it vacuous.
DIR="$(scratch stale)"
baseline_add "$DIR" "health.jsonld:performedDate:missing-datatype"
run "$DIR"
if [ $STATUS -eq 0 ]; then
  fail "a fixed baseline entry fails as stale" \
    "check PASSED; the baseline still lists health.jsonld:performedDate:missing-datatype"
elif echo "$OUT" | grep -q "no longer occur" &&
     echo "$OUT" | grep -q "health.jsonld:performedDate:missing-datatype"; then
  pass "a fixed baseline entry fails as stale, naming the entry"
else
  fail "a fixed baseline entry fails as stale" "$(echo "$OUT" | tail -20)"
fi

# ---------------------------------------------------------------------------
echo ""
echo "11. The 1.1 form clears the finding: a scoped structured term goes stale"

DIR="$(scratch scoped)"
edit "$DIR" core.jsonld \
  'c["address"] = {"@id": "cascade:address", "@type": "cascade:Address", "@context": {"street": "cascade:street"}}'
run "$DIR"
if echo "$OUT" | grep -q "core.jsonld:address:structured-term-unscoped"; then
  pass "a term given its class and a scoped @context stops being a finding"
else
  fail "a term given its class and a scoped @context stops being a finding" \
    "the entry was not reported stale, so the scoped form was not recognised: $(echo "$OUT" | tail -20)"
fi

# ---------------------------------------------------------------------------
echo ""
echo "12. Hard-error control: an empty contexts directory must not pass"

DIR="$WORK/empty"
mkdir -p "$DIR/contexts"
cp "$SPEC_ROOT/$BASE" "$DIR/baseline.json"
run "$DIR"
if [ $STATUS -eq 2 ]; then
  pass "an empty contexts directory is exit 2, not a green run"
else
  fail "an empty contexts directory is exit 2" "exit $STATUS: $OUT"
fi

# ---------------------------------------------------------------------------
echo ""
echo "13. Hard-error control: a root with no ontologies must not pass"

DIR="$(scratch no-ontologies)"
OUT="$(CONTEXTS_DIR="$DIR/contexts" CONTEXT_AGREEMENT_BASELINE="$DIR/baseline.json" \
      "$PYTHON" "$CHECK" "$WORK/empty" 2>&1)"
STATUS=$?
if [ $STATUS -eq 2 ]; then
  pass "a root with no ontologies is exit 2, not a green run"
else
  fail "a root with no ontologies is exit 2" "exit $STATUS: $OUT"
fi

# ---------------------------------------------------------------------------
echo ""
echo "14. Hard-error control: a missing baseline must not pass"

DIR="$(scratch no-baseline)"
rm -f "$DIR/baseline.json"
run "$DIR"
if [ $STATUS -eq 2 ]; then
  pass "a missing baseline is exit 2, not a green run"
else
  fail "a missing baseline is exit 2" "exit $STATUS: $OUT"
fi

# ---------------------------------------------------------------------------
echo ""
echo "=========================================================="
echo "  passed:  $PASSED"
echo "  failed:  $FAILED"
echo "  total:   $((PASSED + FAILED))"
echo "=========================================================="
echo ""

[ "$FAILED" -eq 0 ] || exit 1
exit 0
