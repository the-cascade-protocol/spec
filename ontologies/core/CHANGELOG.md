# Core Vocabulary Changelog

## v3.3 - 2026-06-16

Cascade Workbench support: ungrounded-AI provenance + caregiver-proxy.

- Added `cascade:AIAsserted` (`owl:Class`, subClassOf `cascade:ConsumerGenerated`):
  provenance leaf for content surfaced by a general-purpose AI assistant in a
  patient-directed conversation. Safety primitive: marks `evidence:Assertion`
  inputs as ungrounded-by-construction so they are never confused with
  `cascade:AIExtracted` clinical data.
- Added `cascade:ProxyAgent` (`owl:Class`, subClassOf `prov:Agent`) and properties
  `actsForPatient`, `proxyWebID`, `proxyRelationship`, `proxyScope`,
  `proxyGrantedAt`, `proxyRevokedAt`: caregiver-proxy actor (e.g. a parent
  operating a minor child's Pod).
- SHACL: `cascade:ProxyAgentShape` (requires actsForPatient, proxyRelationship,
  proxyGrantedAt).
- Downstream sync (cascade-cli, sdk-typescript, sdk-python, cascade-agent) pending
  per the Vocabulary Change Checklist.

## v3.2 — 2026-05-06

Forward-reference closure for the Phase 4 advisory applier.

- Added `cascade:appliedTriplesCount` (`owl:DatatypeProperty`, range
  `xsd:nonNegativeInteger`, domain `cascade:AdvisoryApplicationActivity`).
  Records the number of triples a single advisory application inserted into
  the pod, enabling post-hoc auditable verification of CAP profile constraint
  C5 (≤ 64 inserted triples per match).
- The Phase 4 applier (cascade-cli `src/lib/advisory/applier.ts`) was already
  emitting this property as a documented forward reference; v3.2 retroactively
  declares it. No applier code change is needed; existing emitted records
  become SHACL-clean (Info-severity property shape encourages but does not
  require the stamp).

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
