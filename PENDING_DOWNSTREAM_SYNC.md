# Pending downstream sync ledger

**Purpose.** A vocabulary change is *authored* in `spec/` continuously, but its
propagation to the six downstream repos (the steps 2–7 of the Vocabulary Change
Checklist in the workspace `CLAUDE.md`) is **expensive to do one change at a
time**. This ledger lets us accumulate authored-but-not-yet-propagated changes
and run the full 7-repo sync **in one batch** at a release boundary (e.g. weekly,
or when a draft vocab is promoted out of `v1-draft`).

## Why batching is safe here

1. **Shapes are open-world (not `sh:closed`).** A converter/importer can EMIT a
   new predicate and the Pod still passes `cascade validate` *before* the
   predicate is formally in the embedded shapes. So the DATA can ship as soon as
   `spec/` defines the term; the shape/docs/SDK propagation can lag.
2. **The `v1-draft` namespace is the accumulation buffer.** Draft ontologies
   (e.g. `workbench/v1-draft`) are not listed in `VOCAB_VERSIONS` and do not gate
   downstream releases. Terms accrue in draft; the 7-repo cascade fires only when
   a draft is promoted to a released `vN`.

## The seam (what must sync NOW vs what batches)

| Need | Sync immediately | Batches |
|---|---|---|
| Importer/app emits a new **draft** predicate | `spec/` (author the term) | docs site, conformance, CLI shapes, both SDKs, agent |
| A **released** vocab (`core`/`clinical`/…) gains a property | `spec/` + `cascade-cli` shapes (so `cascade validate` knows it) | docs site, conformance, both SDKs, agent |

Open-world validation means even the released-vocab case usually does not *block*
on the CLI shape sync; do it promptly only so `validate` documents the new term.

## How to run the batch

1. `cd spec && sh scripts/check-downstream-versions.sh` — see drift across repos.
2. For each ledger row below, run the per-repo steps (CLAUDE.md checklist 2–7).
3. Tag `vocab/{name}-v{X.Y}`, update each repo's `VOCAB_VERSIONS`, clear the row.

---

## Open items

### 1. `workbench:userSourceLabel` (draft) — authored, downstream pending

- **Authored:** `spec/ontologies/workbench/v1-draft/workbench.ttl` (DatatypeProperty,
  `owl:versionInfo 1.0-draft.0.4`, `dct:modified 2026-06-28`). DONE.
- **What it is:** the user's chosen filing label for a record (the editable-source
  "File under source" action), folded by the app as an annotation. Distinct from
  the imported `clinical:sourceEHR`.
- **Downstream:**
  - [ ] cascadeprotocol.org — `sync-from-spec.sh`, HTML + `cascade-protocol-schemas.md`
  - [ ] conformance — fixture exercising a re-filed record
  - [ ] cascade-cli — embedded `workbench` shapes (currently emitted via generic
        `pod annotate --property`; validates open-world, no shape change required to ship)
  - [ ] sdk-typescript / sdk-python — predicate + context
  - [ ] cascade-agent — query patterns
  - **Batchable:** yes (draft; open-world).

### 2. `clinical:sourceSystemOID` (planned) — NOT yet authored, deferred

- **Status:** DEFERRED from the 2026-06-28 source-attribution work. The Apple
  Health authoritative-`sourceName` fix (importer reads `export.xml`
  `<ClinicalRecord sourceName>`) made OID-based attribution **supplementary**, not
  load-bearing, so this was not authored this round.
- **What it would be:** carry the raw source-system OID (e.g.
  `urn:oid:1.2.840.114350.1.13.296` = an Epic customer org) alongside the friendly
  `clinical:sourceEHR`, as supplementary provenance + a stable cross-export key for
  reconciliation and the OID→org registry. `clinical:` is a RELEASED vocab (1.9),
  so authoring it bumps `clinical` to 1.10 and triggers the CLI shape sync.
- **Trigger to author:** a non-Apple import (raw FHIR / C-CDA with no Apple
  wrapper) needs OID-based attribution, OR the OID→org registry work begins.
- **Downstream when authored:** full 7-repo checklist (released vocab).

---

_Last updated: 2026-06-28._
