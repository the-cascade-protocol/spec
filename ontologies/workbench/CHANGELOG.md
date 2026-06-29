# Cascade Workbench Vocabulary — Changelog

All notable changes to the `workbench:` vocabulary. Draft status: not registered in `spec/VOCAB_VERSIONS` until v1.0 graduation (per the `genomics:` / `advisory:` draft policy).

## v1-draft.0.4 (2026-06-28)

- **Added the filing / organization axis:** `workbench:userSourceLabel` (xsd:string), the user-chosen label for the SOURCE a record is filed under in the Workbench "filing cabinet".
- It is a filing **preference attributed to the user**, carried on a `workbench:Annotation` overlay (`annotationProperty` = `"workbench:userSourceLabel"`, `annotationValue` = the chosen label) whose overlay bears `cascade:SelfReported` provenance.
- It **must not** overwrite the objective imported origin `clinical:sourceEHR`, which is preserved and displayed alongside. The effective source the UI groups by prefers this label when present, else falls back to `clinical:sourceEHR`, else the import-batch tag.
- Orthogonal axis with an **open domain**, mirroring how `workbench:verificationStatus` was added in v1-draft.0.3, so it can file any record.
- **SHACL:** no new shape required — the "file under source" action reuses the already-shaped string predicates `workbench:annotationProperty` / `workbench:annotationValue` on `workbench:Annotation`.

## v1-draft.0.1 (2026-06-16)

- Initial draft authored in `spec/` for the Cascade Workbench desktop investigation app (Layer 3).
- **Classes:** `Investigation`, `ImportedConversation`, `Hypothesis`, `Pin`, `InvestigationNote`, plus status enums.
- **Investigation status enum:** `Active`, `Paused`, `Resolved`, `Archived`.
- **Hypothesis status enum:** `Proposed`, `Supported`, `Retired`, `Excluded` (supports widening + explicitly retiring/excluding hypotheses).
- Properties linking investigations to conversations, hypotheses, pins, and notes; conversation metadata; assertion links into `evidence:`.
- **SHACL:** `InvestigationShape`, `ImportedConversationShape`.
- Deliberately thin: grounding model lives in Layer-2 `evidence:`; phenotype lives in `genomics:`.
- Rationale and design review: `cascade-assets/Cascade-documents/Cascade-Workbench/vocab-proposals/`.
