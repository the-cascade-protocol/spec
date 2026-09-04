# D-CONTEXT-1: The published JSON-LD contexts

**Status:** Ratified
**Date:** 2026-09-04
**Decided by:** Jed Reinitz
**Prompted by:** jayostis/spec#3, #4, #44, #46, #47, PR #55 (marked DO NOT MERGE by its author),
jayostis/sdk-typescript#70 (the Supplement finding), and D-DERIVED-1 condition 5. The primer in Part 1 is kept on purpose: the decision is only
legible to someone who knows what a context is and why ours could not say what the ontologies say.

---

## Part 1. Primer: what a context is and why ours cannot say what the ontologies say

**A context is a dictionary from JSON keys to IRIs.** A developer writes plain JSON:

```json
{ "type": "MedicationRecord", "medicationName": "Lisinopril", "dosage": "20 mg" }
```

The context says what each key *means* in RDF: `medicationName` is `clinical:medicationName`,
`dosage` is `clinical:dosage`. With the context applied, the JSON is a graph, and the same graph
can be written as Turtle. Without it, the keys are just strings.

**Rule of JSON-LD 1.0: one key, one meaning, per document.** That is fine as long as no key needs
two meanings. Ours do, in three distinct ways. Keep them apart; they have different fixes.

### Problem 1. The same local name is declared in several vocabularies

Counted across the six stable ontologies on 2026-09-04: about 30 local names are declared by
more than one vocabulary. `notes` exists in four (`cascade:`, `clinical:`, `health:`, `pots:`),
`date` in three, `status` in three, `sourceRecordId` in five. In RDF this is legal and
unambiguous, because a triple carries the full IRI. In JSON it collides the moment two of them
appear in one document under one context.

*Where it bites today:* only in `cascade.jsonld`, the "everything" context that merges the other
six into one 1,483-line dictionary. Merging seven one-meaning dictionaries produces a file that
must pick one meaning per key and silently loses the rest. Measured in jayostis/spec#46: 34 keys collide in it,
and it drops `@container` from 7 terms. **Each per-vocabulary context is unambiguous on its own**
(measured: each is 100% within one namespace). So the merged file is the defect, not the six.

### Problem 2. Nested structures: the class and the children are stated nowhere (#44)

A profile carries an address as an object. The Turtle for it is a blank node typed
`cascade:Address` with six child predicates. Producing that needs three facts: the predicate for
`address`, the class of the nested node, and the meaning of each child key. Our context states
the first (and states it wrongly: `"@type": "@id"` says "an IRI reference", but the value is an
inline object). The class is stated nowhere. The children happen to resolve because they are
also top-level keys, which holds only until a child key is also a top-level key with another
meaning. That is exactly the live defect: `notes` inside a `cascade:RecordSummary` must be
`cascade:notes`, while `notes` at the top of a health record is `health:notes`. A flat context can
hold one.

### Problem 3. Bare tokens for enumerated values (#47)

Records write `"dataProvenance": "ClinicalGenerated"`. The context says the value is an IRI, so a
conformant processor resolves the bare token against the document base and produces a
**relative IRI** that differs per consumer. 85 of 92 fixtures carry this field. The intended
meaning is `cascade:ClinicalGenerated`, an individual in the core vocabulary.

### What is *not* a spec problem: SDK-invented keys

The Supplement finding (sdk-typescript#70) looked like a fourth case: JSON `dose` means
`clinical:dosage` on a Medication and `clinical:dose` on a Supplement. Checked against
`contexts/v1/clinical.jsonld`: spec already publishes **both** keys, `dosage` for
`clinical:dosage` and `dose` for `clinical:dose`. The SDK's Medication model chose the JSON key
`dose` and mapped it to `clinical:dosage` itself. That is an SDK invention, fixed by the SDK
adopting spec's key. It is listed here because it is the clearest example of the rule this
decision should state: **a JSON key is the local name of the predicate it maps to.** No
implementation renames.

### The two tools JSON-LD 1.1 adds

- **Type-scoped contexts.** A term definition can carry its own `@context`, active inside the
  node it introduces. `address` can say: my value is a `cascade:Address`, and inside it these are
  the children. `clinicalSummary` can say: inside me, `notes` means `cascade:notes`. This is the
  only mechanism that solves Problem 2 without renaming keys.
- **`@version: 1.1`.** A 1.0 processor that meets it **refuses** the document rather than
  silently mis-expanding. For clinical data that is the safe direction.

(`"@type": "@vocab"`, the fix for Problem 3, is available in 1.0 already.)

### The two ways to resolve a colliding key, and why the choice is smaller than it looks

1. **Scope it** (1.1): `notes` keeps its name; its meaning depends on the node it is in.
2. **Rename it** (1.0): `summaryNotes`, `readingDate`, one key per IRI, flat.

Renaming changes every JSON record and every serializer, and it does not solve Problem 2 (a
nested object still needs its class stated). Scoping solves Problems 1 and 2 and leaves the
JSON unchanged. PR #55 prototyped scoping and was then marked DO NOT MERGE by its author, not
because scoping is wrong, but because **hand-authoring** the scoped blocks is a third place for
the same fact to drift (ontology, flat entries, scoped children). Its author's current position is that
the mapping should be **generated** from the ontology and shapes. That is a separate axis from
the format, and this decision treats it separately.

## Part 2. The decision

**C1. Authored is normative.** The ontologies and shapes are the source of truth for the JSON to
RDF mapping. The contexts are a published artefact that MUST agree with them; a context that
disagrees is the defect. (This answers #4's "make the context normative": it is normative for a
JSON consumer *because* it is derived from and gated against the ontology, not instead of it.)

**C2. A JSON key is the local name of its predicate.** No implementation invents or renames keys.
Where a vocabulary declares `dosage`, the JSON key is `dosage`. Where two vocabularies declare
the same local name, both keys exist and scoping (C4) distinguishes them.

**C3. The per-vocabulary contexts are the mapping. `cascade.jsonld` is retired as a mapping.**
It stays published for one deprecation window as a convenience, with its collision policy
stated in the manifest (D-DERIVED-1's `aggregateContext`), and is not used to write documents.
A document declares the context of the vocabulary its record class belongs to.

**C4. JSON-LD 1.1 with type-scoped contexts.** Every per-vocabulary context declares
`@version: 1.1`. A term whose range is a structured class carries `@type` naming that class and
a scoped `@context` listing the class's own properties (from the shapes: `sh:targetClass` to
`sh:path`). A term whose meaning differs by enclosing class is scoped the same way. Enumerated
ranges use `"@type": "@vocab"`.

**C5. Generated, with a shrink-only override file, once the residue is measured.** D-DERIVED-1's
Phase 5 measures, per vocabulary, how many terms a rule-generated context would get wrong
against the published one. If the residue is small and every entry is explainable, the contexts
flip to generated-plus-overrides in a follow-on epic. Until then they stay hand-authored and the
Phase 3 agreement check (context versus ontology versus shapes) gates every PR touching them.

**C6. Under-specification is fixed regardless (#46).** Missing `@type` on date terms, code terms
declared as literals where the corpus writes IRIs, numeric datatypes: each is resolved to what the
shapes say, by the agreement check, before any format change lands.

## Part 3. What it costs

- **Consumers need a 1.1 processor.** jsonld.js and pyld are 1.1. The TypeScript SDK's generic
  engine must implement type-scoped resolution, which is more than the ~250 lines its author
  budgeted when spec used zero scoping. PR #55 names this cost. It is the price of
  not renaming every key, and it is paid once, in layer B.
- **`cascade.jsonld` consumers.** The live URL `cascadeprotocol.org/ns/context/v1/cascade.jsonld`
  is what SDK-written documents reference today. Only in-house code reads it. Retiring it as a
  mapping means new documents reference their vocabulary's context instead; old documents keep
  resolving during the deprecation window.
- **A vocabulary PR that adds a property to a structured class** must also update the scoped
  children (until C5 flips to generated). The agreement check makes forgetting a red job, not a
  silent drift.

## Part 4. Alternatives considered and rejected

- **Rename every colliding key** (`summaryNotes`, `readingDate`), staying in 1.0. Rejected: it
  changes every JSON record and serializer, and it still cannot express a nested structure's
  class and children (Problem 2), so 1.1 would be needed anyway.
- **Keep `cascade.jsonld` as the mapping and scope its collisions.** Rejected: a merged
  dictionary of seven vocabularies has no per-vocabulary rule that produces it; its whole
  content is the resolution of cross-vocabulary collisions, which is exactly what cannot be
  generated or checked. It stays as a convenience with its policy stated, not as the mapping.
- **Let implementations choose their own JSON keys** (the status quo that produced the
  Medication `dose` case). Rejected: every renamed key needs a per-class override table in
  every implementation, and that table is the drift the whole derive-from-spec direction
  exists to remove.
- **Flip to generated contexts now**, before measuring the residue. Rejected: the measurement
  is cheap (D-DERIVED-1 Phase 5) and a generator whose override file is large is a hand-authored
  context with extra steps. Measure, then decide.
- **Stay on JSON-LD 1.0 and rely on embedded `@context` objects inside nested nodes** (legal in
  1.0). Rejected as the published mechanism: it moves the scoping decision into every document
  a writer emits instead of stating it once in the context, and a reader holding only the
  context still cannot tell what a nested `notes` means.

## Sequencing

C6 and the agreement check first (they are format-neutral). Then C4 on the per-vocabulary
contexts, one vocabulary per PR through the checklist, `core` first because it holds the
structured classes. C3's deprecation notice lands with the first 1.1 context. C5 after Phase 5
reports. sdk-typescript's Phase 3 engine sizes for scoped resolution from the start.
