# Cascade Advisory Vocabulary — Changelog

All notable changes to `advisory.ttl` are recorded here. The vocabulary is
pre-stable; pre-stable drafts are NOT registered in `spec/VOCAB_VERSIONS`
(per D-PATH in the Genomics & Advisory implementation plan). When the
vocabulary graduates to `v1.0` stable a single row will be added there.

## v1.0-draft.0.1 — 2026-05-05

Initial draft of the Cascade Advisory Patch (CAP) profile vocabulary
(TASK-0.3 in the Genomics & Advisory v0.1 workstream).

### Added — classes

- `advisory:CascadeAdvisoryPatch` — the constrained-LDPatch envelope (subclass
  of `prov:Entity`). Application is recorded by
  `cascade:AdvisoryApplicationActivity`, declared in core v3.1.
- `advisory:AdvisoryClass` — closed taxonomy of advisory categories.
- `advisory:Cadence` — closed enumeration of recommended check cadences.
- `advisory:TrustedIssuer` — per-pod issuer trust record (per D-Q3).
- `advisory:TrustSourceEnum` — provenance flag for how an issuer was added.
- `advisory:AutoApplyPolicy` — per-pod opt-in auto-apply policy.
- `advisory:AutoApplyScope` — `(issuer, advisoryClass)` tuple for auto-apply.

### Added — six AdvisoryClass named individuals

- `advisory:SafetyCritical` — every-app-open cadence.
- `advisory:VariantReclassification` — monthly cadence.
- `advisory:DrugInteraction` — monthly cadence.
- `advisory:LabReferenceRangeUpdate` — quarterly cadence.
- `advisory:SurveillanceGuidelineUpdate` — quarterly to annual cadence.
- `advisory:CarrierFrequencyUpdate` — annual cadence.

### Added — six Cadence named individuals

- `advisory:EveryAppOpen`, `advisory:Daily`, `advisory:Weekly`,
  `advisory:Monthly`, `advisory:Quarterly`, `advisory:Annually`.

### Added — four TrustSourceEnum named individuals

- `advisory:RecommendedStarterList`, `advisory:UserAdded`,
  `advisory:ImportedFromRegistry`, `advisory:VerifiedViaDID`.

### Added — envelope properties

Required: `advisory:humanSummary`, `advisory:advisoryClass`,
`advisory:issuer`, `advisory:issuedAt`.

Optional: `advisory:advisoryId`, `advisory:supersedes`,
`advisory:expiresAt`, `advisory:applicableUntil`, `advisory:profileVersion`,
`advisory:issuerName`, `advisory:evidenceUrl`,
`advisory:appliesToActiveOnly`, `advisory:cadence`.

### Added — signature properties (per D-Q4)

`advisory:signature` (detached JWS Ed25519, RFC 7515 compact serialization),
`advisory:signatureIssuer` (iss), `advisory:signatureIssuedAt` (iat),
`advisory:signatureExpiresAt` (exp), `advisory:signatureContentType` (cty,
fixed to `application/x-cascade-advisory-patch`).

### Added — TrustedIssuer properties

`advisory:trustedIssuerId`, `advisory:trustedIssuerName`,
`advisory:trustedIssuerPublicKey`, `advisory:trustSource`,
`advisory:trustAddedAt`.

### Added — AutoApplyPolicy properties

`advisory:appliesTo`, `advisory:effectiveFrom`, `advisory:effectiveUntil`,
`advisory:requiresQuorum` (forward-compat flag, unused in v0.1),
`advisory:scopeIssuer`, `advisory:scopeAdvisoryClass`.

### Design notes

- Per D-PATH the namespace URI is `https://ns.cascadeprotocol.org/advisory/v1#`
  (stable major) with `owl:versionInfo "1.0-draft"`. Pre-stable drafts are
  NOT registered in `VOCAB_VERSIONS`.
- Per D-Q3 the trust model is per-pod. The vocabulary declares
  `advisory:TrustedIssuer` and `advisory:TrustSourceEnum` so each pod can
  carry its own trust graph at `<pod>/trust/issuers.ttl`; the protocol does
  NOT define a centralized registry.
- Per D-Q4 the signing envelope is detached JWS Ed25519 for v0.1; W3C VC 2.0
  wrapping is deferred to a later profile version.
- `cascade:AdvisoryApplicationActivity` is declared in core v3.1 and is
  REFERENCED here, not redeclared.
- Both `advisory:expiresAt` and `advisory:applicableUntil` are declared.
  The published worked CAP examples use `applicableUntil`; `expiresAt` is
  the form named in the implementation plan. They are equivalent in
  meaning and both are honoured by the applier; future profile versions
  may consolidate.
