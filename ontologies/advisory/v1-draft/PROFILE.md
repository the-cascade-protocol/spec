# Cascade Advisory Patch (CAP) — Profile of W3C LDPatch

**Status:** Profile draft v0.1
**Underlying spec:** [W3C Linked Data Patch Format](https://www.w3.org/TR/ldpatch/) (Recommendation, 2015)
**Profile namespace:** `https://ns.cascadeprotocol.org/advisory/v1#`
**Date:** 2026-05-04

---

## What this profile is

Cascade Advisory Patch (CAP) is a **strict subset** of W3C LDPatch designed for clinical knowledge updates that are:

- **Author-readable.** A genetic counselor or VCEP curator can read a CAP file and understand its full effect without RDF training.
- **Statically auditable.** A reviewer can determine the complete set of triples a patch can produce and the conditions under which they fire, by reading the file alone.
- **Bounded in execution.** A CAP applier has predictable resource cost regardless of the patch contents.
- **Forward-compatible with LDPatch.** Every CAP file is a valid LDPatch file. An issuer who ships a CAP file works with any conformant LDPatch implementation.

What the profile gives up: full LDPatch's `Delete`, `Cut`, `UpdateList`, prefix manipulation, and unconstrained `Bind` queries. What it keeps: `Add` insertions, parameterized by a single bound variable matched against a stable identifier.

## Constraints

A document conforms to CAP if **all** of the following hold:

### C1. Operations restricted to `Add` and `Bind`

Only the `Add` operation may produce triples. `Delete`, `Cut`, and `UpdateList` are forbidden. Supersession of an existing record (e.g., a reclassification superseding a prior interpretation) is expressed additively by inserting `prov:wasRevisionOf` triples that link a new node to the prior — the prior node is never modified or removed. This makes every CAP application monotonic and roll-forward auditable.

### C2. At most one `Bind` per advisory, restricted to single-identifier match

A `Bind` may bind exactly one variable. The path expression must be a `?var <predicate> <literal>` triple pattern where:

- `<predicate>` is one of a published whitelist (`genomics:caId`, `genomics:vrsId`, `genomics:clinvarVariationId`, `clinical:loincCode`, `clinical:rxNormCode`, `clinical:icd10Code`, `clinical:snomedCode`, `genomics:hgncId`).
- `<literal>` is a fully-quoted string literal (no variable, no IRI computation).

This is the **single most important constraint.** It means an advisory matches against exactly one stable identifier — never against a free-text HGVS string, never against a complex graph pattern, never recursively. The applier runtime cost is O(index lookup), not O(graph traversal).

### C3. No prefix manipulation

The `@prefix` directives at the top of a CAP file are limited to a published whitelist of vocabularies — Cascade vocabularies, W3C standard prefixes (`prov:`, `xsd:`, `rdfs:`, `owl:`), and the canonical genomics-standards prefixes (`hpo:`, `mondo:`, `so:`, `clinvar:`, `omim:`, `hgnc:`). Inventing a new prefix in a patch file is forbidden — it would let an issuer reference vocabulary the pod hasn't pre-trusted.

### C4. No IRI computation

All IRIs inserted by an `Add` are either:
- fully-qualified literals from the patch text, or
- the bound `?var` from the (single, constrained) `Bind`.

No `CONCAT`, no template substitution, no string-to-IRI conversion. The set of IRIs an advisory can mention is finite and obvious from reading the file.

### C5. Bounded insert size

A CAP advisory inserts at most **64 triples per match**. This is a soft limit on advisory complexity — for clinical reclassifications, a typical advisory inserts 5-15 triples. Larger advisories should be split into multiple smaller ones or use a non-CAP delivery mechanism.

### C6. Required envelope metadata

Every CAP file must declare, before any operation:

```turtle
<> a advisory:CascadeAdvisoryPatch ;
   advisory:profileVersion "0.1" ;
   advisory:advisoryClass <one of the published advisory classes> ;
   advisory:issuer <issuer-IRI> ;
   advisory:issuedAt <xsd:dateTime> ;
   advisory:humanSummary "<one-paragraph plain text>" ;
   advisory:supersedes <prior-advisory-IRI>?  # optional
.
```

The `humanSummary` is what the user sees in the queue UI. The applier MUST reject patches without it.

## Profile validation

A CAP applier validates a candidate patch in this order:

1. **Parse as LDPatch.** Any LDPatch syntax error → reject.
2. **Profile envelope check.** Required `advisory:` metadata present and well-formed → continue, else reject.
3. **Constraint check.** C1–C5 enforced statically → continue, else reject.
4. **Signature verification.** VC envelope signature valid against trusted issuer keys → continue, else queue for explicit user trust review.
5. **Selector evaluation.** Bind query against pod → if zero matches, advisory is logged as inapplicable; if one match, proceed; if multiple matches, each is treated as a separate application.
6. **Application.** Inserts performed; `cascade:AdvisoryApplicationActivity` recorded with `prov:used` linking to the patch + matched node.

## Worked examples

See:
- `example-brca2-reclassification.ldpatch` — reclassification of a VUS to Likely Pathogenic
- `example-cpic-cyp2c19-warfarin.ldpatch` — PGx dosing guidance update tied to a star allele

Both files are valid LDPatch and conform to this profile.

## What CAP does NOT solve

- **Cross-record advisories.** A CAP advisory operates on one record (one Bind match). Advisories that need to update multiple unrelated records — e.g., "update all conditions with ICD-10 code X to also carry SNOMED code Y" — are out of scope for CAP v0.1. They'd require either a non-CAP delivery mechanism or splitting into N separate advisories.
- **Dependent inserts.** All inserts in a CAP advisory fire together or not at all — there's no conditional-on-prior-insert logic. If you need to insert B only when A inserted successfully, ship two advisories chained via `advisory:requires`.
- **Computation over the bound value.** The bound `?var` IRI can appear in inserts, but you cannot derive a new value from it (no string ops, no arithmetic).

These are deliberate omissions — adding any of them returns CAP toward unconstrained LDPatch and breaks the auditability story.
