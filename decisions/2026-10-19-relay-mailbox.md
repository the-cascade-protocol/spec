# D-RELAY-1: A relay mailbox that holds one sealed envelope for hours, and never a key

**Status:** Proposed. Not ratified. Normative text, once ratified: [`relay-mailbox.md`](../relay-mailbox.md) (draft 0.3).
**Date:** 2026-10-19
**Proposed by:** the specification maintainer
**Prompted by:** route a of the sealed delivery envelope ([`sealed-envelope.md`](../sealed-envelope.md), D-PAIR-1, proposed), which hands an envelope from a sender to a receiver through a relay and specifies only three things about it: one deposit per mailbox, opaque storage, and a collect and delete credential that is not in the pairing. Everything else about the relay (its routes, what it stores, for how long, what it logs) was left to a separate document. This is that document. The routes, the token hashing, the rate limiting and the logging rules follow an existing sealed mailbox, already built and deployed, that carries encrypted answers between browsers, generalized from many deposits per request to one envelope per pairing.

---

## Decision (proposed)

1. **The receiver creates the mailbox, before it shows the pairing,** with `PUT /mailboxes/{mbx}` and `If-None-Match: *` ([RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) section 13.1.2), giving the pairing's `exp` and the SHA-256 of a collect token. A taken id is `412`. If creation fails, no pairing is shown.
2. **The collect token is minted by the receiver**: 32 random bytes, kept with the pairing's private key and deleted with it, sent only as an [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750) bearer token on collect and delete. The relay stores only its hash. It never appears in the pairing.
3. **A deposit is a create-only `PUT`** of the envelope as `application/jose`, also with `If-None-Match: *`. A second deposit is `412`, and its problem details say whether the body is byte for byte the stored envelope (`identical`), so a sender whose first response was lost knows it was delivered and a sender who was beaten knows it was not. A stored envelope is never replaced.
4. **The relay checks shape only**: five base64url segments, a protected header that is a JSON object with the envelope's `typ` and a string `alg`, a non-empty ciphertext. It never checks `alg`'s value, `kid` or the route, and judges no cryptography.
5. **Collecting does not delete; deleting does.** The receiver collects (`GET`, bearer), stores the envelope on its own device, then deletes the mailbox (`DELETE`, bearer), before it opens the envelope or asks the person anything. Delete is idempotent, and also cancels a pairing nothing was deposited for.
6. **Lifetime is tied to the pairing.** Deposits are accepted until `exp`. The retention end is `exp` plus 24 hours, the same moment by which the receiver must have deleted the pairing's private key, after which no copy could ever be opened. Serving stops at once on delete or retention end; every stored copy, soft-deleted objects and backups included, is gone within 24 hours after that. No envelope stays in a relay longer than about 72 hours after its mailbox was made. A closed mailbox keeps a record with no envelope until the retention end, so a late deposit is refused rather than recreating the mailbox.
7. **Logs hold no identifiers and nothing from an envelope**: no `mbx`, token, hash, header value, envelope byte, envelope length or protected header member, no expiry, no network address. Platform request logs, which record addresses and paths, are turned off or excluded.
8. **Refusals are [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details,** with six Cascade problem types where the status code alone is ambiguous (`no-mailbox`, `not-deposited`, `already-deposited`, `expired`, `closed`, `malformed-envelope`) and `about:blank` everywhere else. Polling is paced by `Retry-After`; rate limits answer `429` with `Retry-After`.
9. **The relay's address is configuration.** The pairing carries `mbx` and no relay URL; both sides use the relay of the application the pairing link is made for. Paths are defined under a deployment-chosen base URL, as [RFC 8820](https://www.rfc-editor.org/rfc/rfc8820) section 2.3 allows.

## Why these choices

**Reuse before invention.** Every construct was checked against ratified standards first; [`relay-mailbox.md`](../relay-mailbox.md) section 3 lists each. Two things are new: the two path templates (under a deployment's own base URL) and six problem types. Three IETF drafts that would otherwise fit (`Idempotency-Key`, resumable uploads, `RateLimit` fields) are not ratified, and the design needs none of them.

**`If-None-Match: *` for "one deposit".** HTTP already has a create-only write, and its refusal (`412`) already means "something is there". Requiring the header (`428` without it) means a sender that forgets cannot be mistaken for one that meant to overwrite. Recognizing a retry by its bytes avoids an idempotency key, the only standard for which is an active working group draft, not ratified.

**A receiver-minted token over the alternatives.** A token issued by the relay (as some SMART Health Links hosting does for its management token) would have to travel back from the server, and the relay would see it at least once in clear; a minted token is seen by the relay only on use and stored only as a hash. A token derived from the pairing key would tie a delete credential to an encryption key. Proof of possession of the pairing key ([RFC 9449](https://www.rfc-editor.org/rfc/rfc9449)) would show the relay the pairing's public key, which the envelope design keeps from it, and would sign with a key agreement key.

**Two steps, collect then delete.** A single destructive read loses the envelope if the response is lost on the way. Two steps cost one request and leave the retention end as the only backstop.

**Delete before the person decides.** Whether to import is a decision about content, which the relay cannot see and has no part in. Holding the envelope until the person answers would keep ciphertext on the relay for as long as a dialog stays open.

**Shape check, not more.** Refusing a body that is not an envelope stops an accidental upload from using the mailbox's one deposit. Checking more (the suite, the route, the `kid`) would make every relay a party to the envelope format's evolution and would gain nothing: the receiver refuses what it cannot open.

**Hours, not days.** The pairing lives an hour by default and the receiver's key at most a day past it. A relay that keeps ciphertext longer than any key that could open it holds risk with no use.

## Consequences

- A relay needs object storage for envelopes up to 43 MiB, since common document stores cap a document near 1 MiB, and an HTTP path that accepts a body that large (some hosting front ends cap HTTP/1.1 request bodies below it; HTTP/2 lifts the cap there).
- Object stores that keep deleted objects by default (soft delete, versioning) must be configured not to, or the deletion bound is false.
- An operator can still deny service, and can deposit into an open empty mailbox whose id it knows; the receiver's duty to show what arrived before importing ([`sealed-envelope.md`](../sealed-envelope.md) section 11.4) covers the second.
- Anonymous creation makes a relay a place to park bytes for two days. Address-based limits and a total byte cap bound it; a later revision may add an anonymous token (Privacy Pass, [RFC 9576](https://www.rfc-editor.org/rfc/rfc9576)) in front of creation. Accounts are ruled out because they would link mailboxes to people.
- Storing only ciphertext does not settle an operator's obligations under health privacy law; that depends on whom it runs the relay for ([`relay-mailbox.md`](../relay-mailbox.md) section 12.8).

## Conformance

Request and response cases are in [`vectors/relay-mailbox/cases.json`](../vectors/relay-mailbox/cases.json): 19 positive and 77 negative, 10 of them needing a relay whose clock a harness can set and 14 sent byte for byte over HTTP/1.1. Envelopes come by id from [`vectors/sealed-envelope/vectors.json`](../vectors/sealed-envelope/vectors.json). Before publication the cases were replayed against two implementations written separately: a reference relay in JavaScript on Node, and a relay in Python written from this document's text without reading the first (both pass all 96 cases of draft 0.3). Deleting stored bytes and keeping identifiers out of logs cannot be seen through the routes; implementations test them themselves.

## Draft 0.2 (2026-10-19)

Draft 0.2 changes no decision above. It settles five points the second implementation read from the text alone: a request that cannot be framed is answered `400` and the connection closed; a transfer coding other than `chunked` is answered `501`; a `405` to `HEAD` carries no content; an `about:blank` title is the status code's reason phrase; and when a mailbox is closed, or closed and past its retention end, while a deposit's body arrives, the earlier check wins. Eleven negative cases were added and every problem title is now checked.

## Draft 0.3 (2026-10-29)

Draft 0.3 changes no decision above. `HEAD` on the envelope is answered exactly as `GET` without content (the bearer required, the same status and header fields), as RFC 9110 sections 9.1 and 9.3.2 describe, rather than refused with `405`; the mailbox, which has no `GET`, still answers `405`. The `Idempotency-Key` draft is described as an active working group draft, not ratified. The document now depends on sealed envelope draft 0.3, whose positive envelope bytes changed. One case changed its expectation, one was rewritten and three were added (96 in all).

## Questions for the ruling

1. Adopt the six problem type URIs under `https://cascadeprotocol.org/docs/spec/relay-mailbox#`, which resolve once the site publishes this document?
2. Keep the relay's envelope limit equal to the envelope's own (44,870,336 characters), rather than a lower relay limit?
3. Retention end at `exp` plus 24 hours, with physical deletion within a further 24 hours?
4. The receiver deletes the mailbox as soon as it has stored the envelope, before the person accepts or refuses it?
5. No relay discovery in this version (the base URL is configuration)?

## Standards

[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) (HTTP semantics), [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111) (caching), [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) (428, 429), [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750) (bearer tokens), [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (problem details), [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515) (`application/jose`), [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) (NumericDate), [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) (base64url), [RFC 6797](https://www.rfc-editor.org/rfc/rfc6797) (HSTS), [RFC 8820](https://www.rfc-editor.org/rfc/rfc8820) (URI design), [FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) (SHA-256), [WHATWG Fetch](https://fetch.spec.whatwg.org/) (CORS), [HL7 SMART Health Cards and Links IG](https://hl7.org/fhir/uv/smart-health-cards-and-links/links-specification.html) 1.0.0, STU (SMART Health Links).
