# spec/CHANGELOG.md

Top-level changelog for the Cascade Protocol vocabulary specifications. Per-vocab changelogs live in `ontologies/<vocab>/CHANGELOG.md`. This file summarizes cross-vocab milestones.

Format: each entry is one milestone, dated, with a short prose summary and pointers to the per-vocab changelogs that go with it.

---

## 2026-07-15 — workbench v1-draft.0.5 (notes / flags / follow-ups as W3C Web Annotations)

Caregiver notes, "needs research" flags, and follow-ups become ONE substrate: `oa:Annotation` over one or more graph nodes, distinguished by `oa:motivatedBy`, with required PROV-O attribution. Maximal Layer-1 reuse: span selectors from `oa:`, due date + status for follow-ups from W3C RDF Calendar (`ical:due` / `ical:status`, follow-ups dual-typed `cal:Vtodo`). Exactly one term minted: `workbench:followUp` (an `oa:Motivation`, `skos:broader oa:questioning`). `workbench:InvestigationNote` removed (draft; unshipped), superseded by the substrate. New Pod container `notes/` documented in `pod-structure.md` §5.2. SHACL Core shapes verified against `cascade validate` with positive + negative fixtures. Unblocks Workbench shell Phase 9 (notes grammar).

Tag: `vocab/workbench-v1-draft.0.5` (applied after merge). See `ontologies/workbench/CHANGELOG.md`. Downstream propagation is BATCHED per `PENDING_DOWNSTREAM_SYNC.md` (row 4) together with the outstanding v1-draft rows.

---

## 2026-05-06 — genomics v1-draft.0.3 (shape relaxations from test-fixture review)

Two SHACL shape relaxations on `genomics/v1-draft`. No vocabulary additions; shapes only.

- `genomics:geneSymbol` on `VariantShape`: Violation → Warning. The required-cardinality `sh:minCount 1` is removed; `sh:maxCount 1` stays. VRS preserve-only imports (D-Q6) and gene-less VCF records legitimately lack gene context.
- `genomics:variantInterpreted` range widened from `genomics:Variant` alone to `{Variant, CopyNumberVariant, Haplotype}` via `sh:or`. Clinical interpretations attach to all three molecular-record types (e.g., the retinoblastoma phenopacket interprets a chr13 CNV).

Tag: `vocab/genomics-v1-draft.0.3` (orchestrator-applied after merge). See `ontologies/genomics/CHANGELOG.md` for the full per-vocab entry, including the list of fixtures that become SHACL-clean post-relaxation and the deferred-to-later candidates.

Source: `cascade-coordination/tie-breaks/2026-05-06-vrs-geneSymbol-shape.md` and the Phenopacket test-fixture agent's report (variantInterpreted CNV violation).

---

## 2026-05-06 — core/v1 3.1 → 3.2 (forward-reference closure)

Small additive bump on `core/v1` to retroactively declare `cascade:appliedTriplesCount`. The Phase 4 advisory applier (cascade-cli TASK-4.5) was already emitting this property on every `cascade:AdvisoryApplicationActivity` record as a documented forward reference; this milestone closes the loop.

- `cascade:appliedTriplesCount` (DatatypeProperty, `xsd:nonNegativeInteger`, domain `cascade:AdvisoryApplicationActivity`). Records the number of triples a single advisory application inserted into the pod — auditable post-hoc verification of CAP profile constraint C5 (≤ 64 inserted triples per match).
- SHACL: Info-severity property shape on `AdvisoryApplicationActivityShape` (recommended, not required — existing activity records without the stamp remain SHACL-clean).
- VOCAB_VERSIONS: `core=3.2`. See `ontologies/core/CHANGELOG.md` for the full per-vocab entry.

Tag: `vocab/core-v3.2` (orchestrator-applied after merge).

---

## 2026-05-05 — Genomics v1-draft.0.2 evolution

Small, additive evolution pass on `genomics/v1-draft` driven by gaps surfaced in the Phase 1 FHIR Genomics IG importer (cascade-cli) and the TASK-1.9 HLA tie-break. Four high-confidence additions; nothing removed or renamed.

- **`genomics:reportedRecord`** (ObjectProperty, no `rdfs:range` — deliberately broad). Generic GeneticTest → record predicate for non-Variant report links (Diplotype, Haplotype, PGx implication, future genomics record types). Resolves the HLA tie-break: `genomics:variantsObserved` has `rdfs:range genomics:Variant` and cannot represent these without a range violation. Importers should still emit the more specific `variantsObserved` for true Variant references.
- **`genomics:refAllele`, `genomics:altAllele`, `genomics:genomicStartEnd`** (DatatypeProperty, `xsd:string`). VCF-style coordinate properties mapping LOINC 69547-8 / 69551-0 / 81254-5. Required for the Phase 3 VCF importer and for FHIR Genomics IG variants that lack HGVS but carry the LOINC components directly.
- **`genomics:somaticStatus`** ObjectProperty + **`genomics:SomaticStatus`** class with three named individuals (`Germline`, `Somatic`, `UnknownSomaticStatus`). Maps LOINC 48002-0 (Genomic source class). Critical for cancer interpretation and inheritance reasoning.
- **`genomics:variantAlleleFrequency`** (DatatypeProperty, `xsd:decimal`, SHACL-bounded 0.0–1.0). Maps LOINC 81258-6. Distinct from the existing `genomics:mosaicismFraction` — VAF is a sequencing-evidence fraction; mosaicism is the clinical conclusion that the variant is present in only a subset of cells. Phase 1 importer was shoehorning VAF into mosaicismFraction; this is the proper home.

SHACL: VariantShape gains optional property shapes for all five new Variant-domain properties (Info severity for the three string coordinates; Violation severity for the closed-enumeration `somaticStatus` and the 0.0–1.0 range on `variantAlleleFrequency`). No NodeShape added for `reportedRecord` — its domain breadth is intentional. All existing fixtures continue to pass.

Per D-PATH this is still a draft; no `VOCAB_VERSIONS` change. Tag: `vocab/genomics-v1-draft.0.2` (orchestrator-applied after merge). See `ontologies/genomics/CHANGELOG.md` for the full per-vocab entry, including the deferred-to-later candidates (CompositeVariant, multi-gene Diplotype, cytogenetic location, SNOMED reaction coding).

---

## 2026-05-05 — Genomics & Advisory v1-draft.0.1 milestone (TASK-0.5)

First draft of the Genomics & Advisory v0.1 implementation workstream lands in `spec/`:

- **`core/v1`** bumped 3.0 → 3.1 (TASK-0.0). Adds two new `prov:Activity` subclasses to support the workstream:
  - `cascade:AdvisoryApplicationActivity` — records application of a Cascade Advisory Patch to a pod, joining the advisory and the matched record via `prov:used`.
  - `cascade:AIGenerationActivity` — sibling of `cascade:AIExtractionActivity` for LLM-generated narrative content (e.g., `checkup:VariantNarrative`). Carries `cascade:promptVersion`, `cascade:generationTemperature`, and a `cascade:trigger` ObjectProperty with three `cascade:GenerationTrigger` named individuals: `InitialGeneration`, `RegenerationAfterReclassification`, `AudienceRetargeting`. A single class with a trigger property was preferred over multiple subclasses (e.g., a separate `AIRegenerationActivity`) — avoids over-modeling.
  - SHACL shapes mirror the structure: `AIGenerationActivityShape` requires `extractionModel` + `trigger`; `AdvisoryApplicationActivityShape` requires `prov:used minCount 2` (advisory IRI + matched-record IRI).
  - See `ontologies/core/CHANGELOG.md` for the full v3.1 entry.

- **`genomics/v1-draft.0.1`** authored (TASK-0.1, TASK-0.2). 220 declared `genomics:` terms across 14 classes, ~30 net-new properties versus the v0.1 design draft.
  - Layer 2 vocabulary at `https://ns.cascadeprotocol.org/genomics/v1#` with `owl:versionInfo "1.0-draft"` per D-PATH. Pre-stable drafts are NOT registered in `VOCAB_VERSIONS` (they land there at v1.0 stable graduation only).
  - Folds in all GAP-ANALYSIS additions (Haplotype, Diplotype, CopyNumberVariant, SubmitterAssertion, GeneticTestOrder, interpretationStatus + 7-value ReviewStatus enum).
  - Folds in the directory-session additions per D-DIRECTORY (SequencingRun, RawFile + 6 properties, sequencing-run metadata, dataProvenance enum).
  - Folds in the data-quality tier model per D-QUALITY-TIER (DataQualityTier class + 4 tier individuals: ClinicalGrade, ResearchGrade, ConsumerGrade, UnknownQuality; `requiresConfirmation` property on `VariantInterpretation`).
  - SHACL shapes (TASK-0.2) enforce: D-Q5 multi-condition cardinality (`condition` 1..1, `variantInterpreted` 1..1, reclassification chain via `prov:wasRevisionOf`); D-QUALITY-TIER safety constraint expressed as `sh:xone` on `VariantInterpretation` — Pathogenic/LikelyPathogenic interpretations MUST either reference a `ClinicalGrade` Variant OR carry `requiresConfirmation true`.
  - 12 `sh:NodeShape` declarations covering every concrete class.
  - See `ontologies/genomics/CHANGELOG.md`.

- **`advisory/v1-draft.0.1`** authored (TASK-0.3, TASK-0.4). 55 declared `advisory:` terms (8 classes, 16 named individuals across 3 enums, 31 properties).
  - Layer 2 vocabulary at `https://ns.cascadeprotocol.org/advisory/v1#` with `owl:versionInfo "1.0-draft"` per D-PATH.
  - Defines the Cascade Advisory Patch (CAP) envelope: `CascadeAdvisoryPatch`, `AutoApplyPolicy`, `AdvisoryClass` (six named individuals: `SafetyCritical`, `VariantReclassification`, `DrugInteraction`, `LabReferenceRangeUpdate`, `SurveillanceGuidelineUpdate`, `CarrierFrequencyUpdate`), `TrustedIssuer` per D-Q3 (per-pod, with `TrustSourceEnum` for provenance: `RecommendedStarterList`, `UserAdded`, `ImportedFromRegistry`, `VerifiedViaDID`).
  - Signing envelope per D-Q4: detached JWS Ed25519 (RFC 7515 compact serialization). Properties for `signature`, `signatureIssuer` (iss), `signatureIssuedAt` (iat), `signatureExpiresAt` (exp), `signatureContentType` (cty, fixed to `application/x-cascade-advisory-patch`).
  - Six tiered cadences: `EveryAppOpen`, `Daily`, `Weekly`, `Monthly`, `Quarterly`, `Annually`.
  - SHACL shapes (TASK-0.4) enforce: required envelope fields (humanSummary, advisoryClass, issuer, issuedAt); closed enumerations on advisoryClass/cadence/trustSource; `appliesTo` cardinality on AutoApplyPolicy; AutoApplyScope structure. Issuer-trust allowlist enforcement is OUT of SHACL scope per D-Q3 (runtime concern, lives in `<pod>/trust/issuers.ttl`).
  - 4 `sh:NodeShape` declarations.
  - See `ontologies/advisory/CHANGELOG.md`.

### Tags landed in this milestone

- `vocab/genomics-v1-draft.0.1` on `spec/main`
- `vocab/advisory-v1-draft.0.1` on `spec/main`
- `gate/0a-passed` on `cascade-coordination/main` (cross-repo gate marker)

### Workstream context

The Genomics & Advisory v0.1 implementation plan lives at `cascadeprotocol.org/drafts/05-04-26 Genomics & Advsiory IMPLEMENTATION-PLAN.md`. Decision tracker rows resolved in this milestone: D-PATH, D-Q3, D-Q4, D-Q5, D-Q6, D-N1, D-N3, D-N4, D-N5, D-N6, D-Q8, D-A, D-B, D-DIRECTORY, D-QUALITY-TIER, D-Q10. Phase -1 readiness prep complete; Gate 0a achieved with this entry.

### What's next (Gate 0b prep)

- TASK-0.6: downstream sync to `cascadeprotocol.org` (HTML docs, schemas.md update, llms-full.txt regeneration).
- TASK-0.7: conformance fixture skeletons in `conformance/fixtures/{genomics,advisory}/`.
- After both: Gate 0b sign-off, which unblocks Phase 1+ importers and SDK propagation.
