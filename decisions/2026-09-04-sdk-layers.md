# D-LAYERS-1: What an SDK is for

**Status:** Ratified
**Date:** 2026-09-04
**Decided by:** Jed Reinitz
**Prompted by:** the derive-from-spec epic (jayostis/sdk-typescript#69, PR #89) and the
proposal to publish spec as data (jayostis/spec#56). Both remove from the SDKs the code that
transcribes this repository by hand, which raised the question the maintainers had not written
down: once the rules live in `spec/` and the oracle lives in `conformance/`, what is an SDK?

---

## The decision

**A Cascade SDK, in any language, is four layers. Only two are hand-written, and only one of
those is specific to this protocol.**

| layer | holds | written by |
|---|---|---|
| **A. Spec data** | the vocabularies, shapes, contexts and record-type table as published by this repository | nobody downstream: copied from a pinned `spec/` revision or its release asset (see D-DERIVED-1) |
| **B. Generic engine** | JSON to RDF and back, driven by context and ontology; SHACL evaluation over the shapes graph; record-type lookup | once per language; never names a record type |
| **C. Protocol runtime** | what this repository states in prose and cannot state in SHACL: identity and content addressing (code-point sort, canonicalisation), encryption at rest, pod layout (`attachments/{algorithm}/{digest}`, buckets, amend/retract overlays), provenance and egress logs, consent mechanics, signing | once per language, against conformance **vectors** |
| **D. Types and platform adapters** | typed models for the host language; HealthKit, browser versus Node crypto, filesystem versus Solid | types are generated from layer A; adapters are hand-written where the platform differs |

**Layer C is the SDK.** Everything spec can state, spec states and ships as data. The SDK is
the code for what spec can only say in words, plus the engine that reads spec's data, plus the
ergonomics that make it usable in its language.

## Why

Measured at `sdk-typescript` main on 2026-09-04: 9,249 lines, of which about 7,300 (79%) are
a person re-typing this repository into TypeScript: one interface per class, a per-type Turtle
writer, a hand-written Turtle parser, a validator restating the shapes, and predicate tables
restating the contexts. That code has no consumer in the organisation's own repositories and
carried defects this repository never had (a parser with no comma-object-list branch; value
sets that contradict the published shapes). Meanwhile the one implementation with real users,
`cascade-cli`, imports none of it and carries its own copy of the same layers. The identity
sort defect fixed on 2026-09-03 (D16) was present, in the same function, in both.

Four hand-maintained copies is the cost the seven-step vocabulary checklist exists to manage.
The checklist is the symptom. The decision above removes the reason for most of it: layers A
and D become artefacts, and only B and C are code anyone maintains.

## Consequences

- **An implementation is a Cascade implementation iff it passes conformance.** Fixtures test
  layer B. Layer C needs vectors (identity, canonical ordering, encryption, pod layout), which
  `conformance/` will grow; until it does, this repository's prose is the only oracle for C.
- **Nothing hand-transcribed from this repository is deleted before the rule it carried exists
  here and a conformance fixture has gone red-then-green without it.** The order is: state the
  rule upstream, prove the fixture catches its absence, then delete the copy.
- **Browser-safety (D-BROWSER-1) is a layer C requirement.** Layer A is `JSON.parse`, layer B
  is pure computation. Only layer C touches platform APIs, so that is where the requirement is
  enforced and where any vendored parser lives.
- **The vocabulary checklist collapses.** Authoring (step 1) and conformance (step 3) stay
  human on purpose. Steps 4 to 7, one per consumer, become one mechanical re-pin that a script
  performs and a drift check verifies.

## Direction of travel per implementation (recorded as intent, not scheduled)

- **`cascade-cli` is to be built on `sdk-typescript`, not beside it.** Same language, same
  runtime. The cli holds the proven layer C; the direction is to extract that runtime into the
  SDK and make the cli depend on it, module by module, identity first. Not a port of the SDK
  into the cli, and not a rewrite. This starts only after the SDK's layer B is proven against
  this organisation's conformance corpus. It is recorded now so that no third copy is started
  in the meantime.
- **`sdk-python` stays a thin reader** (generated types, an off-the-shelf SHACL engine, layer
  C only as a named consumer requires) until a consumer is named.
- **`cascade-sdk-swift` keeps its runtime and gains generated models.** It is the production
  lineage and the one with platform adapters that matter.

## Amendment 2026-09-04: the query layer

The four layers say how data gets into a pod and how it is judged. They say nothing about
asking the pod a question, and no Cascade application has yet asked its graph anything it
could not have asked a JSON file. Querying is the payoff of having built a graph, so it is
named here as a layer of its own, sitting on B and C:

| surface | what it is | which layer it belongs to |
|---|---|---|
| **typed queries** | generated accessors from the record-type table and shapes: active medications, results for a code in a date range, a timeline | D (generated) |
| **SPARQL** | the escape hatch for every question the generated accessors did not anticipate | B (engine) |
| **traversal** | record to record, and provenance chains back to the source document | B over C's provenance |
| **as-of** | what the pod said at a date, answered from the amend and retract overlays | C exposed through B |
| **consent-scoped views** | the subgraph a recipient may see, a `CONSTRUCT` under the ACL: the export primitive | C exposed through B |
| **search** | full text over notes and attachments; nearest-neighbour over embeddings | B, optional |
| **federation** | one question over several pods (the caregiver case) | later |

Two rules follow. **Query never bypasses C.** A query surface reads through the same
decryption, consent and provenance code paths a write uses, so "what may this caller see"
has one answer. **The engine is a dependency, not a re-implementation.** SPARQL and SHACL
engines are not written here; one is adopted per language, or one engine is adopted for
all of them, and the conformance corpus is the oracle that says it agrees with what ships.
Layer C stays dependency-free; the engine ships as an optional companion package.

**Open:** which engine. An evaluation is in progress; this section is amended when it
reports.

## What this does not decide

The format of the published contexts (JSON-LD 1.1 scoping versus unambiguous keys) and
whether they are hand-authored or generated. That is D-CONTEXT-1
(`2026-09-04-context-format.md`).
