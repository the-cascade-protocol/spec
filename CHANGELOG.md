# spec/CHANGELOG.md

Top-level changelog for the Cascade Protocol vocabulary specifications. Per-vocab changelogs live in `ontologies/<vocab>/CHANGELOG.md`. This file summarizes cross-vocab milestones.

Format: each entry is one milestone, dated, with a short prose summary and pointers to the per-vocab changelogs that go with it.

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
