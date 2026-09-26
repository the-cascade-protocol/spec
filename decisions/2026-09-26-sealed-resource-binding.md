# D-SEAL-1: Bind each sealed resource to its path, and say what rollback protection a Pod can have

**Status:** Proposed. Not normative. Nothing here changes the format in [`pod-encryption.md`](../pod-encryption.md) until a maintainer rules on the options below and a revision of that document adopts them.
**Date:** 2026-09-26
**Decision needed from:** the specification maintainer (Jed Reinitz)
**Prompted by:** a security review of both implementations of the Pod encryption format, which showed that a sealed file copied over another sealed file, or replaced by an older sealed copy of itself, is accepted as authentic by every reader. [`pod-encryption.md`](../pod-encryption.md) section 9.4 states the limitation; this document is the design it points to.

---

## The problem, precisely

Every sealed resource in a Pod is `nonce || ciphertext || tag` under the one Pod data key, with a random nonce and **no associated data** (AAD). GCM authentication therefore proves one thing: these bytes were sealed under this Pod's key at some point. It does not prove any of the following, and nothing else in a Pod does either:

1. **Place.** That the file is at the path it was written for. `clinical/allergies.ttl` copied over `clinical/medications.ttl` opens without complaint.
2. **Time.** That the file is the latest version written to its path. Yesterday's `clinical/medications.ttl` from a backup, put back in place, opens without complaint and shows a stopped medication as active.
3. **Completeness.** That no file is missing. A deleted record file reads as a Pod with fewer records.

The actor is anyone who can write to the Pod folder but holds no secret: a shared or synced folder, a backup restored by someone else, a Pod handed over as a zip. Destroying data is always possible for that actor and is out of scope. **Presenting tampered or outdated records as authentic** is in scope, because a reader cannot tell the person anything is wrong.

## What can and cannot be achieved without state outside the Pod

This is the constraint every option below lives inside, so it comes first.

A Pod is a folder. Anything a reader can check about it, it checks against other bytes in the same folder. An actor who holds an **entire earlier copy** of the folder (header, every sealed file, any index) can put all of it back at once, and the result is a Pod that was, at some moment, exactly what an honest writer produced. No check that reads only the folder can tell that Pod from the real one, because at the moment it was copied it *was* the real one.

So the achievable properties split cleanly:

| Tampering | Detectable from the folder alone? |
|---|---|
| a file moved or copied to another path | **yes**, by binding each file to its path (Part A) |
| one file, or several, rolled back while the rest of the Pod is newer | **yes**, by an authenticated index (Part B) |
| a file deleted, or an old file re-added under a path the index no longer lists | **yes**, by the same index |
| the **whole** Pod rolled back to one consistent earlier copy | **no**. Only state kept outside the folder can detect it (Part C), and only on a device that saw the newer state |

Anything that promises the last row without external state is wrong, and the specification should say so rather than imply it.

---

## Part A: bind each sealed resource to its path and format

### A1. The binding (recommended)

Seal every resource with GCM associated data:

```
AAD = "cascade-pod-resource" || 0x00 || format || 0x00 || path
```

- `format` is the ASCII decimal sealed-resource format number: `2` for this format. (The current, unbound format is format 1 in retrospect.)
- `path` is the Pod-relative path of the file as UTF-8: `/` separators, no leading `/` or `./`, no `..`, and the name bytes exactly as they are stored in the directory (no case folding or Unicode normalization is applied by the reader; a writer uses the name as it will be listed).
- The fixed prefix is domain separation, so this AAD can never coincide with one any other Cascade format uses.

The layout on disk does not change: still `nonce(12) || ciphertext || tag(16)`, still no magic number. Cost at runtime is negligible: GCM authenticates a few dozen more bytes per file.

What it buys: a file opens only at the path it was sealed for. Every cross-path swap in the problem statement fails authentication. What it does not buy: an older version of the **same** path still opens (Part B).

Consequences to accept:

- **A path is part of a file's identity.** Renaming or moving a sealed file inside a Pod means opening it and sealing it again under the new path. [`pod-structure.md`](../pod-structure.md) already forbids renaming attachments on encryption, and Pod-managed names are generated identifiers and digests, so this touches little. Moving the **Pod folder** as a whole changes nothing, because paths are relative to the Pod root.
- **Names must survive transport byte for byte.** A tool that rewrites file names on the way (an archiver that changes Unicode normalization, a case-insensitive copy that changes case) breaks every file whose name it rewrote. Pod-managed names are ASCII today; the revision adopting this should make that a writer rule for any name a writer generates.

### A2. How a reader knows which format a Pod uses (recommended: Pod-wide, in the header)

There is no per-file marker, and a reader must not guess, so the format has to be declared somewhere a reader reads first: the header.

**Proposed:** header version `1.2`, identical to `1.1` plus a required top-level member `"resourceFormat": 2`. A Pod is entirely format 1 or entirely format 2, never mixed:

- a reader that knows `1.2` opens every sealed resource with the A1 binding and never tries without it;
- a reader that only knows `1.0` and `1.1` refuses a `1.2` header as an unsupported version and tells the person to update the tool, which is the correct failure. (Declaring the format only in a new member of a `1.1` header would be wrong: a `1.1` reader ignores unknown members, would try every file without AAD, and would report every file as undecryptable instead.)
- editing the header back to `1.1` does not downgrade anything: the files are format 2, so without the binding none of them opens. That is data destruction, which was already possible.

**Rejected alternative: a per-file version prefix,** allowing a Pod to hold both formats during a gradual migration. It keeps an unbound path open for as long as any format 1 file might exist, and an actor can always supply one: put back an old format 1 file from a backup and a reader that still accepts format 1 accepts it, bound to nothing. Closing that needs a Pod-wide statement that no format 1 file remains, which is the header declaration above with extra steps.

**Rejected alternative: try with the binding, fall back to none, re-seal on the next write.** Same flaw, permanently: the fallback is exactly the unbound path an attacker needs.

### A3. Migration: it rides the re-key

The re-key in [`pod-encryption.md`](../pod-encryption.md) section 7 already opens every sealed file, seals it again under a new data key, builds the result in a staging copy, verifies it, and swaps it in with one commit point. Sealing under format 2 instead of format 1 is a change to the seal step and the header it writes, nothing else. So:

- a Pod moves from `1.1` to `1.2` in one atomic step, with the same crash recovery, and is never mixed;
- the same machinery serves a **format upgrade without a new secret**: a re-key whose new secret is the current one. The current re-key refuses an unchanged secret because its purpose was revocation; the revision would allow it when the purpose is an upgrade, and should say that such an upgrade is not a revocation;
- implementations SHOULD upgrade when the person next changes the key, and MAY offer the upgrade on its own;
- `1.1` Pods stay readable indefinitely. Nothing is forced.

Copies of a Pod made before the upgrade stay format 1 and remain open to the swaps above. That is the same property as a re-key not reaching old copies.

### A4. What A needs from each implementation

Every reader and writer of the format changes in the same release (the TypeScript command-line tool, the desktop application, and any SDK that adopts the format), since an old reader cannot open an upgraded Pod. The conformance repository gains `1.2` positive fixtures and negative vectors: a sealed file copied to another path is refused; a `1.2` file opened without the binding is refused; a `1.2` header without `resourceFormat` is malformed.

---

## Part B: detect mixed versions inside a Pod

### B1. An authenticated index (recommended as the second step, not now)

A sealed index file (name to be chosen, under `settings/`) lists every sealed resource: its path and a per-path write counter. The index carries a Pod-wide generation number and is itself sealed with the A1 binding. Each resource's AAD additionally carries its write counter, so a file and the index entry for it must agree. Readers compare the two:

- a file whose counter is **lower** than its index entry has been rolled back: refuse it;
- a file the index lists that is **missing** has been deleted: report it;
- a sealed file the index does **not** list was never written by a writer that kept the index: refuse it;
- an index older than the files it describes is detected the same way, from the files' side.

What this cannot catch is the last row of the table above: the index and every file restored together from one earlier copy.

### B2. Why it is not the first step

The hard part is not cryptography. It is that **every write becomes two writes** (the file and the index), and a Pod has more than one writer: two applications, or two processes of one, can write to the same Pod, and the plaintext egress log exists precisely because of that. B1 therefore needs:

- a write protocol that survives a crash between the two writes without looking like an attack. One workable shape: record the intent (path and new counter) in the index first, then write the file, then commit the index. A file ahead of the index is legitimate only if the index names it as pending, so a genuinely rolled-back index is still detected;
- a rule for concurrent writers, which means either a lock the implementations agree on or an index structure that merges;
- a decision on which files are covered. The plaintext files of `pod-encryption.md` section 3.2 cannot be, since they are not sealed.

Those belong with the multi-writer and second-keyholder design, not bolted on here. Recommended: decide B1 in principle now, design it there.

---

## Part C: detect whole-Pod rollback (optional, application level)

The only way to detect a consistent earlier copy is to remember something newer somewhere the actor cannot write. With B1 in place, an application can keep, per Pod and per device, the highest index generation it has seen, in the operating system's protected store (the same place it keeps the Pod's key). On open, a lower generation means the folder has been rolled back or replaced with an earlier copy.

Limits, which the specification should state wherever this is offered:

- it protects only on a device that has seen the newer state. A new device, or a person opening a Pod they were just given, has nothing to compare against;
- a legitimate restore from backup looks identical to an attack, so the person needs a way to accept an older Pod deliberately, and the warning has to explain what they are accepting;
- it is not portable: two devices each have their own memory.

This is a property of an application, not of the Pod format. The specification can describe it as optional behavior and must not describe a Pod as rollback-proof.

---

## Options

| Option | Stops cross-path swaps | Detects partial rollback and deletion | Detects whole-Pod rollback | Cost |
|---|---|---|---|---|
| **0. Status quo** | no | no | no | none; [`pod-encryption.md`](../pod-encryption.md) section 9.4 already discloses it |
| **1. Part A** (path and format binding, header `1.2`, migration by re-key) | yes | no | no | small: one header version, one seal change, every implementation in one release |
| **2. Parts A and B** (plus the authenticated index) | yes | yes | no | large: write protocol, crash rules, multi-writer coordination |
| **3. Parts A, B and C** (plus a per-device anchor) | yes | yes | on devices that saw the newer state only | 2, plus application work and a restore flow |

## Recommendation

1. **Adopt option 1 now.** It is cheap, closes the most direct attack (one record file presented as another), and its migration is the re-key that already exists, so no Pod is ever in a mixed state.
2. **Accept option 2 in principle and design Part B with the multi-writer and second-keyholder work**, where the concurrency question it depends on is already being answered.
3. **Leave option 3 to applications**, described in the specification as optional and bounded, never as a property of the Pod.
4. In every case, keep the explicit statement that no format can detect a consistent earlier copy of a whole Pod from the folder alone.

## Open questions for the ruling

- Is a format upgrade that keeps the same secret (A3) acceptable, or must the upgrade wait for the person's next key change?
- Should the header itself be bound too? Today anyone can edit labels or remove wraps; neither yields a key, but both change what a person is shown. A digest of the header inside the B1 index would detect it; nothing in option 1 does.
- The ASCII rule for writer-generated names (A1): specify it with option 1, or separately?
