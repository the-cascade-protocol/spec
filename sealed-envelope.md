# Cascade Protocol Sealed Delivery Envelope Specification

**Status:** Draft, proposed (see [`decisions/2026-10-16-sealed-delivery-envelope.md`](decisions/2026-10-16-sealed-delivery-envelope.md)); not ratified
**Version:** 0.1
**Date:** 2026-10-16
**Authors:** Cascade Agentic Labs LLC
**Website:** https://cascadeprotocol.org
**Formats specified:** pairing payload `v` 1, sealed envelope `typ` `cascade-sealed-envelope+jwe` (one version)

This document specifies how one application hands a bundle of records to another application's Pod so that nothing in between can read it: a **pairing** the receiving application shows as a QR code or a link, a **sealed envelope** the sending application makes for that pairing, and a **saved file** form of the same envelope that opens with the Pod's six-word key instead. It also specifies how the bundle inside is framed and how a receiver checks that it arrived whole.

It defines as little as it can. The envelope is a JSON Web Encryption object; the pairing key is a JSON Web Key; the encryption is HPKE; the six-word key derivation is the one [`pod-encryption.md`](pod-encryption.md) already specifies; the bundle is a ZIP archive. Section 3 lists every construct with the standard it reuses or the reason it is new.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Terminology](#2-terminology)
3. [Standards Reused](#3-standards-reused)
4. [The Pairing](#4-the-pairing)
5. [The Receiver's Key](#5-the-receivers-key)
6. [The Envelope](#6-the-envelope)
7. [The Bundle Inside](#7-the-bundle-inside)
8. [The Saved File](#8-the-saved-file)
9. [Delivery Through a Relay](#9-delivery-through-a-relay)
10. [Outcomes](#10-outcomes)
11. [Security Considerations](#11-security-considerations)
12. [Conformance](#12-conformance)

---

## 1. Overview

### 1.1 Two routes, one envelope

A **sender** holds records (for example, answers collected in a browser, or entries kept on a phone). A **receiver** holds a Pod (for example, a desktop application). Two routes move a bundle from the sender to the receiver's Pod:

- **Route a, pairing.** The receiver makes a one-time key pair and shows a pairing (section 4) as a QR code or a copyable link. The sender reads it, seals the bundle to the pairing's public key with HPKE (section 6.3), and deposits the envelope in a relay mailbox (section 9). The receiver collects it, opens it, and the relay deletes its copy.
- **Route b, saved file.** The sender seals the bundle under a random content key wrapped by the Pod's six-word key (section 6.4) and the person carries the file. The receiver opens it with the six words.

Both routes produce a JWE Compact Serialization ([RFC 7516](https://www.rfc-editor.org/rfc/rfc7516)) with the same `typ`, the same `cty`, the same payload framing (section 7) and the same reading rules. Only the key management differs, and the JWE `alg` says which. A route a envelope may also be saved to a file and carried by hand (section 8); it opens only with the pairing's private key.

### 1.2 What it protects

The relay, and anyone who holds the envelope without the key that opens it, learns no record content. Section 11 lists what each party can and cannot see.

### 1.3 Requirements language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

---

## 2. Terminology

| Term | Definition |
|------|-----------|
| **Sender** | The application that seals a bundle. |
| **Receiver** | The application that holds the destination Pod, makes pairings, and opens envelopes. |
| **Pairing** | The JSON object of section 4, shown by the receiver: a one-time public key, a mailbox id, a Pod reference and an expiry. |
| **Pairing key** | The one-time P-256 key pair a receiver makes for one pairing. |
| **Envelope** | A JWE Compact Serialization as specified in section 6. |
| **Bundle** | The plaintext of an envelope: a ZIP archive (section 7). |
| **Mailbox** | A relay address that holds envelopes for one pairing until the receiver collects them (section 9). |
| **Six-word key** | The secret that opens a Pod's `passphrase` wrap ([`pod-encryption.md`](pod-encryption.md) section 4.3). |

---

## 3. Standards Reused

A construct in this document is new only when no ratified standard defines it. Status is the IETF or ISO status on the date of this document.

| Construct | Reused standard (status) | New, and why |
|---|---|---|
| Hybrid public key encryption | HPKE, [RFC 9180](https://www.rfc-editor.org/rfc/rfc9180) (RFC, Informational, IRTF CFRG) | none |
| Suite: DHKEM(P-256, HKDF-SHA256), HKDF-SHA256, AES-256-GCM | RFC 9180 identifiers `0x0010`, `0x0001`, `0x0002`; named `HPKE-7` by [draft-ietf-jose-hpke-encrypt](https://datatracker.ietf.org/doc/draft-ietf-jose-hpke-encrypt/) (approved, in the RFC Editor queue) | none |
| Envelope container | JWE Compact Serialization, [RFC 7516](https://www.rfc-editor.org/rfc/rfc7516) (Proposed Standard) | none |
| HPKE inside JWE (route a) | Integrated Encryption, `alg` `HPKE-7`, draft-ietf-jose-hpke-encrypt section 5 (approved, not yet an RFC) | none; section 11.6 states the dependency on a document not yet published |
| Content encryption (route b) | `alg` `dir`, `enc` `A256GCM`, [RFC 7518](https://www.rfc-editor.org/rfc/rfc7518) sections 4.5 and 5.3 (Proposed Standard) | none |
| Six-word key derivation and wrap | [`pod-encryption.md`](pod-encryption.md) `passphrase` wrap: Argon2id, [RFC 9106](https://www.rfc-editor.org/rfc/rfc9106) (RFC, Informational) | none |
| Carrying the wraps in the envelope | JWE private header parameter, RFC 7516 section 4.3, marked critical with `crit`, [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515) section 4.1.11 | the parameter name `cascade-header`: JOSE registers no password-based mechanism using Argon2id (only PBES2 with PBKDF2, RFC 7518 section 4.8), and reusing the Pod's own wrap keeps one six-word derivation across the protocol |
| Explicit envelope type | `typ`, RFC 7516 section 4.1.11; practice of [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725) section 3.11 | the value `cascade-sealed-envelope+jwe`: no registered value names this content |
| Content type | `cty` `zip`, RFC 7516 section 4.1.12, for the registered media type [`application/zip`](https://www.iana.org/assignments/media-types/application/zip) | none |
| Public key in the pairing | JWK, [RFC 7517](https://www.rfc-editor.org/rfc/rfc7517) and [RFC 7518](https://www.rfc-editor.org/rfc/rfc7518) section 6.2 (Proposed Standard), inside `cnf`, [RFC 7800](https://www.rfc-editor.org/rfc/rfc7800) section 3.2 (Proposed Standard) | none |
| Expiry | `exp` as a NumericDate, [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) section 4.1.4 (Proposed Standard) | none |
| Mailbox id, Pod reference, pairing version | none found | members `mbx`, `pod`, `v`: a relay mailbox and a Pod reference are Cascade concepts no registry defines |
| Key identifier | `kid` = JWK Thumbprint, [RFC 7638](https://www.rfc-editor.org/rfc/rfc7638) (Proposed Standard) | none |
| Fingerprint for people to compare | RFC 7638 thumbprint, rendered in base32, [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) section 6 | the truncation to 40 bits and the `XXXX-XXXX` grouping: no standard defines a short human comparison string for a JWK |
| Binary-to-text in links and envelopes | base64url without padding, RFC 4648 section 5, as RFC 7515 section 2 uses it | none |
| Link carrying the pairing | URI fragment, [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) section 3.5 | the `pair.` prefix, so a page that reads other fragments can tell this one apart |
| Receiver private key storage | JWK with `d`, `x`, `y`, RFC 7518 section 6.2.2 | none |
| Bundle framing | ZIP, [PKWARE APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT) as profiled by [ISO/IEC 21320-1:2015](https://www.iso.org/standard/60101.html) (International Standard), further restricted (section 7.2) | none; the restrictions only remove options |
| Per-file digests and completeness | the bundle's own manifest (section 7.4); for assessment bundles, the `assessment:` vocabulary's file declarations | none in this document |
| Duplicate JSON member names | refused, as [`pod-encryption.md`](pod-encryption.md) section 4.1 does; [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) section 4 leaves them undefined | none |
| Saved file name extension | none registered for a JWE | `.cpseal`: an operating system needs a distinctive extension to hand the file to the right application |

Considered and not used: COSE with HPKE ([draft-ietf-cose-hpke](https://datatracker.ietf.org/doc/draft-ietf-cose-hpke/), in IETF Last Call, its code points still unassigned), which would also need a CBOR library in every implementation; OpenPGP ([RFC 9580](https://www.rfc-editor.org/rfc/rfc9580)), which covers both routes but brings its own key formats and is not available natively in the target platforms; CMS ([RFC 5652](https://www.rfc-editor.org/rfc/rfc5652)); tar and MIME multipart for the bundle, rejected for ZIP because ZIP has a registered media type, an ISO profile and an existing deterministic writer in this ecosystem.

---

## 4. The Pairing

### 4.1 The object

A pairing is a JSON object ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) encoded as UTF-8:

```json
{
  "v": 1,
  "exp": 1792000000,
  "cnf": { "jwk": { "kty": "EC", "crv": "P-256", "x": "<base64url, 32 bytes>", "y": "<base64url, 32 bytes>" } },
  "mbx": "<base64url, 16 bytes>",
  "pod": "<base64url, 16 bytes>"
}
```

| Member | Rule |
|---|---|
| `v` | The pairing format version: the JSON number `1`. A reader MUST refuse any other integer as **unsupported** and a missing or non-integer value as **malformed**. |
| `exp` | When the pairing stops being usable, as a NumericDate (RFC 7519 section 2): integer seconds since 1970-01-01T00:00:00Z. |
| `cnf` | An object holding `jwk` (RFC 7800 section 3.2): the pairing key's public half as a P-256 JWK with exactly `kty` `EC`, `crv` `P-256`, `x` and `y`. It MUST NOT carry `d`. |
| `mbx` | The mailbox id (section 9): 16 random bytes, base64url without padding. |
| `pod` | The Pod reference (section 4.4): 16 bytes, base64url without padding. |

Readers MUST ignore members they do not know. Writers SHOULD emit the members in the order shown and MUST NOT emit whitespace. A pairing object in which any JSON object holds the same member name twice is **malformed**, as in [`pod-encryption.md`](pod-encryption.md) section 4.1.

### 4.2 The link and the QR code

The receiver shows the pairing as a URI whose fragment ([RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) section 3.5) is `pair.` followed by the base64url encoding, without padding, of the pairing's UTF-8 bytes:

```
https://<sender application origin>/<path>#pair.<base64url(pairing)>
```

The origin and path are the sender application's, chosen by that application; this document does not fix them. Everything after `#` stays on the device that opens the link: browsers do not send a fragment to the server. **The pairing key reaches the sender only through this fragment, from the receiver's own screen or link. A sender MUST NOT accept a pairing key from a server**, because a server that supplies the key can supply its own.

The same URI is shown as a QR code and offered as a link to copy. With an origin of about 30 characters the URI is about 340 characters, which fits a QR code of version 14 at error correction level M (73 by 73 modules). A receiver SHOULD draw it at least 240 CSS pixels wide.

### 4.3 The fingerprint

The **kid** of a pairing is the JWK Thumbprint (RFC 7638, SHA-256) of `cnf.jwk`, base64url without padding. The **fingerprint** is the first 5 bytes of that thumbprint encoded in base32 (RFC 4648 section 6, alphabet `A`-`Z` `2`-`7`, no padding), 8 characters, shown as two groups of four separated by a hyphen, for example `K7QM-2XRD`.

A receiver SHOULD show the fingerprint beside the QR code and the link. A sender SHOULD show it before sealing. The person compares them when the link has travelled through anything other than their own camera (section 11.4).

### 4.4 The Pod reference

`pod` lets a sender recognize the destination ("the same record as last time") without learning anything about the Pod. It MUST NOT be `cascade:podIdentifier` ([`decisions/2026-09-26-pod-identifier.md`](decisions/2026-09-26-pod-identifier.md)) and MUST NOT be derived from it. A receiver mints it as 16 random bytes, either once per Pod and kept with the Pod, or fresh for every pairing. A sender MUST NOT treat it as an identifier of a person.

### 4.5 What the sender checks

Before sealing, a sender MUST:

1. strip `#pair.`, decode the base64url strictly (only the RFC 4648 section 5 alphabet, no padding, no whitespace, unused bits zero; decoding and re-encoding reproduces the text) and the bytes as UTF-8;
2. parse the JSON, refusing duplicate member names;
3. check `v`, then that `exp` is an integer, `cnf.jwk` is a P-256 public JWK without `d` whose `x` and `y` decode to 32 bytes each and name a point on the curve, and `mbx` and `pod` decode to 16 bytes each;
4. refuse the pairing as **expired** when its clock reads `exp` or later, and as **malformed** when `exp` is more than 86,400 seconds (24 hours) after its clock.

### 4.6 What the receiver does

A receiver MUST make a fresh pairing key for every pairing and MUST NOT reuse one across pairings. It SHOULD set `exp` to 1 hour after it makes the pairing and MUST NOT set it more than 24 hours after. It keeps the private half (section 5) only until it has opened one envelope for the pairing, or until 24 hours after `exp`, whichever comes first, and then deletes it. A pairing is single use: one envelope per pairing.

A pairing moves data to the receiver. It never moves a key to the sender: a sender holds only the public half.

---

## 5. The Receiver's Key

The pairing key is generated by a cryptographically secure generator (for example WebCrypto `generateKey` with `ECDH` on `P-256`, or RFC 9180 `DeriveKeyPair` from 32 random bytes). A receiver that stores the private half, including inside an encrypted store, MUST store it as a JWK (RFC 7518 section 6.2.2) carrying `kty`, `crv`, `d`, `x` and `y`, each coordinate and `d` exactly 32 bytes before encoding.

A reader MUST refuse a stored key that lacks `x` or `y`, and MUST NOT rebuild the public point from `d` or choose `y` from `x`. Two engines that rebuild the point differently derive different HPKE key schedules (the encoded public key is an input) and cannot open each other's envelopes; some browser engines also refuse to import a P-256 private key that does not carry its public point. A reader MUST check that the stored `x` and `y` equal the pairing's `cnf.jwk`.

---

## 6. The Envelope

### 6.1 Common rules

An envelope is the JWE Compact Serialization of RFC 7516 section 7.1: five base64url segments separated by four `.` characters, ASCII only, with no whitespace anywhere. Its JWE Protected Header (the first segment) is UTF-8 JSON with no duplicate member names and holds at least:

| Member | Value |
|---|---|
| `alg` | `HPKE-7` (route a) or `dir` (route b). |
| `typ` | Exactly `cascade-sealed-envelope+jwe`. Another string is **unsupported**; a missing `typ` is **malformed**. |
| `cty` | Exactly `zip` (the payload is `application/zip`, section 7). |

Writers MUST put `alg` first, then `typ`, so that every envelope begins with the same characters; this is the envelope's signature for tools that sniff content (section 8). Writers MUST NOT use the JWE JSON Serialization, a JWE AAD, or unprotected headers. The Additional Authenticated Data of the content encryption is ASCII of the first segment as written (RFC 7516 section 5.1 step 14), so a header re-encoded in any way, even with the same members in another order, no longer opens.

An envelope MUST NOT exceed 44,870,336 characters, which is a 32 MiB bundle (section 7.3) after base64url plus 128 KiB for the rest. A reader MUST check the length before decoding.

### 6.2 Algorithm

Every envelope uses AES-256-GCM. Route a uses it through HPKE with DHKEM(P-256, HKDF-SHA256) and HKDF-SHA256 (RFC 9180 suite `0x0010`, `0x0001`, `0x0002`; JOSE `HPKE-7`); route b uses it directly (`A256GCM`). The suite is fixed by this version: there is nothing to negotiate, so there is nothing to downgrade (section 11.7).

P-256 is chosen over X25519 because every target engine has it natively, including every browser's WebCrypto and Apple CryptoKit, and it is the curve the first sealed format in this ecosystem already uses, so one code path serves both. Its cost is a larger QR code (the JWK carries `y`) and the key storage rule of section 5.

### 6.3 Route a: sealed to a pairing (`alg` `HPKE-7`)

Integrated Encryption as specified by draft-ietf-jose-hpke-encrypt section 5, with these choices:

- **HPKE mode:** base (`mode_base`). The protected header MUST NOT carry `psk_id`, `enc` or `crit`.
- **`kid`:** REQUIRED: the pairing's kid (section 4.3). A receiver selects the pairing by it and MUST refuse an envelope whose `kid` names no pairing it holds as **cannot open**.
- **HPKE `info`:** the ASCII bytes `cascade-sealed-envelope/v1`. The draft allows mutually known information in place of its empty default; this value separates envelopes of this format from any other use of HPKE.
- **HPKE `aad`:** ASCII of the encoded protected header (draft section 7.1 step 15).
- **Segments:** the protected header; the encapsulated key (`enc`, the 65-byte uncompressed point); empty; the HPKE ciphertext (bundle plus 16-byte tag); empty.

```
<protected header>.<enc>..<ciphertext>.
```

The receiver MUST check the header (6.1 and this section), the stored key (section 5), and that the encapsulated key decodes to 65 bytes, then call HPKE `Open` once. A failure of `Open` is **not authentic**.

### 6.4 Route b: opened with the six-word key (`alg` `dir`)

JWE with `alg` `dir` and `enc` `A256GCM` (RFC 7518 sections 4.5 and 5.3). The 32-byte content encryption key is a data key wrapped exactly as a Pod's data key is: the protected header carries a [`pod-encryption.md`](pod-encryption.md) version `1.1` header as the value of the critical private parameter `cascade-header`:

```json
{
  "alg": "dir",
  "typ": "cascade-sealed-envelope+jwe",
  "cty": "zip",
  "enc": "A256GCM",
  "crit": ["cascade-header"],
  "cascade-header": {
    "version": "1.1",
    "algorithm": "aes-256-gcm",
    "wraps": [
      {
        "by": "passphrase",
        "label": "primary",
        "createdAt": "2026-10-16T00:00:00.000Z",
        "kdf": "argon2id",
        "kdfParams": { "salt": "<base64 of 16 bytes>", "t": 3, "m": 65536, "p": 1 },
        "wrappedDek": "<base64 of 60 bytes>"
      }
    ]
  }
}
```

- `crit` MUST be exactly `["cascade-header"]`, so a generic JOSE library that does not know the parameter refuses the envelope rather than looking for a shared key elsewhere.
- `cascade-header` is read under every rule of [`pod-encryption.md`](pod-encryption.md) sections 4 and 5 (version, limits, lexical rules, unknown wrap kinds skipped, validation before any derivation), and opened as section 5.5 says: the KEK is Argon2id (RFC 9106) over the six words with the wrap's own parameters; the unwrapped value is the content encryption key. The six words are used exactly as entered, with no trimming or normalization (`pod-encryption.md` section 2).
- A writer MUST include at least one `passphrase` wrap. It MAY include other wrap kinds a sender's own application uses (for example a passkey wrap); a receiver skips kinds it does not implement. An envelope with no `passphrase` wrap is **cannot open** for a reader that implements only `passphrase`.
- The content encryption key is either a fresh random 32-byte key with a new wrap (fresh salt, default parameters), or a data key the writer already holds together with its existing wraps, carried unchanged. It MUST NOT be a Pod's data key (section 11.8).
- Segments: the protected header; empty (no encrypted key with `dir`); a 12-byte random IV; the ciphertext; the 16-byte tag. A reader MUST refuse any other IV or tag length as **malformed**.

Because the protected header is the AAD, the wraps are bound to the content: an edit to any wrap member, a label included, makes the envelope **not authentic**, even though such an edit cannot yield a different key.

### 6.5 Reading order

A reader MUST, in this order: check the length; split into exactly five segments; decode the first strictly and parse it with duplicate-name refusal; check `typ`, `cty` and `alg`; route by `alg` (`HPKE-7` to section 6.3, `dir` to section 6.4, anything else **unsupported**); validate everything that route names before deriving any key or calling `Open`; then decrypt; then read the bundle (section 7). An implementation that only implements one route MUST report the other route's `alg` as **cannot open**, not **unsupported**.

---

## 7. The Bundle Inside

### 7.1 A ZIP archive

The plaintext of every envelope is one ZIP archive (`application/zip`). A receiver opens it only after the envelope has authenticated, so its structure is never parsed from unauthenticated bytes.

### 7.2 The profile

The archive is a ZIP file under ISO/IEC 21320-1, further restricted so that every reader parses it the same way and a writer's output is the same bytes for the same files:

1. Every entry is stored (compression method `0`). No deflate, so no decompression bomb.
2. Version needed to extract is `20` (writers) or `10` or `20` (readers); general purpose flags are `0` (no encryption, no data descriptor, no UTF-8 flag); no extra fields; no file comments; no archive comment; no ZIP64; one disk.
3. Each local header is followed immediately by its data; the central directory follows the last file's data, and the end of central directory record follows the central directory and ends the archive. Nothing else is present.
4. Each central directory entry repeats its local header's flags, method, CRC-32, sizes and name, and points at that local header. A reader MUST refuse any disagreement.
5. The CRC-32 of each entry MUST match its data.
6. Entries are files only (no directory entries). Paths are ASCII, at most 255 bytes, made of `/`-separated segments, each matching `[A-Za-z0-9_][A-Za-z0-9._-]*` (so no empty, `.` or `..` segment and no leading `/`).
7. Entries appear in strictly ascending byte order of path, which also forbids a path appearing twice. No path may be a leading folder of another path (`a` and `a/b.txt`).
8. Writers set the modification date and time to 1980-01-01 00:00 and external attributes to `0`. Readers ignore both.
9. At most 256 entries.

A reader MUST refuse an archive breaking any of these as **malformed bundle**.

### 7.3 Size

The bundle MUST NOT exceed 33,554,432 bytes (32 MiB). There is no chunking: the envelope is one AEAD message (HPKE single-shot, or one `A256GCM` encryption), authenticated as a whole before any file in it is read. A bundle of rating forms, a few Turtle files and a packet PDF is well under 1 MiB. A transport MAY split an envelope's bytes for upload; that is the relay's concern, not this format's.

### 7.4 Completeness

The envelope's authentication proves the archive arrived exactly as sealed. Whether the archive holds what it should is the bundle's own manifest's job, and this document adds no digests of its own:

- An **assessment bundle** has `manifest.ttl` at the root, typed `assessment:BundleManifest`, declaring every other file with its path, SHA-256 and byte count (the `assessment:` vocabulary). A receiver MUST check every declared file is present with the declared length and digest, and SHOULD refuse files the manifest does not declare.
- Other bundle kinds name their manifest in their own specification.

The receiver identifies the bundle kind from its manifest's type, not from the envelope.

---

## 8. The Saved File

A saved file is an envelope (either route) written as its ASCII text, with no trailing newline required (a reader strips at most one trailing `\n` or `\r\n`). Its name SHOULD end in `.cpseal`; its media type is `application/jose` (RFC 7515 section 9.2.1). Because writers put `alg` and `typ` first (section 6.1), a file begins `eyJhbGciOiJ`; a tool that needs to tell a saved file from other content checks that prefix and then parses the header.

A route b file opens with the six words in any receiver. A route a file opens only in the receiver that holds the pairing key, which covers carrying a sealed envelope by hand when no relay is wanted.

---

## 9. Delivery Through a Relay

The relay's routes, storage and retention are specified separately. This document requires only:

- A mailbox is addressed by `mbx`, 16 random bytes, unguessable. Knowing `mbx` is what allows a deposit; collecting and deleting require a credential the receiver holds and that is not in the pairing.
- A mailbox accepts one envelope. A second deposit is refused, so an envelope cannot be silently replaced.
- The relay stores the envelope as opaque bytes and deletes it when the receiver confirms collection, or when its retention ends.

---

## 10. Outcomes

Every attempt to read a pairing or open an envelope ends in exactly one of these.

| Outcome | When |
|---|---|
| **usable** / **opened** | The pairing passed section 4.5 / the envelope authenticated and its bundle passed section 7.2. |
| **unsupported** | A version, `typ`, `alg`, `enc` or curve this reader does not implement. Tells the person to update the application. |
| **malformed** | Any structural rule of sections 4.5, 6.1, 6.3 or 6.4 broken. No key was derived. |
| **expired** | The pairing's `exp` has passed (sender side). |
| **cannot open** | Valid, but this reader holds no key that could open it: an unknown `kid`, a stored key that is not the pairing's, a route this reader does not implement, or no `passphrase` wrap. No key was derived. |
| **incorrect secret** | Route b: no `passphrase` wrap opened with the six words given. |
| **not authentic** | The content did not authenticate: a wrong key, a changed header, a changed or truncated ciphertext, a changed tag. |
| **malformed bundle** | The envelope opened but its ZIP broke section 7.2. |

A reader MUST NOT return, parse or show any byte that failed authentication.

---

## 11. Security Considerations

### 11.1 What the relay sees

The relay sees the mailbox id, the envelope's size and timing, the network addresses of the sender and the receiver, and the protected header: `alg`, `typ`, `cty`, and, for route a, the `kid`. The `kid` is a hash of a one-time public key and links nothing beyond the mailbox the relay already knows. The relay never sees the pairing, the public key, the Pod reference or any record. The size reveals roughly how much was sent; this version does not pad.

### 11.2 What the relay cannot do

It cannot read an envelope: it has no pairing private key. It cannot forge one that opens: sealing needs the pairing's public key, which reaches the sender only in the fragment (section 4.2) and is never sent to the relay. An envelope that opens therefore proves only that its sender held the pairing; it does not identify the sender (base mode has no sender authentication).

### 11.3 Replay

An envelope sealed to one pairing is refused by every other pairing (its `kid` and key differ), so it cannot be replayed into another mailbox. Deposited again into the same mailbox it is refused by the single-deposit rule, and after the receiver has opened one envelope it holds no key for that pairing. Imports themselves SHOULD be idempotent, so opening the same bundle twice changes nothing.

### 11.4 A photographed or substituted code

Someone who photographs the QR code learns the public key and the mailbox. They cannot read anything sealed to it. They can deposit their own envelope first, which the single-deposit rule then lets through and which blocks the real one. A receiver MUST show what arrived (who and what the bundle says it is) before writing it into the Pod and let the person refuse it; a real sender whose deposit is refused tells the person to start again with a new code.

Someone who substitutes the code (a doctored link, a forwarded message) can make the sender seal to their key. Scanning the receiver's own screen with the sender's camera is the strong channel; a copied link is weaker, which is why the fingerprint (section 4.3) exists. The 40-bit fingerprint is fresh for every pairing, so an attacker would have to find a key matching it within the pairing's lifetime.

### 11.5 Key lifetime and forward secrecy

HPKE makes a new ephemeral key for every envelope, and the receiver deletes the pairing private key after one use (section 4.6). A copy of an envelope kept by anyone, the relay included, becomes unreadable for good once the pairing key is deleted, even if the receiver's device is later compromised.

### 11.6 Dependence on a document not yet published

`HPKE-7` and Integrated Encryption are defined by an IETF document approved for publication but not yet an RFC. The cryptography underneath is RFC 9180 and the container is RFC 7516, so a change before publication can only rename or renumber, not change the bytes this document fixes: the suite, the `info`, the AAD and the segment layout are all stated here. A revision of this document will cite the RFC when it is published.

### 11.7 Downgrade

There is no negotiation. A receiver accepts exactly `HPKE-7` or `dir` with `A256GCM`, and the HPKE key schedule binds the suite identifiers in any case. A pairing names one curve; a sender either supports it or refuses. An attacker who could change the pairing in transit could substitute the key outright, which section 11.4 covers.

### 11.8 Route b

A saved file is an offline guessing target exactly like a Pod header (`pod-encryption.md` section 9.3): Argon2id per guess, no rate limit, and six words drawn from 7,776 give about 77 bits. Its content key must not be a Pod's data key: a file opened by someone with the six words would otherwise hand them the key to every sealed file in every copy of that Pod. A file sealed under the key of the store it was exported from (section 6.4) exposes that store's key to whoever opens the file; that is the same set of people who can open the store with the same wraps.

### 11.9 Code delivered by a server

A sender that is a web page runs code its server delivers. A server operator who changes that code can read records before they are sealed. This format cannot prevent that; serving the page without third-party scripts and with Subresource Integrity narrows it. Applications MUST NOT claim more than "our server cannot read what it stores".

---

## 12. Conformance

Deterministic vectors are in [`vectors/sealed-envelope/vectors.json`](vectors/sealed-envelope/vectors.json): two receivers (fixed `ikm`, RFC 9180 `DeriveKeyPair`, the stored JWK, `kid`, fingerprint); two pairings; three positive envelopes (route a with a fixed ephemeral `ikm`, and route b with fixed salt, nonces and keys), each with its bundle files and ZIP bytes; and negative vectors with their expected outcome (section 10): pairing negatives (version, curve, off-curve point, a private key in the pairing, expiry, encoding, duplicate members) and envelope negatives (wrong AAD, wrong `info`, truncation, tampered tag and encapsulated key, replay into another mailbox, a different key under the same `kid`, unsupported `alg` and `typ`, IV and header rules, every ZIP profile rule, wrong and untrimmed six words, an edited wrap, no `passphrase` wrap, a missing `crit`).

A conforming implementation re-seals each positive vector from its inputs where its HPKE library accepts a fixed ephemeral key, opens every positive vector to the stated files, and refuses every negative vector with the stated outcome. The vectors were cross-checked by independent implementations before publication; the decision record names them. They move to the conformance repository when this document is ratified.
