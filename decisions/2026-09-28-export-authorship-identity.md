# D-EXPORT-1: Who authors an export, how it is identified, and that it is valid unsigned

**Status:** Ratified by Jed Reinitz on 2026-09-28 (vocabulary tie-break under the ratified working agreement, r3), accepting Jay Ostis's answer of 2026-09-15 on the-cascade-protocol/spec#47 as written. Ruling B, that an export is valid unsigned, was made by Jed the same day, following Jay's lean. Normative text: `pod-structure.md` section 9.4; vocabulary: core v3.12.
**Date:** 2026-09-28
**Proposed by:** Jed Reinitz (spec#47), revised by Jay Ostis
**Prompted by:** the International Patient Summary export. [Composition-uv-ips](https://hl7.org/fhir/uv/ips/StructureDefinition-Composition-uv-ips.html) makes `Composition.author` 1..* and `Composition.attester` must-support, and [Bundle-uv-ips](https://hl7.org/fhir/uv/ips/StructureDefinition-Bundle-uv-ips.html) makes `Bundle.identifier` 1..1. The pod already knew who it belongs to (`<#me>`), who may operate it for the owner (`cascade:ProxyAgent`) and what produced an export (`cascade:ExportManifest`), but no rule said how those become `author`, `attester` and `identifier`, and the manifest had no identifier.

---

## Rulings

### A. Authorship and identifiers (spec#47)

1. **The author is whoever made the export.** That is the patient, a related person acting for the patient (a `cascade:ProxyAgent`, exported as a FHIR `RelatedPerson`), or both, depending on who created it and why. A young child is the patient and not an author; the parent is the author. The patient is not an author by default.
2. **The author attests.** Each person who is an author is also an attester, with `Composition.attester.mode` `personal`.
3. **The software is a `Device`.** The application that produced the export is listed as a `Device` author, so a recipient can tell a patient-held summary from a provider-issued one.
4. **The manifest carries `dct:identifier`, which becomes `Bundle.identifier`.** It is a random version 4 UUID in `urn:uuid:` form, new for every export. Two exports of the same content get two identifiers.
5. **`Composition.identifier` is omitted.** It is optional in IPS, and optional fields are added only when they serve a need.
6. **People get identifiers minted for one export only.** The patient and each author get an entry whose `fullUrl` is a random `urn:uuid` minted for that export. The subject and the authors reference them by it. It means something only inside that one export. Nothing currently requires a recipient to trace these back to the same person across exports; if that changes, this ruling is revisited.
7. **The pod's own patient identifier never goes in an export.** `cascade:podIdentifier` (D-POD-ID-1) stays inside the pod. Keeping it there is the better default, not something signing depends on (spec#63).
8. **`Patient.identifier` carries only source-system record numbers.** Record numbers from the hospitals and other systems the data came from, where appropriate, and nothing else.
9. **No other vocabulary is added.** `dct:identifier` is the Dublin Core term, already in the manifest's namespace family (`dct:title`, `dct:created`); no `cascade:` term is minted.

### B. Signatures

10. **An export is valid unsigned.** No signature property is added now. It is specified together with signing itself: the key a recipient checks, how the recipient comes to trust it, and how it survives a lost or replaced device. `did:plc` is the direction (spec#63). Adding the property then costs one version bump; guessing its shape now risks a term that has to change.
11. **The publication event stays as D-CANONICAL-1 requires.** Ruling 5 of the two-layer decision's 2026-09-09 amendment is unchanged: an identifier that leaves the pod is minted by a recorded publication event, and the export's `dct:identifier` is that identifier.

## Scope: which exports

"Export" in rulings 1 to 8 means a document made for a recipient outside the pod, of which the IPS Bundle is the first. Such an export is a report a person brings to a recipient: nothing in it is meant to be traced back to the pod, for now. If a recipient later needs that link, the direction is a `did:plc` linked to the pod identifier (spec#63), not the pod identifier itself. A whole-pod copy (`pod export` as a zip or directory) is the pod itself, for backup, restore or moving between devices: it carries `/profile/extended.ttl`, and with it the pod identifier, because a restore must keep it (D-POD-ID-1, Consequences). Ruling 4 applies to both: every `cascade:ExportManifest` carries its own `dct:identifier`.

## Vocabulary (core v3.12, core shapes 1.11)

- `cascade:ExportManifestShape` gains `dct:identifier`: at most one value at `sh:Violation` (a second would identify one export two ways); presence, and the lowercase version 4 `urn:uuid` form typed `xsd:anyURI`, at `sh:Warning`.
- **Why presence is a Warning.** Every manifest written before this version has no identifier, including the conformance reference pod's and every manifest the SDKs and applications write today. A `sh:Violation` would make each of them fail validation for a field that did not exist when it was written. The Warning is the migration path: new manifests MUST carry one, existing ones are reported and stay valid. Raising it to a Violation is a later, separate change once writers have caught up.
- `xsd:anyURI`, as for `cascade:podIdentifier`, since both are `urn:uuid` values.
- The `cascade:ExportManifest` and `cascade:ProxyAgent` comments state the mapping. `contexts/v1/core.jsonld` and the merged `cascade.jsonld` gain `identifier` so a JSON-LD writer produces the typed literal the shape checks.

## Consequences

- An IPS export can populate `Bundle.identifier`, `Composition.author` and `Composition.attester` from what the pod already records, with no new class.
- A recipient cannot link two exports from the same pod by any identifier the pod mints. It can link them only by the source-system record numbers in `Patient.identifier`, which it could already see.
- Writers (the command-line export, the SDK manifest models, the applications' share and export paths) must mint a fresh `urn:uuid` per export, write it to the manifest, and record it with the export's publication event.
- D-CANONICAL-1's IPS export section points here.

## What this does not decide

- **Identifiers for other entries.** Observations and other records a recipient must tell apart across exports are a separate question. Ruling 5 of D-CANONICAL-1 still governs any identifier that leaves the pod; this decision assigns none beyond the Bundle and the people.
- **The vocabulary of the publication event record, and any digest of the export's content.** Both belong to ruling 5's implementation; nothing here adds or removes them.
- **`Composition.custodian`.** Omitted: a patient-held pod has no custodian organisation. Revisit when a pod is hosted by an organisation on the patient's behalf.
- **A coded caregiver relationship.** `cascade:proxyRelationship` may be carried as `RelatedPerson.relationship` text; a coded mapping is not decided here.
- **Attestation by a clinician** (`attester.mode` `professional`). Nothing in the pod carries one today.

## Standards

- FHIR R4 [Composition](https://hl7.org/fhir/R4/composition.html): `author` targets include Patient, RelatedPerson and Device; `attester.party` includes Patient and RelatedPerson. [Bundle.signature](https://hl7.org/fhir/R4/bundle-definitions.html#Bundle.signature) is 0..1.
- [Composition-uv-ips](https://hl7.org/fhir/uv/ips/StructureDefinition-Composition-uv-ips.html), [Bundle-uv-ips](https://hl7.org/fhir/uv/ips/StructureDefinition-Bundle-uv-ips.html).
- [DCMI Terms: identifier](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/identifier); [RFC 4122](https://www.rfc-editor.org/rfc/rfc4122) `urn:uuid`, with `system` `urn:ietf:rfc:3986` in a FHIR `Identifier`.
