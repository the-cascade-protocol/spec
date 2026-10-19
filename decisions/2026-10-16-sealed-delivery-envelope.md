# D-PAIR-1: One pairing and one sealed envelope for moving records into a Pod

**Status:** Proposed. Not ratified. Normative text, once ratified: [`sealed-envelope.md`](../sealed-envelope.md) (draft 0.2).
**Date:** 2026-10-16
**Proposed by:** the specification maintainer
**Prompted by:** two applications that must hand records to a desktop application's Pod without anything in between being able to read them: a web application that has collected answers in a browser, and a phone application. Both were to use the same mechanism. The direction was set earlier as an application design decision (the receiver shows a one-time key as a QR code or a link; the sender seals to it and deposits the result in a relay mailbox; the key never comes from a server). This record formalizes it as a protocol format.

---

## Decision (proposed)

1. **One envelope, two routes.** An envelope is a JWE Compact Serialization ([RFC 7516](https://www.rfc-editor.org/rfc/rfc7516)), `typ` `cascade-sealed-envelope+jwe`, `cty` `zip`. Route a seals it to a pairing key; route b seals it under a key wrapped by the Pod's six-word key. The JWE `alg` says which.
2. **Route a uses HPKE Integrated Encryption in JWE**, `alg` `HPKE-7`: DHKEM(P-256, HKDF-SHA256), HKDF-SHA256, AES-256-GCM, base mode ([RFC 9180](https://www.rfc-editor.org/rfc/rfc9180); [draft-ietf-jose-hpke-encrypt](https://datatracker.ietf.org/doc/draft-ietf-jose-hpke-encrypt/)). HPKE `info` is `cascade-sealed-envelope/v1`; the AAD is the encoded protected header; `kid` is the RFC 7638 thumbprint of the pairing key.
3. **Route b uses `dir` with `A256GCM`** ([RFC 7518](https://www.rfc-editor.org/rfc/rfc7518)), the content key carried as a [`pod-encryption.md`](../pod-encryption.md) version 1.1 header in the critical protected header parameter `cascade-header`. The six-word key derivation is the Pod's own `passphrase` wrap (Argon2id, t = 3, m = 64 MiB, p = 1), not a second one.
4. **The pairing is a small JSON object** carried after `#` in a link and shown as a QR code: `v`, `exp` (RFC 7519 NumericDate), `cnf.jwk` (RFC 7800, a P-256 public JWK), `mbx` (16-byte mailbox id), `pod` (16-byte Pod reference, minted once per Pod and reused in every pairing for it, never the Pod identifier and never derived from it). People compare an 8-character fingerprint taken from the key's thumbprint: the receiver always shows it, and a sender must show it and have the person confirm the match before sealing whenever the pairing reached it by any route other than its own camera scanning the receiver's screen.
5. **The receiver's key is one-time** and stored as a JWK with `d`, `x` and `y`. It is deleted as soon as one envelope authenticates, or 24 hours after expiry.
6. **The bundle is a store-only ZIP** under ISO/IEC 21320-1 with further restrictions that remove every option a reader could interpret two ways. Completeness is the bundle manifest's job (for an assessment bundle, SPDX file declarations with SHA-256 checksums, and an attachment's `cascade:contentHash` equal to its file's checksum); the envelope adds no digests.
7. **Related to SMART Health Links, not built on it.** The saved file uses the SMART Health Links JWE file profile (`dir`, `A256GCM`) and the pairing link shares its payload shape and its `exp` and `v`. Route a is not a SMART Health Link, because that format puts the decryption key in the link, runs in the opposite direction and has no content type for a Turtle bundle. SMART Health Links is the intended route for sharing with clinicians and outside tools, specified separately.
8. **Room for signing.** A later revision may carry a signature inside the bundle (sign, then seal) without changing the envelope format. This version specifies none.

## Why these choices

**Reuse before invention.** Every construct was checked against ratified standards first; [`sealed-envelope.md`](../sealed-envelope.md) section 3 lists each with its standard or the reason it is new. Four things are new: the pairing members `v`, `mbx` and `pod`; the `typ` value; the `cascade-header` parameter; the short fingerprint rendering and the `.cpseal` extension.

**JWE over a custom binary format.** A first draft of this design used a compact binary layout of its own. It worked, but every field in it had a standard equivalent. JWE costs about a third more bytes on the wire (base64url) and a larger QR code (version 14 rather than 9 at error correction M); both are affordable for bundles under a few MiB and a code shown on a computer screen.

**JWE over COSE.** COSE with HPKE ([draft-ietf-cose-hpke](https://datatracker.ietf.org/doc/draft-ietf-cose-hpke/)) is in IETF Last Call with its algorithm and header code points still unassigned, so it is less stable than the JOSE document, which the IESG has approved. COSE would also need a CBOR library in every implementation, including Swift, where none ships with the platform.

**P-256 over X25519.** Both work in every target engine. P-256 is native in every browser's WebCrypto and in Apple CryptoKit, and it is the curve of the first sealed format already in use in this ecosystem, so implementations keep one code path. The cost is the key storage rule (some browser engines refuse a P-256 private key without its public point, so the stored JWK must carry `x` and `y`) and a slightly larger QR code.

**Base mode, not auth or PSK mode.** The sender has no key the receiver knows on first contact, so auth mode has nothing to authenticate with. A PSK carried in the pairing would add nothing: whoever has the pairing would have the PSK too, and the relay already cannot seal to a key it never sees.

**The Pod's own six-word wrap for route b.** JOSE's only password-based mechanism is PBES2 (PBKDF2). With a 77-bit six-word secret PBKDF2 would be adequate, but it would give the protocol two derivations from one secret, and every implementation already has the Argon2id wrap with conformance vectors.

**ZIP over tar or MIME multipart.** ZIP has a registered media type and an ISO profile, and a deterministic store-only ZIP writer already exists in this ecosystem. Store-only removes decompression bombs; the remaining restrictions remove the ambiguities (central directory against local headers, data descriptors, extra fields, ZIP64) that make ZIP readers disagree.

## Consequences

- Senders and receivers need HPKE (base mode, P-256), JWK handling, Argon2id and a strict ZIP reader. Each target platform has them: WebCrypto with an HPKE library in browsers, CryptoKit on Apple platforms, the RustCrypto `hpke`, `argon2` and `aes-gcm` crates in a Rust desktop application.
- The format depends on an IETF document that is approved but not yet an RFC. The bytes do not: the suite, `info`, AAD and segment layout are all fixed in this specification. When the RFC is published, the citation changes, not the format.
- A sealed format already in use for a different purpose (answers sealed from one browser to another inside one application) uses the same HPKE suite and key storage rule but its own binary layout and `info`. It is application-internal and does not need to change; it is not an implementation of this format.
- The relay mailbox (deposit, collect and delete, retention, logging) is specified separately. This record requires of it only one deposit per mailbox and opaque storage.

## Conformance

Deterministic vectors are in [`vectors/sealed-envelope/vectors.json`](../vectors/sealed-envelope/vectors.json): 2 receivers, 2 pairings, 17 pairing negatives, 3 positive envelopes and 39 envelope negatives. Before publication they were checked by four implementations:

1. the reference generator (`@hpke/core` 1.9.0 on Node 22, `hash-wasm` for Argon2id), which produced them;
2. an implementation of RFC 9180 and the JWE processing written out by hand in Python over the `cryptography` package's primitives, with `argon2-cffi`. It first reproduces RFC 9180 appendix A.3.1, opens messages sealed by OpenSSL's HPKE for this suite, and opens the `HPKE-7` JWE test vector of draft-ietf-jose-hpke-encrypt (appendix A.13). It then re-seals every positive vector from its inputs, character for character, opens it, and refuses every negative vector with the published outcome;
3. Apple CryptoKit (`HPKE.Recipient`, `P256_SHA256_AES_GCM_256`), which opens both route a positive vectors, refuses the seven cryptographic route a negatives, and seals a fresh envelope that implementations 1 and 2 open;
4. the Rust `hpke` crate 0.14.1, which opens both route a positive vectors and refuses the same seven negatives.

## Draft 0.2 (2026-10-19)

Draft 0.2 changes no byte of any positive vector and no decision above. It settles reader rules that two independent implementations read differently: the pairing key's members are exactly `kty`, `crv`, `x` and `y`; `v` is checked as written; an archive needs at least one entry and the central directory's version needed is checked too; a missing `kid` (route a) and a missing `enc` (route b) are malformed; a `cascade-header` version `1.0` is malformed and an unknown one unsupported; the pairing key is deleted when an envelope authenticates, whatever the bundle then holds; the stored-key rule forbids rebuilding the stored point, not HPKE's own `Decap`; and section 7.4 names how a file is matched to its attachment, makes refusing undeclared files a MUST and requires exactly one `assessment:BundleManifest`. Five pairing negatives and eight envelope negatives were added.

## Questions for the ruling (answered 2026-10-16)

The maintainer answered each question on 2026-10-16; the specification text above reflects the answers. The record stays Proposed until it is ratified.

1. Adopt `HPKE-7` in JWE now, while its document awaits publication, or wait for the RFC number? **Answered: adopt now.** The specification fixes every byte itself (section 11.6).
2. Should a sender be required, not only recommended, to show the fingerprint when the pairing arrived by a copied link rather than a camera? **Answered: required.** The receiver always shows it; a sender must show it and have the person confirm the match before sealing when the pairing arrived by any route other than its own camera scanning the receiver's screen; after a camera scan it stays recommended (sections 4.3 and 11.4).
3. Pairing lifetime: 1 hour recommended, 24 hours maximum. Right numbers? **Answered: yes,** with the key deleted after one envelope (section 4.6).
4. The Pod reference: minted once per Pod and reused, or fresh for every pairing? **Answered: once per Pod,** still never derived from the Pod identifier (section 4.4).
5. The saved-file extension `.cpseal`. **Answered: `.cpseal`** (section 8).

## Standards

[RFC 9180](https://www.rfc-editor.org/rfc/rfc9180) (HPKE); [draft-ietf-jose-hpke-encrypt](https://datatracker.ietf.org/doc/draft-ietf-jose-hpke-encrypt/) (HPKE in JWE); [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515), [RFC 7516](https://www.rfc-editor.org/rfc/rfc7516), [RFC 7517](https://www.rfc-editor.org/rfc/rfc7517), [RFC 7518](https://www.rfc-editor.org/rfc/rfc7518), [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519), [RFC 7638](https://www.rfc-editor.org/rfc/rfc7638), [RFC 7800](https://www.rfc-editor.org/rfc/rfc7800), [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725) (JOSE); [RFC 9106](https://www.rfc-editor.org/rfc/rfc9106) (Argon2); [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) (base64url, base32); [HL7 SMART Health Cards and Links IG](https://hl7.org/fhir/uv/smart-health-cards-and-links/links-specification.html) 1.0.0, STU (SMART Health Links); [SPDX 2.3](https://spdx.github.io/spdx-spec/v2.3/) (file checksums); [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) (URI fragments); [ISO/IEC 21320-1:2015](https://www.iso.org/standard/60101.html) and the [PKWARE APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT) (ZIP).
