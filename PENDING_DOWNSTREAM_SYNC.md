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

## Done — batched sync 2026-07-15

The three v1-draft rows below were propagated in one batch (Vocabulary Change
Checklist steps 2–7). One PR per repo; every box is checked with its PR number.
Drafts stay UNROWED in `VOCAB_VERSIONS` per D-PATH (each SDK/repo added a dated
comment only), so the released-vocab drift check still reads UP TO DATE across
all repos. Tags `vocab/workbench-v1-draft.0.5`, `vocab/workbench-v1-draft.0.4`,
and `vocab/evidence-v1-draft.0.2` are applied on merge.

**Per-repo PRs (shared across the three rows):**

| Repo | PR | What synced |
|---|---|---|
| cascade-cli | the-cascade-protocol/cascade-cli#16 | embedded `evidence` + `workbench` shapes (`sync-shapes-from-spec.sh`); 992 tests green; note fixtures verified against the embedded shapes |
| cascadeprotocol.org | the-cascade-protocol/cascadeprotocol.org#2 | `evidence/v1-draft` + `workbench/v1-draft` docs (HTML + `cascade-protocol-schemas.md`), `sync-from-spec.sh` + `generate-llms.sh` draft loops, regenerated `llms-full.txt` |
| conformance | the-cascade-protocol/conformance#2 | `fixtures/evidence/` (six facet fixtures) + `fixtures/workbench/` (six note fixtures + one filing-label fixture) with INVENTORY.md; all 14 proven PASS/FAIL against the real validator |
| sdk-typescript | the-cascade-protocol/sdk-typescript#2 | `oa`/`ical`/`skos`/`workbench`/`evidence` namespaces + facet/`userSourceLabel` predicates; drafts excluded from the generated JSON-LD context; 408 tests pass |
| sdk-python | the-cascade-protocol/sdk-python#1 | same namespaces + predicates (snake + camel); VOCAB_VERSIONS draft comment; 207 tests pass |
| cascade-agent | the-cascade-protocol/cascade-agent#13 | system-prompt query patterns for the `notes/` container, evidence facets, and `userSourceLabel`; VOCAB_VERSIONS draft comment |

### 1. `workbench:userSourceLabel` (draft, v1-draft.0.4) — DONE

- **Authored:** `spec/ontologies/workbench/v1-draft/workbench.ttl` (DatatypeProperty,
  `owl:versionInfo 1.0-draft.0.4`, `dct:modified 2026-06-28`).
- **What it is:** the user's chosen filing label for a record (the editable-source
  "File under source" action), folded by the app as an annotation. Distinct from
  the imported `clinical:sourceEHR`.
- **Downstream:**
  - [x] cascadeprotocol.org — `sync-from-spec.sh`, HTML + `cascade-protocol-schemas.md` (#2)
  - [x] conformance — `filing-label-refile.VALID.ttl` re-filed-record fixture (#2)
  - [x] cascade-cli — embedded `workbench` shapes (cascade-cli#16); validates open-world, no shape change required to ship
  - [x] sdk-typescript / sdk-python — predicate registered (sdk-typescript#2 / sdk-python#1)
  - [x] cascade-agent — query pattern (#13)

### 2. `evidence:` verdict taxonomy v2 facet model (draft, v1-draft.0.2) — DONE

- **Authored:** `spec/ontologies/evidence/v1-draft/evidence.ttl` +
  `evidence.shapes.ttl` (`owl:versionInfo 1.0-draft.0.2`, `dct:modified
  2026-07-01`, tag `vocab/evidence-v1-draft.0.2`).
- **What it is:** the grounding outcome moves from the flat 4-value
  `evidence:verdict` to orthogonal facets on the Assertion
  (`evidence:direction` / `basis` / `strength` / `settled` / `reason` object
  properties over closed enumerations, `evidence:confidence` xsd:decimal).
  The facets are the canonical serialized form; the SHACL grounding invariant
  is generalized (SHACL Core). `evidence:verdict` and the `VerdictValue`
  individuals are deprecated, kept one release.
- **Code sync (already done in lockstep, not batched):**
  `cascade-workbench/packages/contracts` (invariant + migration) and
  `packages/claims` `reify()`; Workbench grounding-gate fixtures exercise the
  new shapes against the real validator.
- **Downstream:**
  - [x] cascadeprotocol.org — `sync-from-spec.sh`, HTML + `cascade-protocol-schemas.md` (#2)
  - [x] conformance — facet fixtures ported from the grounding-gate set (#2)
  - [x] cascade-cli — embedded `evidence` shapes via `sync-shapes-from-spec.sh` (cascade-cli#16)
  - [x] sdk-typescript / sdk-python — facet predicates (sdk-typescript#2 / sdk-python#1)
  - [x] cascade-agent — query patterns (#13)
- **At v1.0 graduation (do NOT batch-forget):** remove `evidence:verdict` +
  the `VerdictValue` individuals and the legacy SHACL branch; make
  `evidence:settled` `sh:minCount 1`; drop the derived legacy `Verdict` from
  `@cascade-workbench/contracts`. Also: mint the JSON-LD context for `evidence:`
  and remove the `DRAFT_CONTEXT_EXCLUDED_PREFIXES` guard in sdk-typescript.

### 3. `workbench:` notes / flags / follow-ups as Web Annotations (draft, v1-draft.0.5) — DONE

- **Authored:** `spec/ontologies/workbench/v1-draft/workbench.ttl` +
  `workbench.shapes.ttl` (`owl:versionInfo 1.0-draft.0.5`, `dct:modified
  2026-07-15`, tag `vocab/workbench-v1-draft.0.5`) + `pod-structure.md` §5.2
  `notes/` container.
- **What it is:** [NOTES-ANNOTATION-VOCAB] — caregiver notes, research flags,
  and follow-ups as ONE `oa:Annotation` substrate distinguished by
  `oa:motivatedBy`; required PROV-O attribution; follow-ups dual-typed
  `cal:Vtodo` with `ical:due` / `ical:status`. One minted term
  (`workbench:followUp`). `InvestigationNote` removed (unshipped).
- **Code sync (lockstep, not batched):** Workbench Phase 9 emits/reads these
  under `notes/`; the contracts package drops the stale `InvestigationNote`
  types in the same PR.
- **Downstream:**
  - [x] cascadeprotocol.org — `sync-from-spec.sh`, HTML + `cascade-protocol-schemas.md` (#2)
  - [x] conformance — valid commenting/questioning/followUp notes + INVALID
        followUp-without-status, commenting-without-body, floating annotation (#2)
  - [x] cascade-cli — embedded `workbench` shapes via `sync-shapes-from-spec.sh` (cascade-cli#16)
  - [x] sdk-typescript / sdk-python — `oa:`/`ical:`/`skos:` predicates + namespaces
        (`workbench:followUp` is a motivation individual, reached via the namespace;
        sdk-typescript#2 / sdk-python#1)
  - [x] cascade-agent — query patterns (`notes/` container, motivation filters) (#13)
- **JSON-LD context:** none yet (drafts get contexts at v1.0 graduation, same as
  the other draft rows; sdk-typescript explicitly excludes draft prefixes from
  the generated context until then).

---

## Open items

### 1. `clinical:sourceSystemOID` (planned) — NOT yet authored, deferred

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

_Last updated: 2026-07-15._
