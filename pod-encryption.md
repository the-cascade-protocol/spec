# Cascade Protocol Pod Encryption Specification

**Status:** Draft
**Version:** 1.0
**Date:** 2026-09-26
**Authors:** Cascade Agentic Labs LLC
**Website:** https://cascadeprotocol.org
**Formats specified:** sealed resource format (unversioned, see section 3), encryption header versions `1.0` (read only) and `1.1`

This document specifies how a Cascade Pod is encrypted at rest: the byte layout of an encrypted file, the plaintext header that holds the wrapped data key, what a reader must check before it derives any key, what a writer must never produce, and how a Pod's key is changed. It is the normative home of a format that was previously defined only by its implementations. Where this document and an implementation disagree, the implementation is non-conforming; the conformance repository records each known difference as a failing vector (section 10).

The Pod layout itself (directories, discovery, type indexes) is specified in [`pod-structure.md`](pod-structure.md). Nothing in this document changes it: encrypting a Pod changes file contents, never file names or the graph.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Primitives](#2-primitives)
3. [Sealed Resources](#3-sealed-resources)
4. [The Encryption Header](#4-the-encryption-header)
5. [Reading the Header](#5-reading-the-header)
6. [Writing the Header](#6-writing-the-header)
7. [Changing the Key](#7-changing-the-key)
8. [File System Safety](#8-file-system-safety)
9. [Security Considerations](#9-security-considerations)
10. [Conformance](#10-conformance)

---

## 1. Overview

### 1.1 Envelope encryption

An encrypted Pod uses two keys:

- A random 256-bit **data key** (DEK), one per Pod, seals every encrypted file in the Pod.
- A **key-encryption key** (KEK), derived from a secret the person holds (a passphrase), seals the data key. The sealed data key is a **wrap**.

The wraps, with the parameters needed to derive each KEK, are stored in a plaintext **header** at `settings/encryption.json`. A Pod is encrypted if and only if something is present at that path (section 4.1).

More than one wrap of the same data key may exist, so more than one secret can open the same Pod. Every wrap in a header wraps the same data key.

### 1.2 Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

| Term | Definition |
|------|-----------|
| **Pod root** | The directory that holds the Pod. Pod-relative paths are relative to it. |
| **Sealed resource** | A file whose bytes on disk are the output of section 3.1 under the Pod's data key. |
| **Header** | The file `settings/encryption.json` (section 4). |
| **Wrap** | One entry of the header's `wraps` list: one sealed copy of the data key, and how to open it. |
| **Wrap kind** | The value of a wrap's `by` member. |
| **Reader** | Any implementation that opens an encrypted Pod. |
| **Writer** | Any implementation that creates, modifies or replaces a header or a sealed resource. |
| **Re-wrap** | Replacing one wrap with a wrap of the same data key under a new secret (section 6.5). |
| **Re-key** | Replacing the data key itself and re-encrypting every sealed resource (section 7). |

---

## 2. Primitives

**Authenticated encryption.** AES-256-GCM ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final)) with a 256-bit key, a 96-bit (12-byte) nonce and a 128-bit (16-byte) tag. Every nonce MUST be 12 bytes from a cryptographically secure random number generator, drawn fresh for every seal operation. A nonce MUST NOT be derived from the plaintext, a counter shared between processes, or any other deterministic input. No associated data is used by the formats in this document (section 9.4).

**Key derivation.** Argon2id ([RFC 9106](https://www.rfc-editor.org/rfc/rfc9106)), version `0x13`, with:

- password: the secret, encoded as UTF-8 exactly as entered, with no Unicode normalization, trimming or case folding;
- salt: the wrap's decoded 16-byte salt;
- time cost `t`, memory cost `m` in KiB, parallelism `p`: from the wrap (section 4);
- output length: 32 bytes;
- no secret value (`K`) and no associated data (`X`).

An implementation MUST state every one of these explicitly rather than rely on a library default, because a library that silently differs on any of them derives a different KEK and cannot open the Pod.

**Randomness.** Data keys (32 bytes), salts (16 bytes) and nonces (12 bytes) MUST come from a cryptographically secure random number generator.

**Base64.** Binary values in the header use the standard alphabet with padding ([RFC 4648 section 4](https://www.rfc-editor.org/rfc/rfc4648#section-4)) in canonical form. Section 4.5 defines exactly what is accepted.

---

## 3. Sealed Resources

### 3.1 Layout

A sealed resource is exactly:

```
nonce(12) || ciphertext || tag(16)
```

where `ciphertext` has the same length as the plaintext. This is the layout Apple CryptoKit calls `AES.GCM.SealedBox.combined`. There is no magic number, version byte, or other header on the blob, so a reader cannot tell a sealed resource from random bytes except by authenticating it.

The smallest sealed resource is 28 bytes (an empty plaintext). A file shorter than 28 bytes is never a sealed resource.

A reader MUST open a sealed resource with AES-256-GCM under the Pod's data key and MUST treat any authentication failure as an error. A reader MUST NOT return, parse or display bytes that failed authentication, and MUST NOT fall back to reading them as plaintext.

### 3.2 What is sealed

In an encrypted Pod, every regular file under the Pod root is a sealed resource, whatever its name or extension (Turtle files, `settings/preferences`, `.well-known/solid`, attachments, application containers such as `notes/`), except:

| Pod-relative path | Why it stays plaintext |
|---|---|
| `settings/encryption.json` | The header. It holds the wrapped data key, so it cannot be sealed under that key. |
| `README.md` | A human-facing note describing the directory. It MUST NOT contain health data. |
| `provenance/egress-log.jsonl` | An append-only log of what left the Pod, metadata only by design, written by more than one process. Whole-file authenticated encryption cannot be appended to by two writers. |

Entries whose name begins with `.` are not Pod resources, with one exception: `.well-known` is a Pod container and its files are sealed. Other dot-prefixed entries (version-control metadata, operating-system files, a writer's temporary files) are outside this specification; a writer MUST NOT store Pod content in them.

Adding a path to the plaintext list above is a change to this specification, not an implementation choice: each entry is a file anyone holding the disk can read.

What sealing does not hide: every file and directory **name**, the directory structure, each file's **size** (plaintext length plus 28 bytes), and timestamps. Section 9.2 lists the consequences.

### 3.3 Writing a sealed resource

A writer MUST seal the whole file in one operation with a fresh nonce; sealed resources are never appended to or patched in place.

A writer SHOULD replace a file so that it is never observed half-written: create a new temporary file in the same directory (create-new semantics, so an existing file or link at that name is never opened), write it, flush it to stable storage, rename it over the target, then flush the directory. A truncated sealed resource fails authentication forever, so this is the difference between a crash and data loss.

### 3.4 Sealing an existing Pod

When an implementation encrypts a Pod that was plaintext, or seals plaintext files left inside an encrypted Pod, it has to decide per file whether the file is already sealed. It MUST decide by authentication: a file that authenticates under the Pod's data key is already sealed and MUST be left unchanged. A file that does not authenticate MAY be treated as plaintext to be sealed only if it is shorter than 28 bytes or its bytes are valid UTF-8. Any other file MUST be left unchanged and reported, because it cannot be told apart from a file sealed under a different key, and sealing that a second time destroys it.

### 3.5 Nonce budget

With random 96-bit nonces, NIST SP 800-38D limits one key to 2^32 seal operations. A Pod that approaches that many writes under one data key SHOULD be re-keyed (section 7). No Pod observed in practice comes within several orders of magnitude of it.

---

## 4. The Encryption Header

### 4.1 Location and presence

The header is the file `settings/encryption.json` under the Pod root. It is plaintext.

**A Pod is encrypted if and only if anything is present at the header path**, judged without following a symbolic link: a regular file, a directory, a symbolic link (dangling or not), a FIFO, a device or a socket all make the Pod encrypted. A `settings` directory that is itself a symbolic link also makes the Pod encrypted. Anything at the header path other than a regular file reached without a link is then refused when read (section 5.1), so such a Pod reads as locked, never as a plaintext Pod. Treating an unreadable header as "not encrypted" would lead a writer to store plaintext in a sealed Pod.

The header MUST be encoded as UTF-8 JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) without a byte order mark, and its top-level value MUST be an object.

The order of members in an object is not significant. Writers SHOULD emit the orders shown in the examples below. Writers MUST NOT emit an object with duplicate member names; readers SHOULD refuse one as malformed, and a reader that cannot detect duplicates MUST use the last occurrence.

A reader MUST ignore top-level members it does not know. A reader MUST ignore members it does not know inside a wrap. A writer that carries a wrap it did not create into a new header MUST carry it with all of its members unchanged.

### 4.2 Top-level members

| Member | Type | Rule |
|---|---|---|
| `version` | string | `"1.0"` or `"1.1"`. Any other value, including a differently formatted equivalent such as `"1.10"` or `" 1.1"`, is a version this reader does not know (section 5.4). |
| `algorithm` | string | Exactly `"aes-256-gcm"`, in both versions. Anything else is malformed. |
| `wraps` | array | One or more wrap objects, in both versions. An empty list is malformed. |

Version `1.1` adds nothing at the top level. Version `1.0` has two more top-level members (section 4.4).

### 4.3 Version 1.1

Every writer writes version `1.1`.

```json
{
  "version": "1.1",
  "algorithm": "aes-256-gcm",
  "wraps": [
    {
      "by": "passphrase",
      "label": "primary",
      "createdAt": "2026-09-23T17:04:11.123Z",
      "kdf": "argon2id",
      "kdfParams": { "salt": "<base64 of 16 random bytes>", "t": 3, "m": 65536, "p": 1 },
      "wrappedDek": "<base64 of nonce(12) || sealed data key(32) || tag(16)>"
    }
  ]
}
```

A version `1.1` header MUST NOT carry a top-level `kdf` or `kdfParams` member, whatever its value (`null` included). Key derivation parameters belong to each wrap, because one salt cannot serve two secrets.

**Members of every wrap:**

| Member | Type | Rule |
|---|---|---|
| `by` | string | The wrap kind. MUST be a non-empty string. A wrap with a missing, non-string or empty `by` makes the header malformed. |
| `label` | string or `null` | REQUIRED (present, possibly `null`). Plaintext; see below. |
| `createdAt` | string or `null` | REQUIRED (present, possibly `null`). See below. |

**Members of a `passphrase` wrap**, in addition:

| Member | Type | Rule |
|---|---|---|
| `kdf` | string | Exactly `"argon2id"`. |
| `kdfParams` | object | `salt` (string, section 4.5), `t`, `m`, `p` (numbers, section 4.5). Limits in section 5.3. |
| `wrappedDek` | string | Base64 of the data key sealed under this wrap's KEK with the layout of section 3.1: exactly 60 bytes decoded. |

**Wrap kinds.** `passphrase` is the only kind specified. `device-keychain` is reserved for a future wrap sealed under a device-held key and has no defined members yet. A reader MUST skip a wrap whose kind it does not implement, and MUST NOT read, interpret or validate any member of such a wrap other than `by`, `label` and `createdAt`: a newer writer defines those members, not this reader. A header whose wraps are all of kinds the reader does not implement cannot be opened by that reader (section 5.4), which is a different outcome from malformed.

**`label`.** A short name for the wrap, or `null`. The header is plaintext and travels with every copy of the Pod, so a label MUST NOT contain a person's name or any other identifying or health information. Writers use neutral words; the only label writers currently produce is `"primary"`.

**`createdAt`.** When the wrap was created, as an RFC 3339 UTC timestamp with millisecond precision and a `Z` suffix (for example `2026-09-23T17:04:11.123Z`), or `null` when the wrap's age is unknown (a wrap migrated from version `1.0`). It is set once, when the wrap is created, and never rewritten. Readers MUST check only that it is a string or `null` and MUST NOT refuse a header because the string does not parse as a date.

**Wrap identifier.** A passphrase wrap's public identifier is its `kdfParams.salt` string. Applications that need to refer to one wrap (for example, to record which wrap a printed recovery document opens) use it. Replacing a wrap gives it a new salt and therefore a new identifier. Because salts are 16 random bytes, identifiers do not collide in practice; section 6.2 still forbids a writer from repeating one.

### 4.4 Version 1.0 (read only)

Version `1.0` is the first header format. Writers MUST NOT produce it; readers MUST accept it.

```json
{
  "version": "1.0",
  "algorithm": "aes-256-gcm",
  "kdf": "argon2id",
  "kdfParams": { "salt": "<base64 of 16 bytes>", "t": 3, "m": 65536, "p": 1 },
  "wraps": [
    { "by": "passphrase", "wrappedDek": "<base64 of 60 bytes>" }
  ]
}
```

The top-level `kdf` and `kdfParams` are REQUIRED and are held to the limits of section 5.3 whether or not any wrap uses them. They apply to every `passphrase` wrap. A version `1.0` wrap carries `by` and, for a `passphrase` wrap, `wrappedDek`; it has no `label` or `createdAt`, and any other member is ignored.

A reader reads a version `1.0` header as if it were the version `1.1` header its migration would produce (section 6.4), so the rest of the implementation sees one shape:

- each `passphrase` wrap takes the top-level `kdf` and `kdfParams`;
- the first `passphrase` wrap in list order has `label` `"primary"`; every other wrap has `label` `null`;
- every wrap has `createdAt` `null`;
- each passphrase wrap's identifier is the top-level salt.

A version `1.0` header may hold more than one `passphrase` wrap. They share one salt. A reader accepts it; a writer cannot migrate it (section 6.4).

### 4.5 Lexical rules for numbers and binary values

These rules exist because a header is read by implementations in different languages, whose JSON parsers disagree about values that are not written in the plainest form. The only property two parsers can check the same way is the text itself.

**Numbers.** `t`, `m` and `p` MUST each be a JSON number written as decimal digits only: no sign, no fraction, no exponent, no leading zero, that is, matching `0|[1-9][0-9]*`. A reader MUST refuse the header as malformed when any of them is written in any other form, even when the value denoted is an integer in range: `3.0`, `3e0`, `30e-1`, `-0` and `"3"` (a string) are all refused. A reader MUST NOT coerce.

**Binary values.** `kdfParams.salt` and `wrappedDek` MUST be canonical padded base64 with the standard alphabet: only the characters `A` to `Z`, `a` to `z`, `0` to `9`, `+` and `/`, followed by the `=` padding that makes the length a multiple of four; no whitespace or line break anywhere, including at either end; the URL-safe alphabet (`-`, `_`) is not accepted; unused bits in the last character are zero. Equivalently: decoding strictly and encoding the result again reproduces the string exactly. A reader MUST NOT trim, strip or otherwise repair these strings before checking them, and MUST refuse any other form as malformed. The decoded lengths are fixed: 16 bytes for a salt, 60 bytes for a wrapped data key.

**Names.** `version`, `algorithm`, `kdf` and `by` are compared as exact, case-sensitive strings with no trimming. A `by` of `" passphrase"` is therefore an unimplemented kind, not a passphrase wrap.

---

## 5. Reading the Header

### 5.1 Opening the file

The header is attacker-controlled input: a Pod is a folder anyone can hand to a person, and anyone who can write to the folder can edit the header. A reader MUST:

1. Refuse, without reading through it, a `settings` directory that is a symbolic link.
2. Open the header without following a symbolic link in its final component and without blocking (a FIFO with no writer would otherwise hang the open), or check the kind with a non-following status call first and refuse anything that is not a regular file.
3. Check the kind again on the opened handle and refuse anything that is not a regular file: a directory, FIFO, device, socket or link.
4. Read at most 65,537 bytes whatever size the handle reports (a device reports size 0 and returns bytes forever), and refuse the header if more than 65,536 bytes are available.
5. Refuse bytes that are not valid UTF-8, or that begin with a byte order mark.

Each refusal in this section is a malformed header.

### 5.2 Validate everything before deriving anything

A reader MUST parse the header and check every rule in sections 4 and 5.3, for every wrap it implements, **before it derives any key or allocates memory in proportion to any number in the header**. A violation anywhere refuses the whole header, even when a wrap earlier in the list is valid and would open. The checks MAY run in any order, because the outcome does not depend on it.

A reader MUST NOT ask the person for a secret before this validation has passed and the header has at least one wrap the reader implements, since there is nothing the secret could open.

### 5.3 Limits

A header outside any of these limits is malformed. The limits apply to the version `1.0` top-level parameters and to every version `1.1` passphrase wrap.

| Field | Accepted | Why |
|---|---|---|
| header file | at most 65,536 bytes | a real header is well under 1 KiB |
| wraps of any kind | at most 16 | bounds parsing |
| `passphrase` wraps | at most 6 | bounds the try-each-wrap loop (section 5.5) |
| `kdf` | exactly `"argon2id"` | the only KDF specified |
| `kdfParams.t` | 1 to 6 | writers use 3 |
| `kdfParams.p` | 1 to 4 | writers use 1 |
| `kdfParams.m` (KiB) | `8 * p` to 131,072 (128 MiB) | writers use 65,536 (64 MiB); `8 * p` is the Argon2 minimum |
| `kdfParams.salt` | canonical base64 of exactly 16 bytes | writers use 16 random bytes |
| `wrappedDek` | canonical base64 of exactly 60 bytes | 12-byte nonce, 32-byte data key, 16-byte tag |

The limits bound the cost of opening a hostile header: six wraps at the largest parameters. A reader MUST NOT raise them. A writer MUST NOT produce a header outside them (section 6.2). Changing a limit is a change to this specification.

A refusal message SHOULD name the field and MUST NOT echo the offending value, which is attacker-chosen and can be arbitrarily long.

### 5.4 Outcomes

Every attempt to open a Pod ends in exactly one of these outcomes. A reader SHOULD let its caller tell them apart, because they call for different actions.

| Outcome | When | What it tells the person |
|---|---|---|
| **unsupported version** | `version` is a string other than `"1.0"` and `"1.1"` | a newer tool wrote this Pod; update the tool |
| **malformed** | any other rule in sections 4, 5.1 or 5.3 is broken, including a missing or non-string `version` | the header is damaged or hostile; no secret was tried |
| **cannot open** | the header is valid and holds no wrap of a kind this reader implements | this reader has no way in; no secret was tried |
| **incorrect secret** | the header is valid, and no implemented wrap opened with the secret given | the secret is wrong (section 5.5) |
| **opened** | a wrap opened | the data key is available |

The first three outcomes MUST be reached without any key derivation. A reader MUST NOT report any of them as an incorrect secret, and MUST NOT report any outcome other than **opened** as a Pod with no records.

### 5.5 Opening

To open with a secret, a reader tries each `passphrase` wrap in list order: derive the KEK with that wrap's own parameters, open `wrappedDek` with it (section 3.1), and stop at the first wrap whose tag verifies. The decrypted value MUST be exactly 32 bytes; it is the data key. If no wrap verifies, the outcome is **incorrect secret**.

Every wrap in a header wraps the same data key, so which wrap opened does not change what the reader can decrypt. A reader MUST accept a header in which two wraps share a salt (it tries both), even though writers never produce one.

A reader that caches a data key between operations MUST discard the cached key when the header on disk changes, because a re-key (section 7) replaces the data key and a writer using a stale key would seal new files under a key the Pod no longer holds.

---

## 6. Writing the Header

### 6.1 Always version 1.1

A writer MUST write version `1.1`. A writer that modifies a version `1.0` header MUST migrate it (section 6.4) and write the result as version `1.1`.

### 6.2 Invariants

A writer MUST NOT write a header that a conforming reader would refuse. In particular, every header a writer produces:

- has at least one wrap. A header with no wraps makes the Pod unopenable by anyone, so no operation may remove the last wrap;
- has no two passphrase wraps with the same salt;
- has a fresh 16-byte random salt for every passphrase wrap it creates;
- is inside every limit of section 5.3;
- has neutral labels only (section 4.3);
- has a `createdAt` on every wrap it creates, and leaves `createdAt` unchanged on every wrap it carries over.

The default parameters for a new passphrase wrap are `t = 3`, `m = 65536`, `p = 1`.

### 6.3 Writing the file

The header SHOULD be written the same way as a sealed resource (section 3.3): a new temporary file in `settings/` created with create-new semantics, written, flushed, renamed over `settings/encryption.json`, and the directory flushed. A crash then leaves either the old header or the whole new one, never a truncated header over a Pod whose files are sealed.

When the write replaces an existing header, the writer SHOULD read the temporary file back, open it with the new secret, and confirm it yields the same data key before the rename. After the rename the old secret no longer opens the live Pod, so this is the last point at which a mistake is recoverable.

A writer MUST NOT leave a copy of an earlier header inside the Pod: an old header in the live folder keeps the old secret working against it. A temporary header left by an interrupted write is not the header, is never read as one, and SHOULD be removed by the next write to `settings/`. It can hold a wrap of the data key, so it MUST NOT be carried into a re-keyed Pod (section 7).

### 6.4 Migration from 1.0 to 1.1

Migration happens in memory, as part of a write, and never on read. The top-level `kdf` and `kdfParams` move into the `passphrase` wrap, whose `label` becomes `"primary"` and `createdAt` becomes `null`. Every other wrap is carried over with `label: null`, `createdAt: null` and its other members unchanged. The top-level `kdf` and `kdfParams` are then removed.

A version `1.0` header with two or more `passphrase` wraps cannot be migrated: its wraps share one salt, and version `1.1` requires distinct salts. A writer MUST refuse to migrate it and leave it unchanged. Such a Pod can still be read, and can be re-keyed (section 7), which writes a fresh version `1.1` header.

### 6.5 Re-wrap

A re-wrap replaces one wrap with a wrap of the **same** data key under a new secret. The writer:

1. opens the header with the current secret and notes which wrap opened;
2. migrates a version `1.0` header (section 6.4);
3. replaces the wrap that opened with a new `passphrase` wrap: fresh salt, the default parameters, `createdAt` now, `label` kept from the replaced wrap or `"primary"` if it was `null`;
4. keeps every other wrap exactly as it was;
5. writes the result as in section 6.3.

A writer MUST refuse a re-wrap when the current secret opens no wrap, and MUST leave the header byte-identical when it refuses. No sealed resource is read or written, and the data key never touches disk.

### 6.6 Removing a wrap is not revocation

A wrap can be removed, or replaced by a re-wrap, but **neither revokes anyone**. Whoever opened the Pod through that wrap has held the data key, and the data key still opens every sealed resource, including every copy of the Pod made before the change. Every copy of a Pod also carries its own header, so a copy made before a re-wrap still opens with the old secret.

Only a re-key (section 7) cuts off someone who has held the data key, and only for the Pod it is applied to. An implementation MUST NOT describe removing or replacing a wrap as revoking access. An implementation that offers a single "change the key" action to a person, in a model where one secret opens a Pod, MUST implement that action as a re-key.

---

## 7. Changing the Key

A re-key replaces the Pod's data key and seals every sealed resource again under the new one. It is the only operation that revokes a secret or a data key someone may have kept (section 6.6).

### 7.1 What a re-key produces

After a successful re-key:

- the header is version `1.1` with exactly **one** passphrase wrap, of a new random data key, under the new secret: fresh salt, `createdAt` now, `label` kept from the wrap the current secret opened, or `"primary"`;
- no other wrap is carried over: the secrets behind them are not available to re-wrap the new key, and dropping them is the revocation;
- every file that authenticated under the old data key has been opened and sealed again under the new one, with a fresh nonce;
- every other file (the plaintext files of section 3.2, and any file that did not authenticate under the old key) is byte-for-byte unchanged. A re-key never changes whether a file is sealed.

A re-key MUST NOT start unless the current secret opens the header. It MUST refuse, before writing anything, a Pod that contains a symbolic link or any entry that is neither a regular file nor a directory anywhere below the Pod root (section 8), and a Pod containing a file it cannot read.

### 7.2 Never in place

A re-key MUST NOT rewrite the Pod in place, because a crash part way would leave files under two keys and a header for only one. It MUST build a complete re-encrypted copy, verify it, and swap it in:

1. **Stage.** Create a new directory beside the Pod, in the same parent directory (so the final renames stay on one file system), named `.<pod-name>.rekey-<token>`, where `<pod-name>` is the Pod directory's own name and `<token>` is 12 lowercase hexadecimal digits from a random source. Create it with create-new semantics: never adopt a directory already at that name. Recreate every directory; write every file, sealed or copied as section 7.1 says, each through a durable write (section 3.3); write the new header **last**, so the copy is never a complete Pod before its files are. Flush every file and every directory.
2. **Verify.** Before anything moves, prove from what is on disk that: the new secret opens the copy's header to the new data key; the copy holds exactly the expected files and directories; every re-sealed file decrypts to the same plaintext as its original (for example, by comparing digests); every copied file is byte-identical to its original. Then confirm that nothing in the Pod changed while the copy was built (file set, sizes, modification times, identities). Any failure deletes the copy and leaves the Pod untouched.
3. **Swap.** Rename the Pod to `.<pod-name>.old-<token>` (the same token), rename the copy to `<pod-name>`, and flush the parent directory. **The second rename is the commit point.** If the second rename fails, rename the old Pod back.
4. **Clean up.** Delete the `.old` directory. It is the last place the old data key opens anything in this location. A failure to delete it after the commit point MUST NOT be reported as a failed re-key: the new secret is now the only one that opens the Pod, and a caller told "failed" might discard it. It SHOULD be reported alongside the success and removed by a later recovery (section 7.3).

A re-key MUST NOT hold the data keys longer than it needs them, and MUST NOT write either data key to disk.

### 7.3 Recovery from an interrupted re-key

A process that dies during a re-key leaves directories beside the Pod whose names say how far it got, paired by their shared token. An implementation that finds them MUST resolve them before it re-keys the Pod again, and SHOULD resolve them before writing to the Pod at all. Recovery needs no secret.

| Directories present | Interrupted | Recovery | Secret that opens the Pod afterwards |
|---|---|---|---|
| the Pod, and `.<name>.rekey-<token>` | while staging or verifying | delete the copy | the **current** one |
| `.<name>.old-<token>` and `.<name>.rekey-<token>`, no Pod | between the two renames | rename `.old` back to the Pod, then delete the copy | the **current** one |
| the Pod, and `.<name>.old-<token>` | after the commit point | delete `.old` | the **new** one |

Only real directories whose names match exactly, with a 12-digit lowercase hexadecimal token, are considered. Any other combination (a copy with no Pod and no `.old`; a Pod, an `.old` and a copy of the same token; more than one `.old`) is not a state a conforming re-key leaves. An implementation MUST NOT resolve it automatically and MUST report the directories involved.

The invariant this preserves: **at every moment, exactly one of the two secrets opens the directory at the Pod's path, and no file is lost.** A caller that did not see the result of a re-key that was interrupted after its commit point should try the new secret when the current one is refused.

### 7.4 What a re-key cannot do

A re-key protects the Pod at this location only. A copy made before it, anywhere (a backup, a synced folder, a folder shared with someone), carries its own header and its own copy of the old data key, and still opens with the old secret. An implementation MUST NOT claim otherwise.

A write that lands in the Pod after the final verification in step 2 and before the first rename in step 3 is not detected. Implementations SHOULD stop their own writes to a Pod while its key is being changed.

---

## 8. File System Safety

**Symbolic links are never followed inside a Pod.** Not the header, not a sealed resource, not a directory during a walk, not a directory a write would create. A reader or writer MUST check every existing component of a Pod-relative path without following links and refuse a path that contains one. As an independent second check, a path whose resolved location is outside the Pod root MUST be refused. The Pod root itself MAY be reached through a link (a folder moved to another disk); only what is inside the Pod is held to this rule. An implementation MAY refuse to re-key a Pod whose own path is a symbolic link.

Pod-relative paths MUST NOT be absolute and MUST NOT contain `..` components.

**Only regular files are resources.** A walk of the Pod (to seal, decrypt, re-key or list it) MUST skip or refuse anything that is neither a regular file nor a directory, and a read of a single resource MUST refuse one, without blocking: a FIFO would hang the reader and a device can return bytes without end. A re-key refuses them outright (section 7.1), because a file the copy silently left out would be lost when the old directory is deleted.

---

## 9. Security Considerations

### 9.1 What the format is for

The format protects the **confidentiality** of a Pod's contents against someone who holds a copy of its folder but not a secret that opens it, and protects readers against a **hostile folder**: a Pod whose files someone else wrote must not be able to hang, crash, or exhaust the memory of a reader, extract a key, or make a reader write outside the Pod (sections 5 and 8). It is not designed to protect a Pod from someone who can write to it; destroying data inside a Pod is always possible for such a writer.

### 9.2 What is visible without a secret

The header (every wrap's kind, label, creation time, salt, KDF parameters, and the number of wraps), the three plaintext files of section 3.2, every file and directory name, the directory structure, file sizes and timestamps. Names and sizes can reveal the kinds of records a Pod holds, and roughly how many. Attachments are named by the digest of their plaintext ([`pod-structure.md`](pod-structure.md) section 4.3), so someone who already holds a document byte-for-byte can learn whether a Pod holds it.

### 9.3 Offline guessing

The header is a complete offline guessing target: anyone with a copy can try secrets against a wrap at the cost of one Argon2id derivation per guess, with no rate limit. The KDF parameters raise that cost; they cannot make a weak secret strong. A secret with high entropy (for example, six words drawn uniformly from a 7,776-word list, about 77 bits) makes guessing infeasible. An implementation that lets a person choose their own secret SHOULD say that its strength is the Pod's protection.

Section 2 forbids normalizing the secret. Two devices that produce different Unicode sequences for what a person thinks of as the same text (composed and decomposed accents, for example) derive different keys. Implementations that generate secrets SHOULD use ASCII.

### 9.4 No associated data: swapped and rolled-back files are accepted

Sealed resources use no associated data, so authentication proves only that a file was sealed under this Pod's data key at some point. It does not prove that the file is the current content of the path it is found at. Anyone who can write to the Pod folder can therefore, without any secret:

- copy one sealed resource over another (for example, one record file over another), and
- restore an earlier sealed version of a file from an older copy of the same Pod,

and every conforming reader accepts the result as authentic. Nothing in the current format detects either. The header is not authenticated either, but an edit to it cannot yield a different data key without a secret that opens a wrap: it is refused, or fails to open, or opens the same key.

This is a known limitation of this version of the format. The ratified design that binds each sealed resource to its path and format version, with an analysis of which kinds of rollback can and cannot be detected without state kept outside the Pod, is in [`decisions/2026-09-26-sealed-resource-binding.md`](decisions/2026-09-26-sealed-resource-binding.md). Until a revision of this specification adopts it, applications SHOULD NOT present an encrypted Pod's contents as tamper-evident against someone who can write to its folder.

### 9.5 Header limits

Without the limits of section 5.3, one edited number in a header could make every reader allocate gigabytes or compute for hours before the secret was even checked, and a reader that opens every Pod it knows about when it starts would repeat that on every start. The limits bound the cost of the worst header to a few seconds of work per open. Section 5.1 exists for the same reason: a header path that is a device or a FIFO defeats a size check made before opening.

### 9.6 Key material in memory

Implementations SHOULD overwrite data keys, KEKs and the encoded secret as soon as they are no longer needed, and SHOULD NOT keep a second copy of an unwrapped key (including the plaintext produced before a tag check completes). Languages whose strings cannot be overwritten cannot meet this for the secret itself; such implementations SHOULD at least overwrite the encoded bytes passed to the KDF.

### 9.7 Copies

Every copy of a Pod is independently openable with the secrets that opened it when it was copied. Re-wraps and re-keys change only the Pod they are applied to (sections 6.6 and 7.4).

---

## 10. Conformance

Cross-implementation fixtures live in the [`conformance`](https://github.com/the-cascade-protocol/conformance) repository under `pod-encryption/`:

- **positive fixtures**: sealed resources and headers produced by independent implementations, in versions `1.0` and `1.1`, with the test-only secrets that open them. A conforming reader opens every one and decrypts it to the stated plaintext; a conforming writer's output opens in every other implementation.
- **negative header vectors**: one per refusal rule in sections 4, 5.1 and 5.3, each with its expected outcome (section 5.4).
- **acceptance vectors**: headers a reader MUST accept, for the rules that tell a reader what not to refuse.
- **file system vectors**: layouts built at test time (links, FIFOs, devices), since a repository cannot carry them portably.

An implementation that reads or writes this format SHOULD run them in its own test suite. A vector an implementation is known to fail is listed, with the implementation that owns the fix, in that directory's `KNOWN_FAILURES.json`.

