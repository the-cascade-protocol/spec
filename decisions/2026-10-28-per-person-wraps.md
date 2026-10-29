# D-KEY-3: Share a Pod with a person by wrapping its data key to that person's public key

**Status:** Proposed, 2026-10-28. Being prototyped in Cascade Appeal under the draft wrap kind `x-draft-hpke-recipient`. Not eligible for ruling until the evaluation below is complete and its results are recorded in this document. Not normative: nothing here changes [`pod-encryption.md`](../pod-encryption.md) until a revision of that document adopts it.
**Date:** 2026-10-28
**Prompted by:** an application in which a patient shares an insurance-appeal case with an advocate or a family member, each signing in with their own passkey, and the patient needs to be able to remove one of them later. The ratified rule for sharing a Pod is to hand over its recovery sheet (D-KEY-2, 2026-09-24). D-KEY-2 left the door open on purpose ("the file format keeps allowing several wraps, so they can be added later without migrating any pod"). This document is the design for walking through it.
**Depends on:** the `webauthn-prf` wrap kind (decision accepted 2026-10-06, revised 2026-10-07; a follow-up is filed to specify it), which this document assumes is specified.

---

## The problem, precisely

Under D-KEY-2 a Pod has one secret, and sharing means giving another person that secret. That is the right model for a Pod on one person's Mac. It falls short when several named people use the same Pod from their own devices:

1. **No individual removal.** Removing one person means changing the secret and handing the new one to everyone who stays.
2. **The secret travels.** The six words are written down, photographed and messaged. Each copy is a full key to the Pod.
3. **No passkey for the second person.** A `webauthn-prf` wrap can only be made by the person whose authenticator produces the PRF output. The owner cannot make one on someone else's behalf.

The goal is that each person opens the Pod with their own passkey, the owner can add someone without that person being present, and the owner can remove one person and leave the others' access intact.

## Decision (proposed)

### 1. Each person has a personal key pair

A person who receives shared Pods holds one long-lived HPKE key pair:

- **Suite:** HPKE base mode ([RFC 9180](https://www.rfc-editor.org/rfc/rfc9180)), `DHKEM(P-256, HKDF-SHA256)` (KEM `0x0010`), `HKDF-SHA256` (KDF `0x0001`), `AES-256-GCM` (AEAD `0x0002`). This is the suite the Full Picture rater envelope already uses, so implementations need one HPKE suite, not two. P-256 rather than X25519 because it is the curve every WebCrypto engine imports (spike 2026-10-06, section 4.3).
- **Public key:** a JWK ([RFC 7517](https://www.rfc-editor.org/rfc/rfc7517), [RFC 7518](https://www.rfc-editor.org/rfc/rfc7518) section 6.2) with exactly `kty: "EC"`, `crv: "P-256"`, `x`, `y`.
- **Key identifier:** the JWK thumbprint ([RFC 7638](https://www.rfc-editor.org/rfc/rfc7638), SHA-256, base64url without padding) of the public key. This is the `kid` used everywhere below, as in the proposed D-PAIR-1 pairing.
- **Private key:** stored as a JWK carrying `d`, `x` and `y` (the public point is required, spike section 4.2), only inside a **personal keyring**: a sealed record whose header has the person's own `webauthn-prf` wrap and, optionally, a `passphrase` wrap (their six words). The private key never exists outside that keyring except in memory.

The personal keyring is the person's, not any Pod's. Losing it (all passkeys and the six words) loses access to every Pod shared with that person, and the owner re-shares.

### 2. A new wrap kind: `hpke-recipient`

```json
{
  "by": "hpke-recipient",
  "label": null,
  "createdAt": "2026-10-28T17:04:11.123Z",
  "kid": "<RFC 7638 thumbprint of recipientKey>",
  "recipientKey": { "kty": "EC", "crv": "P-256", "x": "<base64url>", "y": "<base64url>" },
  "enc": "<base64 of the 65-byte HPKE encapsulated key>",
  "wrappedDek": "<base64 of the 48-byte HPKE ciphertext: data key(32) || tag(16)>"
}
```

- **Sealing:** `SealBase(pkR = recipientKey, info = "cascade-pod-key/hpke-recipient/v1", aad = UTF-8(kid), pt = data key)`.
- **`recipientKey` is in the header** so that a writer holding the data key can re-wrap a new data key to every remaining person during a re-key (section 5 below) without asking them to do anything. A public key is not a secret.
- **Reader validation**, before any key operation: `kid` is 43 base64url characters and equals the thumbprint of `recipientKey`; `recipientKey` has exactly the four members above and is a point on P-256; `enc` decodes to exactly 65 bytes beginning `0x04`; `wrappedDek` decodes to exactly 48 bytes. A failure makes the header malformed (section 5.2), as for any other wrap.
- **Opening:** a reader holding a personal keyring finds the wrap whose `kid` equals its own key's thumbprint and calls `OpenBase`. No match is "this person has no access", not "incorrect secret".
- **Limits:** the kind counts toward the existing 16-wrap limit. Opening it costs one ECDH, so it needs no separate limit.

This maps one-to-one onto JWE key encryption with HPKE (draft-ietf-jose-hpke-encrypt: `alg` `HPKE-0`, `enc` as the encapsulated key, the wrapped data key as the JWE Encrypted Key), so a later JWE serialization of the header is a re-encoding, not a redesign.

### 3. The owner's own wraps are unchanged

The owner opens the Pod with their `webauthn-prf` wrap (and the six-word `passphrase` wrap where the passkey wrap's rules require one). An owner MAY also hold an `hpke-recipient` wrap to their own personal key, which is how one person opens many Pods with one passkey prompt. The writer rule about a passkey wrap being the only wrap applies to the Pod as a whole: a header MUST always have at least one wrap that is not `hpke-recipient`, so that a Pod never depends entirely on other people's keyrings.

### 4. Adding a person: the public key must arrive authenticated

The owner must wrap to the right public key. A storage host that can swap the public key in transit can give itself access. So the key is delivered under a secret the host never sees, in the pattern Full Picture already ships:

1. The owner's app creates an invite: a random 32-byte **link key**, carried only in a URL fragment (`#...`), so the host never receives it.
2. The recipient opens the link, creates or unlocks their personal keyring, and returns their public JWK sealed with AES-256-GCM under `HKDF-SHA256(link key, info = "cascade-pod-key/invite-response/v1")`, with AAD = UTF-8 of the invite identifier.
3. The owner's app opens the response, shows a short confirmation code derived from the thumbprint (the first 4 bytes of the 32-byte thumbprint digest read as a big-endian unsigned integer, mod 10^6, written as 6 digits with leading zeros) that the two people MAY compare, then adds the `hpke-recipient` wrap.
4. The invite is single-use. The host deletes it once the response is collected or after a fixed expiry.

The security of step 2 rests on the link reaching the recipient over a channel the host does not control (a text message, in person). The confirmation code exists for the case where that channel is in doubt.

### 5. Removing a person is a re-key, carried to everyone who stays

[`pod-encryption.md`](../pod-encryption.md) section 6.6 already says removing a wrap is not revocation, and that remains true. Removal of a person is therefore always a re-key (section 7), which this document amends:

- After the re-key, the header holds a new owner wrap (as section 7.1 says today) **plus** one new `hpke-recipient` wrap for every person who keeps access, sealed to the `recipientKey` copied from the old header.
- The person removed loses access to the Pod at this location from that moment. Copies they already made, and plaintext they already read, are beyond reach, and implementations MUST say so (section 7.4).

### 6. Who has access is visible to the host

Each `hpke-recipient` wrap carries a public key and its thumbprint in plaintext. A host can count how many people share a Pod and recognize the same person across Pods. It cannot learn who they are from the header alone. `label` stays `null` or neutral (section 4.3): never a name.

### 7. Consent is recorded separately

A wrap is a capability, not a record of consent. When the consent record of D-CONSENT-1 is built (modeled on FHIR Consent), a grant SHOULD produce one `cascade:ConsentRecord` naming the recipient's `kid`, and a removal SHOULD set its `revokedAt`. This document does not build that record.

## How this relates to D-KEY-2

D-KEY-2 stays the rule for a Pod held by one person on their own devices (the Workbench case): one key, one sheet. This document adds a second, opt-in model for Pods used by several named people through an application that gives each of them a personal keyring. An implementation that does not implement `hpke-recipient` skips those wraps (section 4.3) and opens the Pod with the owner's secret as before.

## Alternatives considered

| Option | Why not |
|---|---|
| Hand over the six words (D-KEY-2 as written) | No individual removal; the secret is copied wherever it is sent. Still the right model for one-person Pods. |
| A one-time link-key wrap of the data key that the recipient converts into their own `webauthn-prf` wrap | Works without a personal key pair, but the owner can only re-key for everyone by sending new links to every remaining person. The data key also sits under a link secret until it is redeemed. |
| JWE (RFC 7516) as the header format now | The same cryptography in a different envelope. Worth doing when D-PAIR-1's sealed envelope lands; not a reason to fork the header format today. |
| X25519 | Not importable in every browser engine at the time of the 2026-10-06 spike. |

## Evaluation before ratification

The specification maintainer ruled on 2026-10-28 that this design must be built, tested and evaluated before it is considered for ratification. The prototype writes the draft kind `x-draft-hpke-recipient` (same members as section 2), so that no stored data claims the final name before its members are settled. Readers skip it as an unknown kind (section 4.3 of `pod-encryption.md`). It renames to `hpke-recipient` only after a ruling.

The evaluation passes when each item below has a recorded result (pass, fail, or changed design) with evidence:

1. **Grant without presence.** The owner adds a person through the invite of section 4; the person opens the Pod with their own passkey on their own device; the owner was not online when the person first opened it.
2. **Removal without the others.** The owner removes one of at least two people; a re-key re-wraps to everyone who stays from the header alone; the people who stay open the Pod with no action; the removed person's keyring no longer opens it.
3. **Key substitution.** A storage host that replaces the public key in the invite response is detected (the response fails to open), and the confirmation code differs when keys differ.
4. **One prompt, many Pods.** A person with access to several Pods opens all of them with one passkey prompt, through their own-key wrap (section 3), with no PRF salt reused across headers.
5. **New device.** A person recovers access on a second device through a synced passkey, and through six words alone.
6. **Validation.** Every rule in section 2's reader validation has a negative test; a reader that does not implement the kind skips it and still opens the Pod with the owner's wrap.
7. **Vectors.** Fixed-ephemeral-key vectors (RFC 9180 Appendix A method) produced by one implementation are reproduced by a second, independent one.
8. **People in the loop.** At least one real invite and one removal done by people other than the builder, with notes on where they hesitated, including whether the confirmation code was read.
9. **Open questions** below each have an answer drawn from the prototype.

## Open questions for the ruling

1. Is the confirmation code (section 4, step 3) shown always, or only on request?
2. Should a personal keyring be a Pod (with its own `settings/encryption.json`) or an application record using the same header? This document assumes the latter, as Full Picture's keyring does.
3. Conformance: vectors for `hpke-recipient` need fixed HPKE ephemeral keys. RFC 9180 Appendix A gives the method; the vectors themselves would be generated with a second implementation, as the `webauthn-prf` vectors were.
