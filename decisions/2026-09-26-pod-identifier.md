# D-POD-ID-1: A pod has one random identifier, minted once, kept inside the pod

**Status:** Ratified by Jed Reinitz on 2026-09-26 (vocabulary and pod layout, his tie-break under the ratified working agreement, r3). It records the outcome agreed with Jay Ostis on 2026-09-14 and written into the-cascade-protocol/spec#63 on 2026-09-15, which the-cascade-protocol/spec#53's earlier HTTP-URL ruling was withdrawn in favour of on 2026-09-11. Until now no decision document carried it and nothing implemented it.
**Date:** 2026-09-26
**Proposed by:** Jed Reinitz
**Prompted by:** the wellness importer, the first code that puts a pod component into record names. D-WELLNESS-1's Q1 seeds include a "pod subject" that must be "stable for the life of the pod", and every command-line pod resolved it to the same constant, `/profile/card.ttl#me`.

## Decision

1. **What it is.** Every pod has exactly one identifier: a random version 4 UUID in `urn:uuid:` form, lowercase, minted when the pod is created. It identifies the pod and the patient record the pod keeps.
2. **Where it lives.** On `<#me>` in `/profile/extended.ttl`, as `cascade:podIdentifier` (core v3.11), a literal of type `xsd:anyURI`. That file is owner-only and inside the encrypted pod. It is never written to `/profile/card.ttl`, which is the one profile document a pod may serve to unauthenticated readers. It is a property of `<#me>`, not an `owl:sameAs`, so nothing is inferred to be the same individual.
3. **Minted once, never recomputed.** `pod init` mints it. A pod created before this decision gets one the first time a command needs it, and it is written before any record is named from it. It never changes afterwards. Nothing derives it: it is read back, so "stable for the life of the pod" holds by construction.
4. **It is the naming subject.** Wherever a naming rule includes a pod subject (D-WELLNESS-1 Q1), the input is this identifier as written. Because the seed is hashed, a record's name does not reveal it. Two pods therefore never mint the same name for the same watch, day or summary, which is the cross-person collision Q1 exists to prevent.
5. **It never leaves the pod.** D-CANONICAL-1 ruling 5 applies unchanged: exports carry no Cascade identifier by default. An application that needs a handle for a pod folder while the pod is locked keeps its own separate value; it never reads or copies this one for that purpose.
6. **`did:plc` stays parked.** If signing is ever needed, a `did:plc` is created at that upgrade and linked to this identifier, never replacing it, as spec#63 describes.

## Consequences

- **A pod rebuilt from the same exports is a new pod.** It gets a new identifier, so records named from the pod subject (today, the wellness records) get new names. A restore from backup keeps the identifier and every name. Applications must say so at the moment a person chooses between rebuilding and restoring.
- **One value, one place.** A pod with two identifiers would name the same thing two ways. `cascade:PodIdentifierShape` rejects a second value.
- **Nothing is re-minted by this decision.** No pod yet carries records named from a pod subject.
- `pod-structure.md` section 3.6 documents the property; core v3.11 declares it and its shape.
- The commented provenance example in `core.ttl` that used an `https://id.cascadeprotocol.org/users/…` agent is replaced, since no such identifier is minted.

## What this does not decide

Which name-based UUID version and hash the naming seeds are fed to. That changes every name family at once and is decided with the import pipeline's naming convention, not here.
