# D-CANONICAL-1: Two layers: a source of record that only adds, and a canonical layer that only merges

**Status:** Proposed; direction ratified by Jed Reinitz on 2026-09-05, rulebook open for review; amended 2026-09-05 with the identity and IPS measurements (below)
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
  (`cascade:sourceIdentity`), the record class and that identifier, so two devices importing
  the same document converge without communicating and re-import is idempotent by
  construction. Where it does not, the name is derived from a digest of the raw source
  element under a canonicalisation this repository states per input format, with a declared
  exclusion list for volatile fields and the enclosing document's identifier as context (the
  amendment below records why each of those qualifications is there; the first draft of this
  sentence said only "JCS for JSON, C14N for XML", and measurement showed that rule would
  merge data). No regex, key set, comparator or terminology table participates in a name. An
  import batch label never does either. Existing content-hashed IRIs remain valid as opaque
  names; nothing is re-minted.
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
   The canonical shape for each class is written against the IPS profile that will export it
   (its must-support elements and bindings), so that a record which satisfies layer 2 is by
   construction a record IPS can carry; see the amendment for what that requires of the
   vocabularies first.
9. **The layer 1 naming rule**, stated per input format, as decisions the amendment below
   grounds: the ordered tiers, the canonicalisation, the exclusion list, the document context,
   and what happens when a source identifier is not unique within its own document.
10. **Section-level absence.** IPS states "no known allergies" as a property of a section,
    while `cascade:dataAbsentReason` is a property of an element. The canonical layer needs an
    explicit assertion for "none known, checked" per class, made by a source or a person,
    never inferred from the absence of records.
11. **The clinical/health class split.** `clinical:Condition`, `clinical:Allergy`,
    `clinical:LabResult` and `clinical:Immunization` are declared with shapes, while every pod
    serialises the `health:` record classes, so the `clinical:` four validate nothing today.
    Decide whether they become the layer 2 classes (strict shapes, untouched layer 1 data) or
    are deprecated; either is defensible, and it must be a decision rather than an accident.

## The canonical export: the International Patient Summary

The canonical layer's natural external form is the HL7 FHIR **International Patient Summary**
(IPS, https://hl7.org/fhir/uv/ips/): a document Bundle with a Composition whose sections
(problems, medications, allergies, immunizations, procedures, devices, results, and optional
others) are a minimal, condition-independent summary any conformant system can read. Each
entry carries FHIR Provenance back to its sources. This is the artefact a patient hands to a
new clinician for intake, a second opinion, or a language model that must reason over one
unambiguous record. Terminology licensing for IPS is decided by the organisation's existing
licensing policy, not here.

## Amendment 2026-09-05: what two measurements changed

Before the rulebook went to review, two read-only measurements were run against the public
inputs: the reference pod and every fixture in `conformance` (commit `07754a4`), the
reference implementation's converters and its synthetic FHIR bundles and 22 C-CDA documents
(`cascade-cli` commit `5f6c06f`), and the published IPS implementation guide (2.0.1, STU 2).
The full reports are internal working documents; every number below is reproducible from
those inputs, and the decisions rest on the numbers, not the reports.

### Why this matters

A layer 1 name is the one thing in this design that is never revised. It decides whether two
devices importing the same document converge, whether a re-import is a no-op, and what every
`prov:wasDerivedFrom` link in the canonical layer points at. A naming rule can fail in two
directions, and they are not symmetric. If it gives one source element two names across
imports, layer 2 inherits a duplicate to reconcile forever, which is expensive but visible. If
it gives two different source elements one name, the second overwrites the first at write
time and the data is gone before any reconciler sees it. That second failure violates the
first property this document exists to guarantee, and the draft rule had it in two places.
Separately, the canonical layer is only worth building if its shapes are strong enough that
what satisfies them can be exported as a conformant IPS; the mapping found gaps that no
importer can fill, so they have to be closed in the vocabularies before the first canonical
class is written.

### What the identity measurement found

| Finding | Measurement | Decision it grounds |
|---|---|---|
| Source identifiers dominate | 548 of 574 FHIR resources carry `resource.id` (95.5%); `identifier[]` never appears without it (0 of 574). 125 of 131 C-CDA clinical statements carry an `<id>`. | Tier 1 is source identity + record class + the source's own identifier. The digest is the minority path, and an `identifier[]` tier would be dead code; do not specify one. |
| Plain JCS merges FHIR decimals | 19 literals spelled `4.0`, `250.0`, `21.0` in the corpus collapse to `4`, `250`, `21` under RFC 8785 shortest-form numbers. FHIR treats that precision as significant. | JSON canonicalisation must keep number lexical forms as the source wrote them (JCS structure with numbers as source text, or a digest of the element's source bytes). |
| C14N 1.0 breaks on whitespace | Re-indenting the source moves 131 of 131 C-CDA statement digests under C14N 1.0; C14N 2.0 with `TrimTextNodes` moves 0 of 131. Neither survives a namespace-prefix rewrite (131 of 131); prefix rewriting is untested here because the tooling to hand does not expose it. | XML canonicalisation is C14N 2.0 with trimmed text nodes. Whether prefix independence is required is open: it is not, if importers always digest the bytes the source sent. |
| Context must be the document | Statement alone: 7 collision groups. Statement plus its section: the same 7. Statement plus the enclosing document identifier: 1, a genuine intra-document twin. | The digest includes the enclosing document's identifier, not the section. |
| Source ids are not always unique | In the C-CDA corpus 6 identifiers are claimed by more than one statement in the same document, and 33 statements carry a root-only id. | Tier 1 applies only when the identifier is unique within its document; otherwise the record falls to the digest tier with the identifier included. |
| Volatility dominates the digest | Bumping `meta.versionId` moves 511 of 511 raw FHIR digests; the reference implementation's existing exclusion list moves 0 of 511, at a cost of one collision. C-CDA has its own axis, the narrative anchor `<reference value="#id">` on 15 of 131 statements, and no C-CDA exclusion list exists anywhere. | The exclusion list is declared here per format (FHIR `meta.versionId`, `meta.lastUpdated`, `text`; C-CDA document `effectiveTime`, narrative anchors, generated ids), and importers implement exactly it. |
| Batch labels leak into names | 50 of 178 C-CDA records in the pod under test are named partly from the import batch label; changing the label re-mints them. | The rule says it explicitly: an ingestion label is never part of a name. |
| The reference pod cannot show layer 1 | Zero `cascade:sourceIdentity`, zero `prov:wasDerivedFrom`, 250 of 448 typed subjects are blank nodes, 176 are non-UUID `urn:uuid:` strings. Zero `prov:wasDerivedFrom` in all 163 fixtures. | Conformance regenerates the reference pod from committed inputs through the importers once the rule lands, and gains derivation fixtures before the coverage gate is claimed to work. |

One caveat is recorded rather than hidden: every C-CDA number rests on 22 synthetic
documents. The C14N and context decisions should be re-measured on a real corpus before they
are written as normative text.

### What the IPS mapping found

Against IPS 2.0.1, of the 31 registered record classes, 6 have a home in a required section
(problems, allergies, medications), 7 in a recommended section, 3 in an optional one, 1 is the
subject, and 14 have no IPS home (coverage, family history, encounters, and every wellness and
device class). IPS permits additional sections when the required ones are present, so the 14
are not dropped from a summary; they are simply not what IPS profiles. The three required
sections are reachable from `health:ConditionRecord`, `health:AllergyRecord` and
`clinical:Medication`/`clinical:Supplement`. Four gaps block a conformant export today and
none can be supplied by an importer:

- No ontology declares a patient name; `Patient.name` is 1..1 with invariant `ips-pat-1`.
- Allergies carry no coded substance and no coded manifestation; `AllergyIntolerance.code` is
  1..1 must-support, and the importer joins manifestations into one text literal.
- The only supplier of `MedicationStatement.effective[x]` (1..1 must-support) is a predicate
  the reference implementation writes and no ontology declares.
- There is no authorship model for `Composition.author` and no section-level absence model
  (rulebook item 10).

Three registered classes have no shape at all (`clinical:ImagingStudy`,
`clinical:ImplantedDevice`, `clinical:MedicationAdministration`); their shapes should be
authored from the IPS profiles that export them rather than from current writer output.

### What changes in this document

The identity section's naming sentence is qualified as above. Rulebook item 8 now ties each
canonical shape to its IPS profile, and items 9, 10 and 11 are added. Sequencing gains a
step before the naming rule: close the four vocabulary gaps, since the first canonical class
(medications) hits one of them directly.

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

The four vocabulary gaps the IPS mapping found are closed first, through the vocabulary
change process, because the first canonical class depends on one of them. Idempotency and
input-derived naming for layer 1 next, as rulebook item 9, re-measured on a real C-CDA corpus
before the text is normative; the canonical layer and its coverage gate after that, with the
regenerated reference pod and derivation fixtures landing with it; content-derived naming
removed from importers last. The IPS export is built on layer 2 as soon as one record class
(medications) has a canonical form, and grows section by section.
