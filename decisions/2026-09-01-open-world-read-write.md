# D-OPENWORLD-1: The Open-World Read/Write Contract

**Status:** Ratified
**Date:** 2026-09-01
**Decided by:** Jed Reinitz
**Prompted by:** jayostis/spec#32 (ASK-03), which implemented both halves of this contract in a
fork and asked whether that was the intent. It was, but no document said so; this one does.

---

## The question

What does a writer owe a key the vocabulary does not declare, and what does a reader owe a
predicate it cannot name? Nothing in the corpus answered either. No shape is `sh:closed`, so
SHACL cannot tell a declared predicate from an invented one; and the SDKs had answered by
accident, in the worst way — writing predicates they could not read back, and dropping values
that matched no branch (the silent-drop defects behind sdk-typescript #14/#15).

## The decision

**Preservation beats policing at the write boundary. Validation reports; it never refuses, and
it never destroys.**

1. **A writer writes every key that is present.** A declared child is written by its rule's
   form; an undeclared child is written by runtime type. Refusing or silently dropping a key is
   data destruction, and the write boundary of a patient's own pod is the last place to destroy
   data. The SDK is not a gatekeeper of vocabulary evolution.
2. **A reader reads every triple back**, including predicates it cannot name. A
   read-modify-write cycle MUST round-trip triples the implementation does not recognise;
   "unknown" never means "deleted".
3. **A predicate with no prefix binding round-trips as its full IRI in angle brackets.** That
   is standard Turtle. A missing prefix is a cosmetic gap; cosmetics never justify loss.
4. **`validate()` reports an undeclared child as a finding.** The report is the policing. This
   mirrors `cascade validate`'s ratified stance that an unshaped subject is counted and named,
   never a failure — the gap is in the vocabulary, not in the patient's data.
5. **`sh:closed` stays out of the shapes.** A Cascade record deliberately carries predicates
   from several vocabularies at once (`cascade:` + a domain vocabulary + `prov:` + extensions),
   so closed shapes would reject conformant layering. The unknown-predicate guard lives in SDK
   validators and tooling reports, never in the shapes.

## Consequences

- The fork's implementation of both halves (faithful write, faithful read, reported
  validation, bracketed-IRI round-trip) is the intended behaviour and can be carried upstream
  as-is where its code is wanted.
- Any future proposal to add `sh:closed`, to make writers refuse unknown keys, or to let a
  reader drop unrecognised triples should be pointed here first.
- The silent-drop bug class this contract forbids has been found three times in one SDK
  (repeated `dataAbsentReason`, repeated `interpretationSourceCode`, blank-node children); the
  contract is the general statement of why each was a bug.
