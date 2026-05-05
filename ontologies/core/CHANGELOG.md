# Core Vocabulary Changelog

## v3.1 — 2026-05-05

Genomics & Advisory provenance (TASK-0.0). Two new `prov:Activity` subclasses
plus a trigger enumeration for AI generation events.

- Added `cascade:AdvisoryApplicationActivity` (`rdfs:subClassOf prov:Activity`).
  Created when a Cascade Advisory Patch is applied to a pod. Joins to
  advisory provenance via `prov:used <advisory-iri>` and
  `prov:used <matched-record-iri>`.
- Added `cascade:AIGenerationActivity` (`rdfs:subClassOf prov:Activity`).
  Sibling of `cascade:AIExtractionActivity` for LLM-generated narrative
  content (e.g., `checkup:VariantNarrative` chunks). Reuses
  `cascade:extractionModel`, `cascade:extractionConfidence`,
  `cascade:sourceNarrativeSection`, and `cascade:requiresUserReview` from
  `AIExtractionActivity`. Adds `cascade:promptVersion` and
  `cascade:generationTemperature`.
- Added `cascade:trigger` (`owl:ObjectProperty`,
  `rdfs:domain cascade:AIGenerationActivity`,
  `rdfs:range cascade:GenerationTrigger`).
- Added `cascade:GenerationTrigger` class with three named individuals:
  `cascade:InitialGeneration`, `cascade:RegenerationAfterReclassification`,
  `cascade:AudienceRetargeting`.
- Added SHACL shapes `cascade:AIGenerationActivityShape` and
  `cascade:AdvisoryApplicationActivityShape`.

Design note: a single `AIGenerationActivity` class with a `trigger` property
was chosen over multiple subclasses (e.g., a separate
`AIRegenerationActivity`). One class is enough.
