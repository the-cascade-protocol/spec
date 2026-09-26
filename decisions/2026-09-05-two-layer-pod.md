# D-CANONICAL-1: Two layers: a source of record that only adds, and a canonical layer that only merges

**Status:** Ratified by Jed Reinitz on 2026-09-26, every rulebook item ruled; direction ratified 2026-09-05; amended 2026-09-05 with the identity and IPS measurements, 2026-09-09 with the rulings from the spec#38 review, and 2026-09-26 with the rulings on rulebook items 10 and 11 and on item 9, the layer 1 naming rule (all below)
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

## The decision

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
- **A canonical record's identifier names one build of the canonical layer, and nothing
  durable references it.** (Amended 2026-09-09; the first draft said "minted once and kept for
  life".) Annotations, consent scope and human resolutions attach to layer 1 records, which
  never change, and a canonical record is found again through any of its members. When the
  reconciler changes its mind, the next build emits different rows; no identifier has to
  survive a merge or a split, and no redirect table is needed. An identifier that must leave
  the pod is a different thing, minted by a recorded publication event (below).
- **Sameness is the reconciler's judgement**, made with records side by side, recorded as
  links that can be retracted, driven by key fields declared once in this repository rather
  than in each implementation. The hash of extracted meaning survives as a reconciler
  heuristic and as a rebuildable index. It is no longer a name.

## The rulebook the canonical layer needs (each item ruled)

1. **Creation, merge, split, retire.** When a canonical record is created from a new source;
   when two canonical records are found to be one; when one is found to be two; how a retired
   record is marked and why it never disappears. Amended 2026-09-09: canonical records are
   rows of a rebuildable derivation, so creation, merge and split are whatever the next build
   emits from layer 1 and the judgements, and retirement is a status computed from sources.
2. **Disagreement.** A conflict between sources is never resolved silently and never shown as
   two records: one canonical record, both values, an explicit unresolved flag, until a rule or
   a person resolves it.
3. **Precedence.** Who wins when the patient and a clinical source disagree. Proposed: an
   explicit patient correction wins the canonical view and is marked as such; the clinical
   source is retained unchanged in layer 1. Amended 2026-09-09: precedence is declared per
   class, beside the key declarations, because the right answer for a stopped medication
   (the patient's statement wins the view) is not the right answer for a clinician-confirmed
   allergy (stays in the view with the patient's statement attached); and whether a patient
   may make a sameness judgement outright, or only propose one for a clinician to confirm, is
   part of that per-class declaration.
4. **The patient is a source.** An edit in an application is a patient-authored layer 1 record
   with patient-reported provenance plus a canonical update, never an edit of layer 1.
   Amended 2026-09-09: this extends from edits to decisions. A match, a value choice, a
   correction and a withdrawal are each a layer 1 record, authored by a person through an
   application at a time, naming the source records and values it is about, never a canonical
   row or a conflict entry, so a rebuild cannot orphan it. Withdrawing a judgement is another
   record citing the first, not a deletion.
5. **Human resolutions are durable.** A recorded human decision outranks any re-derivation. A
   rule change or re-import may surface a new conflict; it may not silently override a
   resolution. Amended 2026-09-09: the reconciler's own confident merges are also recorded in
   layer 1, as machine-authored judgement records with software-agent provenance and the
   build's input versions, ranked below every human judgement. That is what lets a person ask
   "what merged these, when, and under which rule", and undo it with one record.
6. **Delete means retire; erase is separate.** Retirement keeps sources. Erasure for a legal
   obligation is an explicit layer 1 operation that leaves a tombstone in the journal and
   removes the record from every canonical derivation.
7. **As-of.** The canonical layer is versioned through the existing amend and retract
   overlays, so "the record as of a date" is answerable.
8. **Key declarations.** Which fields identify a real thing per class, declared here as a
   `cascade:` term listing the key fields with a normalisation per field, consumed by every
   reconciler. Amended 2026-09-09: not `owl:hasKey` on a layer 1 class. In OWL 2 a key is an
   entailment of sameness, not a constraint: any tool honouring the semantics would conclude
   that two source records with equal key values are one individual, by inference, with no
   judgement and no trail, which is the merge this decision exists to prevent; it also
   compares literals exactly and fires only on named individuals.
   The canonical shape for each class is written against the IPS profile that will export it
   (its must-support elements and bindings), so that a record which satisfies layer 2 is by
   construction a record IPS can carry; see the amendment for what that requires of the
   vocabularies first.
9. **The layer 1 naming rule**, stated per input format, as decisions the amendment below
   grounds: the ordered tiers, the canonicalisation, the exclusion list, the document context,
   and what happens when a source identifier is not unique within its own document.
   Ruled 2026-09-26 (amendment on item 9, at the end).
10. **Section-level absence.** IPS states "no known allergies" as a property of a section,
    while `cascade:dataAbsentReason` is a property of an element. The canonical layer needs an
    explicit assertion for "none known, checked" per class, made by a source or a person,
    never inferred from the absence of records. Ruled 2026-09-26 (amendment of that date).
11. **The clinical/health class split.** `clinical:Condition`, `clinical:Allergy`,
    `clinical:LabResult` and `clinical:Immunization` are declared with shapes, while every pod
    serialises the `health:` record classes, so the `clinical:` four validate nothing today.
    Decide whether they become the layer 2 classes (strict shapes, untouched layer 1 data) or
    are deprecated; either is defensible, and it must be a decision rather than an accident.
    Ruled 2026-09-26: deprecated (amendment of that date).

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

## Amendment 2026-09-09: what the spec#38 review changed

The review of this document on spec#38 (comment of 2026-09-05) accepted the two layers and
the layer 1 naming rule, and put one test to the canonical layer: delete it, rebuild it, and
nothing may be lost. Everything the pod cannot regenerate has to live in layer 1, and nothing
durable may depend on anything that lives only in layer 2. The document as first written
failed that test in one sentence, "identifiers minted once and kept for life", and in one
inheritance rule, consent attached to canonical records and inherited by their sources. The
maintainer accepted the test and the six changes that follow from it. They are rulings; the
text above is amended in place where a sentence changed, and this section records the whole.

1. **Canonical identifiers are build-scoped.** A canonical record's identifier names one
   build; nothing durable inside the pod references it; a handle to a canonical record is any
   member's layer 1 name, re-resolved against the current build. Merge and split need no
   survivor rule because nothing is attached to the row.
2. **Judgements are layer 1 records.** Every sameness judgement, value choice, correction and
   withdrawal, human or machine, is an append-only layer 1 record naming source records and
   values, with its author, instrument, time and (for machine judgements) the build's input
   versions. Rulebook items 4 and 5 are amended accordingly.
3. **Consent never widens on a rebuild.** Consent scope attaches to layer 1 records, to
   classes, or to codes, never to a canonical grouping, and a record nothing has classified is
   undecided rather than inherited. A rebuild that regroups records must not change what is
   shared. This is a constraint on the consent architecture decision of 2026-09-01.
4. **Key declarations are a `cascade:` term, not `owl:hasKey`** on a layer 1 class, for the
   reason recorded at rulebook item 8. Normalisation per key field is written in SPARQL
   `REPLACE` syntax so the regular-expression dialect is pinned by the standard (XPath 2.0
   functions) rather than by each implementation's host library; Unicode normalisation of
   layer 1 text is stated at import or declared as a gap, since SPARQL has none.
5. **No generated identifier leaves the pod by default.** Where one must, it is minted by a
   **publication event**, a layer 1 record stating that on this date, under these input
   versions and these judgements, this recipient was told these source records were one
   thing, called X. X always resolves to what was said, to whom, when and on what basis; a
   later record withdraws it. A merge is published only when confirmed by a human judgement or
   by a key match on source-supplied codes; a normaliser's or a table's merge exports as two
   entries or as one that states the disagreement. No export drops a value the pod may share,
   or its sources. For the IPS this means the Bundle identifier and each entry's identifier are
   minted by the export's publication event, which is the same record spec#47 asks
   `cascade:ExportManifest` to carry as `dct:identifier`; an IPS export is a recorded
   publication, not a property of the canonical rows.
6. **The derivation is published as data.** Layer 2 is defined as the triples that published
   SPARQL `CONSTRUCT` queries emit, run to a fixpoint, over four versioned inputs: layer 1
   source records, layer 1 judgements, the queries themselves, and reference data (brand to
   ingredient, code crosswalks) whose shape and location this repository publishes and whose
   contents are versioned separately with a digest. Every build is stamped with its four input
   versions. Conformance gains vectors of the form "this layer 1 plus these judgements at these
   versions yields exactly this layer 2", so an implementation on any platform either produces
   those triples or does not. Storing layer 2 in the pod stands, for cost and for readers with
   no engine; what changes is that a stored layer 2 is a cache of a specified derivation, and a
   reader that rebuilds it must get the same triples.

Two things the review raised are recorded as open rather than decided: which platforms can
run the queries locally (a SPARQL engine on iOS is a concrete requirement for the SDK-layers
decision's open engine question), and the cases, if any, in which a recipient outside the pod
genuinely needs identifier continuity across exports beyond what source identifiers give.
Each such case is decided per use case before anything is minted, never by default.

## What this revises

The 2026-08-18 Workbench ruling for condition summaries said: the pod stays raw, the derivation
lives in the application, and is promoted to a cli projection once stable, anchored on the IPS
Problem List section with `prov:wasDerivedFrom` receipts to every folded record. That ruling
was the first instance of the canonical layer, and it was right about anchoring on IPS and
about provenance receipts. This document revises its first clause: the canonical layer lives
**in the pod**, as layer 2, so that every reader sees the same clean view without an engine
and so that consent, annotations and human resolutions have a stable home. The application's
derivation becomes the first reconciler feeding layer 2, not a private view over layer 1.

The 2026-09-09 amendment revises this document's own first draft in two places: canonical
identifiers are no longer "minted once and kept for life" but scoped to a build, and consent,
annotations and human resolutions attach to layer 1 records rather than to canonical records.
"Every reader sees the same clean view" now rests on a specified derivation with version
stamps rather than on the stored rows alone.

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
(medications) has a canonical form, and grows section by section. Amended 2026-09-09: the
key and precedence declarations, the judgement record shapes and the published queries come
before any materialised layer 2, since the canonical view exists as soon as the queries do and
materialisation is worth building when the performance case needs proving; the first
conformance vectors for layer 2 are written against the queries, not against an
implementation's output.

## Amendment 2026-09-26: rulebook items 10 and 11 ruled

The maintainer ruled rulebook items 10 and 11 on 2026-09-26. Item 9 stays open until the
C-CDA re-measurement the 2026-09-05 amendment calls for has been run, so this document stays
Proposed. The rulings are recorded here; the item text above is unchanged apart from a pointer.

### Item 10: section-level absence

1. **"None known, checked" is an explicit record.** It is a record of the class the IPS section
   holds (an allergy, a medication, a problem, a procedure, an immunization, a device) coded
   with an absence concept. A source or a person authors it, with the provenance every record
   carries. It is never inferred from missing records: a pod with no allergy records says
   nothing about allergies.
2. **No new Cascade vocabulary for the assertion.** The assertion is a code value on a record
   class that already exists. Element-level absence stays on `cascade:dataAbsentReason`.
3. **Written as SNOMED CT, following IPS 2.0.1.** IPS 2.0.1 (STU 2, "Empty Sections and
   Missing Data", and each section's value set) removed the HL7 code system earlier versions
   used and recommends SNOMED CT concepts, each included in the section's primary code value
   set, plus one concept for an explicit "no information available" statement. A producer
   writes these, and an IPS export carries them:

   | Section | None known | No information available |
   |---|---|---|
   | Allergies | 716186003 No known allergy (narrower: 409137002 No known drug allergy, 428607008 No known environmental allergy, 429625007 No known food allergy) | 1287211007 No information available |
   | Medications | 787481004 No known medications | 1287211007 |
   | Problems | 160245001 No current problems or disability | 1287211007 |
   | Procedures | 787480003 No known procedures | 1287211007 |
   | Immunizations | 787482006 No known immunizations | 1287211007 |
   | Devices | 787483001 No known device use | 1287211007 |

   Every concept above is in the SNOMED CT International Edition. Only a "none known" concept
   states "none known, checked"; 1287211007 states that nothing is known either way. It sits
   outside the section value sets, which IPS 2.0.1 binds as preferred, so it remains valid in
   an export.
4. **Readers accept the retired HL7 codes too.** Documents written against IPS 1.1.0 (STU 1)
   use `http://hl7.org/fhir/uv/ips/CodeSystem/absent-unknown-uv-ips`, and a reader accepts
   those codes on import so older documents stay readable. An importer normalises them with
   the IPS 1.1.0 ConceptMap `http://hl7.org/fhir/uv/ips/ConceptMap/absence-to-snomed-uv-ips`:
   `no-known-allergies` to 716186003, `no-known-medication-allergies` to 409137002,
   `no-known-environmental-allergies` to 428607008 and `no-known-food-allergies` to 429625007
   (equivalent); `no-known-medications` to 787481004, `no-known-problems` to 160245001,
   `no-known-procedures` to 787480003, `no-known-immunizations` to 787482006 and
   `no-known-devices` to 787483001 (the SNOMED CT concept is narrower). The six `no-*-info`
   codes are unmatched in that map; their IPS 2.0.1 counterpart is 1287211007. Normalising
   adds the SNOMED CT code beside the source's; the layer 1 record keeps what the source said.
5. **Export of an empty required section.** A required section (allergies, problems,
   medications) with neither records nor an absence record is exported with the
   `Composition.section.emptyReason` IPS requires (`ips-comp-1`), and never as `nilknown`,
   since that would be the inference point 1 forbids.
6. **Display.** An application that shows an absence record always shows who asserted it and
   when. "No known allergies", stated years ago or by a source that never asked, misleads if
   it reads as current.
7. **Licensing.** The SNOMED CT concept identifiers and display terms above are shared under
   the SNOMED CT Global Patient Set (CC BY-ND 4.0), which publishes every International
   Edition identifier and its preferred term, so a pod or an export may carry them. The
   repository README carries the attribution: SNOMED CT concept identifiers and terms are from
   the SNOMED CT International Edition, included under the SNOMED CT Global Patient Set,
   Creative Commons Attribution-NoDerivatives 4.0, from SNOMED International.
8. **What follows, in a later vocabulary release.** Each class that can carry the assertion
   gets a shape (a code from the table above or its HL7 predecessor, author and time
   required, since the display depends on them) and a valid and an invalid conformance
   fixture. Which property carries the code is settled with each shape:
   `health:ConditionRecord` has `health:snomedCode`, `clinical:Medication` and
   `clinical:Procedure` have `clinical:snomedCode`, `health:AllergyRecord` has
   `health:allergenCode` and `health:ImmunizationRecord` has `health:vaccineCode`; a class with
   no property able to carry the code is a vocabulary gap, closed in that release, not a reason
   for an absence term.

### Item 11: the clinical/health class split

1. **One class per real thing serves both layers.** A canonical record uses the same class as
   the layer 1 records it merges. Layer membership is told apart by provenance, not by class: a
   canonical record carries `prov:wasDerivedFrom` each of its sources and a
   `prov:wasGeneratedBy` naming the build that emitted it, stamped with the build's input
   versions (ruling 6 of the 2026-09-09 amendment).
2. **Strict layer 2 shapes select records by that marker, not by class.** A layer 1 record of
   the same class stays under the open shapes it validates against today.
3. **`clinical:Condition`, `clinical:Allergy`, `clinical:LabResult` and `clinical:Immunization`
   are deprecated, not made into layer 2 classes.** Each already carries `owl:deprecated true`
   and `rdfs:seeAlso` its `health:` equivalent, since clinical v1.13, so no ontology change is
   needed to record the ruling. What it adds is the standard migration window, which clinical
   has not yet opened for these four: a warning shape that fires wherever one of them is
   typed, with the four classes and their shapes removed in a later clinical version once the
   warning is observably absent from conforming output. One emitter remains, the reference
   implementation's `pod extract` command; it moves to the `health:` classes before the
   window closes. Properties still declared with one of the four as `rdfs:domain` are
   dropped from that domain or retired before removal, as clinical v1.16 and v1.18 did for
   others. Readers accept both spellings until the window closes.

## Amendment 2026-09-26: rulebook item 9 ruled, and the decision ratified

The 2026-09-05 amendment asked for its C-CDA naming decisions to be re-measured on a real
corpus before they became normative text. That measurement has now been run, and the
maintainer ruled item 9 on 2026-09-26. With it every rulebook item is ruled (items 1, 3, 4, 5
and 8 as amended on 2026-09-09, items 2, 6 and 7 as written, items 10 and 11 by the amendment
above, item 9 here), and the decision is ratified. The rulings are recorded here; the item
text above is unchanged apart from a pointer.

### The measurement

Inputs: two C-CDA CCD exports from each of two US health systems, downloaded weeks to months
apart by the record's owner, run through the reference implementation (`cascade-cli` 0.23.0)
with the import label held equal so that it could not be a factor. Counts only; no record
content was printed or stored.

- **Same system, seven weeks apart.** 1,016 of 1,424 records kept their name (71 percent).
  Every record whose source identifier was unique within its document kept it: lab results
  580 of 580, vital signs 116 of 116, immunizations 25 of 25, conditions 5 of 5, and the
  patient profile.
- **Section narratives: 0 of 385 kept their name.** Every download carries new document
  identifiers (0 shared), while 25 of 26 documents share a `setId` whose `versionNumber` is
  incremented on each download. The narrative markup also moves between downloads: footnote
  text, and the ids on table rows and cells.
- **Source identifiers reused within one document: 344 records carried one, and 22 of them
  were renamed.** What the disambiguator hashed included narrative reference pointers
  (`text/reference/@value`, `originalText/reference/@value`), nested encounter detail and an
  author organisation's address, all of which move between downloads.
- **Same system, three months apart.** The same pattern at smaller scale: 0 of 51 narratives
  kept their name, and some records named through the disambiguator (encounters and
  medications) were renamed, while labs, vitals, immunizations and allergies were stable.
- **Across the two systems.** Zero shared record identifiers in every cross pair, including
  immunizations present in both. Two systems' records of one real event are separate source
  records by construction, and only the canonical layer's key-field merge brings them
  together.
- **The reconciler's identity-collision split** did not fire: simulating a pod import of the
  later download over the earlier one, all 1,352 names from the first import survived, with
  zero splits.

### The rulings

1. **Tier 1 is the source's own identifier, as the HL7 instance identifier, plus the record
   class.** The identifier is `root:extension`, or the root alone when there is no extension;
   when an element carries several `<id>` elements, the first in document order with a usable
   root or extension is used. The name is minted from `{class}:{identifier}`, where the class
   is the record's identity type (every importer mints medications under one shared type, so
   a C-CDA and a FHIR record of one prescription agree). The root OID identifies the
   assigning authority, and that is how the source system enters the name. This reconciles the
   identity section's "the source system (`cascade:sourceIdentity`), the record class and that
   identifier": for C-CDA, source identity is carried by the identifier's root, and
   `cascade:sourceIdentity` is not an input to the name. Measured: every record with a unique
   source identifier kept its name across downloads. The consequence is intended: a record
   one organisation forwards with the original organisation's identifiers keeps the same
   name, and a record whose identifiers were re-issued is a second source record, merged in
   layer 2.
2. **The document context for a content-named record is the document set.** A section
   narrative has no identifier of its own, so it is named from a digest of the section's
   narrative under the C-CDA canonicalisation, with its section code and the enclosing
   document's `ClinicalDocument/setId` as context, falling back to the document's `id` only
   when there is no `setId`. An import label never participates. The narrative
   canonicalisation's exclusion list gains `@ID` and `@IDREF` on every narrative element,
   `@styleCode`, and footnotes (the `footnote` elements and the references to them), since
   footnote text was measured to change between downloads of one document (83 pairs). The
   exclusions apply to the name only: the full narrative text, footnotes included, is still
   stored. A re-download of an unchanged narrative therefore names the same record, and a
   narrative whose text changed between versions is a new record, added beside the old one,
   never written over it. Measured: 0 of 385 narratives kept their name while the per-download
   document id was the context.
3. **When a source identifier is not unique within its own document, the disambiguator
   hashes stable clinical fields only.** The case is an identifier claimed by two or more
   elements of one document whose content differs; claimants with identical content are one
   act restated and share one name. Each differing claimant is named
   `{class}:{identifier}#{digest}`, and the digest covers stable clinical fields (the code,
   the effective time, the value and fields like them), never narrative reference pointers
   (`*/reference/@value`) and never author or organisation addresses. Status is one of the
   stable clinical fields and is included (`statusCode`, and the value of a nested status
   observation): two statements sharing an identifier and differing only in status, one
   active and one resolved, are different claims and must not merge. A status change between
   downloads of such a record therefore yields a new name, reconciled in layer 2. Measured: 22
   of 344 such records were renamed between downloads under a disambiguator that hashed the
   whole element.
4. **Existing names are never renamed.** Records named under the earlier behaviour keep their
   names. Names under these rulings apply to imports from the implementing release on. The
   first import after that release adds one more copy of each affected record (every section
   narrative, and each record whose disambiguator changes), and the copies are reconciled by
   a machine-authored sameness judgement, as ruling 2 of the 2026-09-09 amendment and
   rulebook item 5 provide, never by renaming or deleting either copy.
5. **A split never changes a layer 1 name.** The reconciler's identity-collision split, a
   feared source of layer 1 renames, did not occur on the measured data. The rule is stated
   regardless: a split must never change the name of a record already written to layer 1.

### Implementations released before this ruling, and one open question

Implementations released before this ruling may have named section narratives from the
per-download document id and an import label, hashed the whole element in the id-reuse
disambiguator, and let the reconciler's identity-collision split move a record already in the
pod. Names they wrote stay valid under ruling 4; imports from an implementing release follow
rulings 2, 3 and 5.

One alignment question stays open, pending a ruling: how a record without a usable source
identifier is named. The identity section and the 2026-09-05 amendment name it from a digest
of the raw source element under C14N 2.0 with trimmed text nodes. The reference
implementation names it from a curated set of fields per record class, reaching a raw-element
digest only when those are empty, and that digest is of the parsed element serialised as JSON
with sorted keys. Either the text or the implementation moves to meet the other; which one is
not decided here.

Conformance gains vectors for each ruling (a re-download with a new document id and the same
`setId`; a narrative differing only in excluded markup or footnotes; an id reused with
differing content, where only a narrative reference pointer or an address changes between
downloads; the same, differing only in status) when the implementation lands.
