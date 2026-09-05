# D-CANONICAL-1: Two layers: a source of record that only adds, and a canonical layer that only merges

**Status:** Proposed; direction ratified by Jed Reinitz on 2026-09-05, rulebook open for review
**Date:** 2026-09-05
**Proposed by:** Jed Reinitz
**Prompted by:** the-cascade-protocol/spec#38 (identity is a derived value used as the record's
name; should it be?), which argues correctly that a content-derived hash should not name a
record, and stops one layer short of where that argument leads. It is also the generalisation
of a ruling made in the Workbench on 2026-08-18 for condition summaries, which this document
revises in one respect (below).

---

## The goal, stated as two properties

A patient's record must **never drop data**, and it must present a **clean, unambiguous view of
the truth**. These are properties of two different things. The first is a property of what is
stored. The second is a property of what is shown. One mechanism cannot deliver both at write
time; content-derived naming tried, and every control the reference implementation has grown
since exists to catch it being wrong.

## Why: the product case

Medical records today fail patients in a specific way. Every provider adds; nobody merges. A
patient carries several versions of one medication list across several portals with no way to
say which is current, and the conservative instinct, add and never merge or delete, is what
makes the problem grow. Two scenarios define what a pod has to be instead.

**A model reasoning over the record.** A patient or caregiver attaches their complete record to
a language-model call and asks a real question. The model needs every clinical fact stated
once, one value per fact or an explicitly labeled disagreement, a citation from each fact to
its sources, identifiers stable enough that the citations resolve, a date the record is true
as of, and a size that fits a context window. Three records for one drug is not more
information to a model; it is a question it will answer wrong.

**A reconciled summary the patient can hand to anyone.** Nobody today can give a patient one
reconciled summary of their own record across every provider they have seen. The HL7 FHIR
International Patient Summary is the ratified artefact for exactly that, usable for intake at
a new clinician, a second opinion, or the model above. A pod that emits a correct IPS with
provenance on every entry is a product in its own right.

Both scenarios need the same thing: a clean view that exists once, in the pod, and is the same
through every door. If the clean view were computed by each application, every patient-facing
app would derive its own truth, they would disagree, and the protocol would offer developers
nothing they could not get from a folder of FHIR files. Storing the canonical layer in the pod
is what makes the protocol worth building on: an application reads one reconciled record and
spends its effort on the patient, not on reconciliation. The price is that this specification
must be strong enough to carry that weight, which is why the rulebook below is part of the
decision and not left to implementations.

## The decision (proposed)

A pod holds two layers.

**Layer 1, the source of record, only adds.** Every record as it arrived, from every source,
including the patient. Append-only. Nothing in it is ever edited or merged. It is open-world
(D-OPENWORLD-1): a write is never refused and never destroys. Physical duplicates are allowed
and are removed by lossless background compaction with set semantics, never on the write path.

**Layer 2, the canonical layer, only merges.** One record per real thing: one medication, one
allergy, one problem, one immunization. Each canonical record links to every source record it
was derived from (`prov:wasDerivedFrom`), carries a status, and states one value per field or
an explicit, visible disagreement. It is the default view in every application, the input to
every export, and the thing a patient hands to a clinician or a model. It is strict where
layer 1 is open: its shapes may require one value per field, closed value sets and provenance.

**Coverage between them is total, by construction.** Every layer 1 record is linked to a
canonical record, or excluded with a stated reason, or flagged pending. That is checked by a
gate that walks layer 1 independently; it is never assumed. A canonical layer that silently
omits a source record has failed at the one thing layer 1 exists to guarantee.

## Identity, resolved by the split

- **A layer 1 record is named from its input, never from its meaning.** Where the source
  supplies an identifier, the name is derived deterministically from the source system
  (`cascade:sourceIdentity`) and that identifier, so two devices importing the same document
  converge without communicating and re-import is idempotent by construction. Where it does
  not, the name is derived from a digest of the raw source element under a standard
  canonicalisation (JCS for JSON, C14N for XML). No regex, key set, comparator or terminology
  table participates in a name. Existing content-hashed IRIs remain valid as opaque names;
  nothing is re-minted.
- **A canonical record's identifier is minted once and kept for life.** When the reconciler
  changes its mind, it remaps sources to canonical records; it does not replace a canonical
  identifier. Annotations, consent scope and human resolutions attach to canonical records and
  are inherited by their sources, which is why those identifiers must be stable.
- **Sameness is the reconciler's judgement**, made with records side by side, recorded as
  links that can be retracted, driven by key fields declared once in this repository rather
  than in each implementation. The hash of extracted meaning survives as a reconciler
  heuristic and as a rebuildable index. It is no longer a name.

## The rulebook the canonical layer needs (open, to be settled before ratification)

1. **Creation, merge, split, retire.** When a canonical record is created from a new source;
   when two canonical records are found to be one; when one is found to be two; how a retired
   record is marked and why it never disappears.
2. **Disagreement.** A conflict between sources is never resolved silently and never shown as
   two records: one canonical record, both values, an explicit unresolved flag, until a rule or
   a person resolves it.
3. **Precedence.** Who wins when the patient and a clinical source disagree. Proposed: an
   explicit patient correction wins the canonical view and is marked as such; the clinical
   source is retained unchanged in layer 1.
4. **The patient is a source.** An edit in an application is a patient-authored layer 1 record
   with patient-reported provenance plus a canonical update, never an edit of layer 1.
5. **Human resolutions are durable.** A recorded human decision outranks any re-derivation. A
   rule change or re-import may surface a new conflict; it may not silently override a
   resolution.
6. **Delete means retire; erase is separate.** Retirement keeps sources. Erasure for a legal
   obligation is an explicit layer 1 operation that leaves a tombstone in the journal and
   removes the record from every canonical derivation.
7. **As-of.** The canonical layer is versioned through the existing amend and retract
   overlays, so "the record as of a date" is answerable.
8. **Key declarations.** Which fields identify a real thing per class, declared here
   (`owl:hasKey` with a stated caveat, or a `cascade:` term), consumed by every reconciler.

## The canonical export: the International Patient Summary

The canonical layer's natural external form is the HL7 FHIR **International Patient Summary**
(IPS, https://hl7.org/fhir/uv/ips/): a document Bundle with a Composition whose sections
(problems, medications, allergies, immunizations, procedures, devices, results, and optional
others) are a minimal, condition-independent summary any conformant system can read. Each
entry carries FHIR Provenance back to its sources. This is the artefact a patient hands to a
new clinician for intake, a second opinion, or a language model that must reason over one
unambiguous record. Terminology licensing for IPS is decided by the organisation's existing
licensing policy, not here.

## What this revises

The 2026-08-18 Workbench ruling for condition summaries said: the pod stays raw, the derivation
lives in the application, and is promoted to a cli projection once stable, anchored on the IPS
Problem List section with `prov:wasDerivedFrom` receipts to every folded record. That ruling
was the first instance of the canonical layer, and it was right about anchoring on IPS and
about provenance receipts. This document revises its first clause: the canonical layer lives
**in the pod**, as layer 2, so that every reader sees the same clean view without an engine
and so that consent, annotations and human resolutions have a stable home. The application's
derivation becomes the first reconciler feeding layer 2, not a private view over layer 1.

## Consequences

- D-LAYERS-1's layer C gains the canonical-layer rulebook and loses the requirement that
  implementations agree byte for byte on an identity string.
- Conformance gains fixtures for layer 2 (canonical shapes, coverage, disagreement) and vectors
  for input-derived names; the existing identity vectors remain valid for the index and for
  every pod already written.
- The reference implementation's reconciler, user-resolution records and layer-promotion
  vocabulary are the starting material; none is thrown away.
- spec#38's question 4 (the FHIR medication path putting `resource.id` first) is held until
  this decision lands, because it would re-mint identifiers under a naming rule this document
  retires.

## Sequencing

Idempotency and input-derived naming for layer 1 first; the canonical layer and its coverage
gate second; content-derived naming removed from importers last. The IPS export is built on
layer 2 as soon as one record class (medications) has a canonical form, and grows section by
section.
