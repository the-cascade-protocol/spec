# Cascade Workbench Vocabulary — Changelog

All notable changes to the `workbench:` vocabulary. Draft status: not registered in `spec/VOCAB_VERSIONS` until v1.0 graduation (per the `genomics:` / `advisory:` draft policy).

## v1-draft.0.1 (2026-06-16)

- Initial draft authored in `spec/` for the Cascade Workbench desktop investigation app (Layer 3).
- **Classes:** `Investigation`, `ImportedConversation`, `Hypothesis`, `Pin`, `InvestigationNote`, plus status enums.
- **Investigation status enum:** `Active`, `Paused`, `Resolved`, `Archived`.
- **Hypothesis status enum:** `Proposed`, `Supported`, `Retired`, `Excluded` (supports widening + explicitly retiring/excluding hypotheses).
- Properties linking investigations to conversations, hypotheses, pins, and notes; conversation metadata; assertion links into `evidence:`.
- **SHACL:** `InvestigationShape`, `ImportedConversationShape`.
- Deliberately thin: grounding model lives in Layer-2 `evidence:`; phenotype lives in `genomics:`.
- Rationale and design review: `cascade-assets/Cascade-documents/Cascade-Workbench/vocab-proposals/`.
