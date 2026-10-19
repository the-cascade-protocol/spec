# Cascade Protocol Relay Mailbox Specification

**Status:** Draft, proposed (see [`decisions/2026-10-19-relay-mailbox.md`](decisions/2026-10-19-relay-mailbox.md)); not ratified
**Version:** 0.1
**Date:** 2026-10-19
**Authors:** Cascade Agentic Labs LLC
**Website:** https://cascadeprotocol.org
**Depends on:** [`sealed-envelope.md`](sealed-envelope.md) draft 0.1 (the pairing, `mbx`, the envelope and its size limit)

This document specifies the relay mailbox that carries one sealed envelope from a sender to a receiver for route a of [`sealed-envelope.md`](sealed-envelope.md): how the receiver opens a mailbox, how the sender deposits an envelope in it, how the receiver collects and deletes it, what the relay stores, for how long, and what it may write to a log.

The relay is a holding place, nothing more. It never holds a key that opens an envelope, it never sees the pairing, and it keeps what it holds for hours, not days. The routes are plain HTTP: create-only `PUT` with `If-None-Match: *`, bearer tokens, problem details and `Retry-After`. Section 3 lists every construct with the standard it reuses or the reason it is new.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Terminology](#2-terminology)
3. [Standards Reused](#3-standards-reused)
4. [The Mailbox](#4-the-mailbox)
5. [The Routes](#5-the-routes)
6. [What the Relay Checks in a Deposit](#6-what-the-relay-checks-in-a-deposit)
7. [Retention and Deletion](#7-retention-and-deletion)
8. [Logging and What an Operator Sees](#8-logging-and-what-an-operator-sees)
9. [Limits](#9-limits)
10. [Outcomes](#10-outcomes)
11. [What the Receiver and the Sender Do](#11-what-the-receiver-and-the-sender-do)
12. [Security and Privacy Considerations](#12-security-and-privacy-considerations)
13. [Relation to Other Designs](#13-relation-to-other-designs)
14. [Conformance](#14-conformance)

---

## 1. Overview

### 1.1 One mailbox, one envelope

```
receiver                          relay                              sender
   |  PUT /mailboxes/{mbx}          |                                   |
   |  {exp, collectHash} ---------->|  201                              |
   |  shows the pairing (QR code or link; holds mbx, never the token)   |
   |                                |<-- PUT /mailboxes/{mbx}/envelope  |
   |                                |    (the envelope)            201  |
   |  GET /mailboxes/{mbx}/envelope |                                   |
   |  Bearer <token> -------------->|  200 (the envelope)               |
   |  stores it, then               |                                   |
   |  DELETE /mailboxes/{mbx} ----->|  204 (envelope gone, mailbox closed)
```

1. The **receiver** mints the mailbox id `mbx` and a **collect token**, creates the mailbox with the token's hash and the pairing's expiry (section 5.2), and only then shows the pairing.
2. The **sender** reads the pairing, seals an envelope to it, and deposits it once (section 5.3). Knowing `mbx` is all a deposit needs.
3. The receiver polls with the collect token until the envelope is there (section 5.4), stores it, and deletes the mailbox (section 5.5). Then it opens the envelope.
4. Whatever the receiver does not delete, the relay deletes on its own schedule (section 7): nothing outlives the pairing's expiry by more than 48 hours.

### 1.2 What it protects

The relay holds ciphertext it cannot open, with a hash of a token it never stored, under an id that names nobody. Section 12 lists what the relay and its operator can and cannot see and do.

### 1.3 Requirements language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

---

## 2. Terminology

Sender, receiver, pairing, envelope and `mbx` are as in [`sealed-envelope.md`](sealed-envelope.md) section 2.

| Term | Definition |
|------|-----------|
| **Relay** | The HTTPS service that holds mailboxes. |
| **Mailbox** | The relay's record for one pairing, addressed by `mbx` (section 4.3). |
| **Collect token** | 32 random bytes the receiver mints and keeps; the bearer token for collecting and deleting (section 4.2). |
| **`collectHash`** | SHA-256 of the collect token's 32 bytes; the only form of the token the relay stores. |
| **`exp`** | The pairing's expiry, the same NumericDate as the pairing's `exp`. |
| **Retention end** | `exp` plus 86,400 seconds (section 4.4). |
| **Open / closed** | A mailbox is open until the receiver deletes it, then closed until its retention end (section 4.4). |
| **Base URL** | The relay's location; every path in this document is relative to it (section 5.6). |

---

## 3. Standards Reused

A construct in this document is new only when no ratified standard defines it. Status is the IETF status on the date of this document.

| Construct | Reused standard (status) | New, and why |
|---|---|---|
| Methods, status codes, conditional requests, `Retry-After`, `Allow`, `Content-Length` | HTTP Semantics, [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) (Internet Standard) | none |
| Message framing | HTTP/1.1, [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112) (Internet Standard); HTTP/2, [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113) (Proposed Standard) | none |
| JSON in the create request | [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) (Internet Standard), with duplicate member names refused as [`pod-encryption.md`](pod-encryption.md) section 4.1 does | none |
| Create once, never overwrite (mailbox and deposit) | `PUT` with `If-None-Match: *`, RFC 9110 sections 9.3.4 and 13.1.2, answered `412 Precondition Failed` when something is already there | none |
| Refusing a write that does not say "create only" | `428 Precondition Required`, [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) section 3 (Proposed Standard) | none |
| Rate limiting | `429 Too Many Requests`, RFC 6585 section 4, with `Retry-After` (RFC 9110 section 10.2.3) | none |
| A deposit whose content is not an envelope | `422 Unprocessable Content`, RFC 9110 section 15.5.21 | none |
| Collect and delete credential | Bearer token in the `Authorization` header, [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750) sections 2.1 and 3 (Proposed Standard) | none; the token is minted by the receiver, not issued by an authorization server, which RFC 6750 permits (it does not define issuance) |
| Storing the token | SHA-256, [FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final), over the token's bytes | none |
| Error bodies | Problem Details for HTTP APIs, [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (Proposed Standard), `application/problem+json` | six problem types (section 10): RFC 9457 section 4 advises a plain status code for a generic problem, and these six are not generic: each shares its status code with another outcome the caller must act on differently |
| Envelope media type | `application/jose`, [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515) section 9.2.1 | none |
| Expiry | NumericDate, [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) section 2, as in the pairing | none |
| Ids and tokens as text | base64url without padding, [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) section 5 | none |
| No caching anywhere | `Cache-Control: no-store`, [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111) section 5.2.2.5 (Internet Standard) | none |
| Transport security | `https`, RFC 9110 section 4.2.2; [RFC 6797](https://www.rfc-editor.org/rfc/rfc6797) (HSTS, Proposed Standard) | none |
| Paths under a deployment-chosen base URL | [RFC 8820](https://www.rfc-editor.org/rfc/rfc8820) section 2.3 (Best Current Practice) | the two path templates of section 5, relative to the base URL, as RFC 8820 allows |
| Cross-origin use from a web page | CORS, [WHATWG Fetch](https://fetch.spec.whatwg.org/) (Living Standard) | none |
| Holding encrypted bytes it cannot read, with a deletion credential separate from the content key | SMART Health Links manifest server ([HL7 SMART Health Cards and Links IG](https://hl7.org/fhir/uv/smart-health-cards-and-links/links-specification.html) 1.0.0, STU), section 13 | the routes: a SMART Health Links server is read by many recipients through a manifest; a mailbox is written once by a sender and read once by its receiver (section 13) |

Considered and not used, because none is ratified: an `Idempotency-Key` request header ([draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/), an expired working group draft), which section 5.3 does not need because a retry is recognized by its bytes; resumable uploads ([draft-ietf-httpbis-resumable-upload](https://datatracker.ietf.org/doc/draft-ietf-httpbis-resumable-upload/), a working group draft), which a 43 MiB maximum does not need; `RateLimit` header fields ([draft-ietf-httpapi-ratelimit-headers](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/), a working group draft), where `Retry-After` is enough. Also not used: `Content-Digest` ([RFC 9530](https://www.rfc-editor.org/rfc/rfc9530)), because the envelope authenticates itself and the relay cannot check that; proof of possession of the pairing key (DPoP, [RFC 9449](https://www.rfc-editor.org/rfc/rfc9449)), because it would show the relay the pairing's public key, which [`sealed-envelope.md`](sealed-envelope.md) section 11.1 keeps from it, and would use a key agreement key for signing; Privacy Pass ([RFC 9576](https://www.rfc-editor.org/rfc/rfc9576)) for anonymous rate limiting, which a later revision may add in front of mailbox creation (section 12.6).

---

## 4. The Mailbox

### 4.1 The id

The mailbox id is the pairing's `mbx`: 16 bytes from a cryptographically secure random generator, minted by the receiver, written as 22 base64url characters without padding. Only the canonical spelling is valid: decoding and re-encoding reproduces the text, so the last character is one of `A`, `Q`, `g`, `w`. A receiver MUST mint a fresh `mbx` for every pairing.

### 4.2 The collect token

The collect token is 32 bytes from a cryptographically secure random generator, minted by the receiver for one mailbox and written as 43 base64url characters without padding. `collectHash` is the base64url, without padding, of SHA-256 over the token's 32 decoded bytes (not over its text).

The receiver keeps the token with the pairing's private key ([`sealed-envelope.md`](sealed-envelope.md) section 5), protected the same way, and deletes it when it deletes that key. **The token MUST NOT appear in the pairing, the link or the QR code**, and the receiver MUST NOT give it to the sender or derive it from anything in the pairing. A relay MUST NOT store the token, only `collectHash`.

The token is the receiver's own credential and stays on the receiver's device. Nothing issues it and nothing else needs it: unlike a deposit, a collect is made only by the application that made the pairing.

### 4.3 The record

For each mailbox a relay stores exactly:

| Field | Value |
|---|---|
| `mbx` | the id |
| `collectHash` | from the create request |
| `exp` | from the create request |
| retention end | `exp` + 86,400 |
| state | open or closed |
| envelope | none, or the deposited bytes exactly as received |

A relay MAY also keep, with the record and deleted with it, the time it was created and the length and SHA-256 of the envelope (to answer section 5.3's `identical` without rereading the bytes). It MUST NOT store anything else about a mailbox or a request: no network address, user agent, referrer, header value, account, or anything parsed from the envelope.

### 4.4 Lifetime

| Period | Create | Deposit | Collect | Delete |
|---|---|---|---|---|
| Open, before `exp` | refused (412) | accepted once | the envelope, or "not yet" | closes it |
| Open, from `exp` to the retention end | refused (412) | refused (410 `expired`) | the envelope, or 410 `expired` if none came | closes it |
| Closed, until the retention end | refused (412) | refused (410 `closed`) | refused (410 `closed`) | 204 again |
| From the retention end | as if never created | 404 | 404 | 404 |

The retention end is fixed at creation as `exp` plus 86,400 seconds, whatever the receiver asks for. It matches the receiver's own key lifetime: [`sealed-envelope.md`](sealed-envelope.md) section 4.6 deletes the pairing's private key no later than 24 hours after `exp`, so an envelope kept longer could never be opened by anyone. Because `exp` is at most 24 hours and 5 minutes after creation (section 5.2), a relay holds an envelope for at most about 48 hours, and every trace of a mailbox is gone within 24 hours after its retention end (section 7).

---

## 5. The Routes

### 5.1 Common rules

**Transport.** A relay MUST serve only `https` and SHOULD send `Strict-Transport-Security`. It MAY serve HTTP/1.1, HTTP/2 or HTTP/3; whichever it serves, it MUST accept a deposit of the maximum size (section 9), which some front ends do not allow over HTTP/1.1.

**Two resources.** `/mailboxes/{mbx}` is the mailbox; `/mailboxes/{mbx}/envelope` is the envelope in it. The methods are exactly:

| Method and path | Who | Section |
|---|---|---|
| `PUT /mailboxes/{mbx}` | receiver, no credential | 5.2 create |
| `PUT /mailboxes/{mbx}/envelope` | sender, no credential | 5.3 deposit |
| `GET /mailboxes/{mbx}/envelope` | receiver, bearer | 5.4 collect |
| `DELETE /mailboxes/{mbx}` | receiver, bearer | 5.5 delete |

`{mbx}` stands for any one non-empty path segment, matched as sent (not percent-decoded); whether it is a valid id is a route's own check. A request whose path is neither template (including a trailing `/` or an empty segment) is answered `404` with type `about:blank`. On a matching path, any other method is answered `405 Method Not Allowed` with `Allow: PUT, DELETE` for the mailbox and `Allow: GET, PUT` for the envelope; that includes `HEAD`, since a relay is not a general-purpose server (RFC 9110 section 9.1), and `OPTIONS` other than a CORS preflight the relay chooses to answer (below). There is no route that lists mailboxes or describes one.

**Credentials.** Collect and delete take the collect token as a bearer token in the `Authorization` header (RFC 6750 section 2.1); the scheme name is case-insensitive (RFC 9110 section 11.1) and is followed by one or more spaces and the token (RFC 6750 section 2.1). A relay MUST NOT accept the token from the query string or the body (RFC 6750 sections 2.2 and 2.3) and MUST ignore a query string. A relay checks a token by hashing the presented bytes and comparing the result with `collectHash` in constant time, and treats a bearer that is not 43 canonical base64url characters as a wrong token without a shorter code path. A request with no `Authorization` header is answered `401` with `WWW-Authenticate: Bearer`, carrying no error code (RFC 6750 section 3.1); any other failure, including an empty header, more than one header or another scheme, is answered `401` with `WWW-Authenticate: Bearer error="invalid_token"` (RFC 6750 section 3.1). Relays never use cookies.

**Every response** carries `Cache-Control: no-store` and SHOULD carry `X-Content-Type-Options: nosniff`.

**Refusals** carry an RFC 9457 problem details body (`application/problem+json`) with `type`, `title` and `status`, and nothing that repeats or describes the request (no `detail` built from input, no `instance` naming the mailbox). `type` is one of the six URIs of section 10 where the status code alone is ambiguous, and `about:blank` otherwise.

**Order.** A relay checks the path, then the method, then its rate limits (section 9), then the route's own conditions in the order listed, and answers with the first that fails.

**Media types and framing.** A media type is compared by type and subtype, ignoring case and parameters (RFC 9110 section 8.3.1); a missing `Content-Type` is answered `415`. A precondition is satisfied only by exactly one `If-None-Match` field whose value is `*`; a list, an entity tag or a repeated field is answered `400`. Message framing is HTTP's own ([RFC 9112](https://www.rfc-editor.org/rfc/rfc9112), [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113)): an incomplete or misframed body is a failed request that changes nothing. JSON is [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) UTF-8 without a byte order mark, and a JSON object holding the same member name twice, at any depth, is malformed, as in [`pod-encryption.md`](pod-encryption.md) section 4.1.

**Cross-origin use.** A relay MAY answer CORS preflight requests so a sender or receiver running in a web page on another origin can call it. If it does, it MUST NOT send `Access-Control-Allow-Credentials: true`, and it lists `Authorization`, `Content-Type` and `If-None-Match` in `Access-Control-Allow-Headers` explicitly.

### 5.2 Create: `PUT /mailboxes/{mbx}`

The receiver creates the mailbox before it shows the pairing.

```http
PUT /mailboxes/hWzA3sJDkO9p1vQ6bT2xUg HTTP/1.1
Content-Type: application/json
If-None-Match: *

{"exp":1792003600,"collectHash":"<43 base64url characters>"}
```

| Member | Rule |
|---|---|
| `exp` | The pairing's `exp`: a JSON number written as a non-negative integer (digits only, no sign, fraction or exponent). |
| `collectHash` | 43 base64url characters, canonical (32 bytes). |

Unknown members are ignored. The relay answers, in order:

1. `428` if `If-None-Match` is absent; `400` if it is anything other than exactly `*`;
2. `415` if the media type is not `application/json`;
3. `400` if `{mbx}` is not a canonical 16-byte id (section 4.1);
4. `413` if the body is over 1,024 bytes (by `Content-Length` when present, else as read);
5. `400` if the body is not one JSON object (section 5.1), or `exp` or `collectHash` is missing or breaks the table above;
6. `400` if `exp` is not later than the relay's clock, or is more than 86,700 seconds (24 hours and 5 minutes, allowing for clock difference) after it;
7. `412` (`about:blank`) if a mailbox with this id exists, open or closed, before its retention end;
8. `201 Created`, with an empty body and `Location` giving the mailbox's URI (RFC 9110 section 10.2.2; a relative reference is allowed). The mailbox is open.

A `412` here means a collision of random ids or a reused id. The receiver mints a new `mbx` and token and tries again; it never reuses a pairing whose mailbox it did not create.

### 5.3 Deposit: `PUT /mailboxes/{mbx}/envelope`

```http
PUT /mailboxes/hWzA3sJDkO9p1vQ6bT2xUg/envelope HTTP/1.1
Content-Type: application/jose
Content-Length: 3412
If-None-Match: *

eyJhbGciOiJIUEtFLTciLCJ0eXAiOiJjYXNjYWRlLXNlYWxlZC1lbnZlbG9wZStqd2UiLC...
```

No credential: knowing `mbx` is what allows a deposit ([`sealed-envelope.md`](sealed-envelope.md) section 9). The relay answers, in order:

1. `404` `no-mailbox` if `{mbx}` is not canonical, or names no mailbox, or the relay's clock reads its retention end or later;
2. `410` `closed` if the mailbox is closed;
3. `428` if `If-None-Match` is absent; `400` if it is anything other than exactly `*`;
4. `415` if the media type is not `application/jose`;
5. `411` if there is no `Content-Length` (a deposit sent with a transfer coding, such as HTTP/1.1 chunked, has none); `413` if it is more than 44,870,336;
6. `412` `already-deposited` if an envelope is already stored (below);
7. `410` `expired` if the relay's clock reads `exp` or later;
8. `422` `malformed-envelope` if the body breaks section 6;
9. `201 Created`, empty body, once the envelope is stored durably. The store is the atomic step below; if, at that step, another deposit has been stored, the answer is `412` `already-deposited` as in step 6, and if the mailbox has been closed or its retention end reached while the body was read, the answer is that of step 2 or step 1. `exp` is not checked again: a deposit that passed step 7 is accepted.

**One deposit per mailbox.** Storing an envelope and checking that none is stored is one atomic step. A stored envelope is never replaced, by a deposit or by anything else. A deposit refused at any step other than 9 leaves the mailbox as it was: a refused body never fills the mailbox.

**`identical`.** The `412` `already-deposited` problem details carry the member `identical`: `true` when the request's body is byte for byte the stored envelope, `false` otherwise. A relay MAY set `false` without reading the body when `Content-Length` differs from the stored length. `identical` lets a sender whose first response was lost (a dropped connection, a timeout) learn that its own deposit is the one stored, and a sender whose deposit was beaten by another learn that it was not:

```json
{"type":"https://cascadeprotocol.org/docs/spec/relay-mailbox#already-deposited","title":"An envelope is already deposited","status":412,"identical":true}
```

The `412` takes precedence over `410` `expired`, so a retry after `exp` still learns `identical`.

### 5.4 Collect: `GET /mailboxes/{mbx}/envelope`

```http
GET /mailboxes/hWzA3sJDkO9p1vQ6bT2xUg/envelope HTTP/1.1
Authorization: Bearer <collect token>
```

The relay answers, in order:

1. `404` `no-mailbox` if `{mbx}` is not canonical, names no mailbox, or the relay's clock reads its retention end or later;
2. `401` if the bearer does not match (section 5.1);
3. `410` `closed` if the mailbox is closed;
4. `200 OK`, `Content-Type: application/jose`, the stored bytes exactly, if an envelope is stored;
5. `410` `expired` if the relay's clock reads `exp` or later (nothing came and nothing can now);
6. `404` `not-deposited`, with `Retry-After` in seconds: nothing yet. A relay SHOULD send `Retry-After: 5`.

Collecting does not delete: a receiver whose connection drops mid-download simply collects again. Section 5.5 is the deletion.

### 5.5 Delete: `DELETE /mailboxes/{mbx}`

```http
DELETE /mailboxes/hWzA3sJDkO9p1vQ6bT2xUg HTTP/1.1
Authorization: Bearer <collect token>
```

The relay answers, in order:

1. `404` `no-mailbox` if `{mbx}` is not canonical, names no mailbox, or the relay's clock reads its retention end or later;
2. `401` if the bearer does not match;
3. `204 No Content`. The mailbox is closed and any envelope in it is deleted before the response is sent (section 7).

Delete is idempotent (RFC 9110 section 9.2.2): on a closed mailbox it checks the bearer and answers `204` again. It both finishes a delivery (after collecting) and cancels a pairing (before anything came): either way, nothing more can be deposited.

### 5.6 Locating the relay

The pairing carries `mbx` and no relay address ([`sealed-envelope.md`](sealed-envelope.md) section 4.1). The receiver and the sender each know the relay's base URL from the application the pairing is made for: the receiver builds the pairing link for a particular sender application (section 4.2 of that document) and uses the relay that application uses. This version defines no discovery. Both sides MUST use the same base URL for one pairing; a deposit sent to another relay meets `404` `no-mailbox`.

---

## 6. What the Relay Checks in a Deposit

The relay checks shape only, so that a deposit of the wrong file is refused before it uses up the mailbox's one deposit. It holds no key, derives none, and judges no cryptography: an envelope with a tampered tag, a wrong `kid` or an unknown `alg` is stored as given, and the receiver refuses it ([`sealed-envelope.md`](sealed-envelope.md) section 10).

A body passes when all of these hold:

1. every byte is printable ASCII from `0x21` to `0x7E` (so no whitespace, no line ending);
2. it splits on `.` into exactly five segments, each made only of the base64url alphabet (the second, third and fifth may be empty);
3. the first segment is between 1 and 16,384 characters, and decodes as canonical base64url without padding to UTF-8 text that is one JSON object with no duplicate member names at any depth, whose `typ` is the string `cascade-sealed-envelope+jwe` and whose `alg` is a string;
4. the fourth segment (the ciphertext) is not empty.

Anything else is `422` `malformed-envelope`. Because of item 1, the envelope's limit in characters ([`sealed-envelope.md`](sealed-envelope.md) section 6.1) is the same number of bytes. The relay MUST NOT check more than this (for example the `alg` value, the `kid`, the second segment's length, or the route), and MUST NOT keep anything it parsed after answering.

---

## 7. Retention and Deletion

**When.** A relay deletes an envelope when the receiver deletes the mailbox (section 5.5), and in any case at the mailbox's retention end. It deletes the record at the retention end.

**Serving stops at once; storage follows within a day.** From the instant a delete is answered, or the retention end passes, the relay MUST answer as if the envelope (or the mailbox) were gone. Every stored copy of the envelope MUST be gone within 24 hours after the delete or the retention end, whichever comes first, and every copy of the record within 24 hours after the retention end. "Every copy" includes soft-deleted objects, object versions, point-in-time recovery windows, replicas, caches and backups: a relay MUST configure its storage so that none of them outlives this bound (for example, by turning off object versioning and soft delete, and by taking no backups of mailbox storage).

**The bound, end to end.** A mailbox is created at most 24 hours and 5 minutes before its `exp`; its retention end is 24 hours after `exp`; its last copy is gone 24 hours after that. No envelope stays anywhere in a relay longer than about 72 hours after its mailbox was created.

**Closed mailboxes** keep their record, with no envelope, until the retention end, so that a late deposit is answered `410` `closed` rather than recreating the mailbox, and a repeated delete is answered `204`.

---

## 8. Logging and What an Operator Sees

### 8.1 What a relay may log

A relay MAY log, per request: the route template (never the path), the method, the status, the problem type, and the time taken. It MAY log counts (mailboxes created, deposits, deletions, records swept). It MUST NOT write to any log, trace, metric label or error report:

- an `mbx`, a collect token, a `collectHash`, or any value from a request header;
- any byte of an envelope, or anything derived from one: its length, a hash of it, or any member of its protected header (such as `kid` or `alg`);
- a mailbox's `exp` or retention end;
- a network address, a user agent or a referrer.

Rate limits that need a network address keep it in memory only, keyed by a keyed hash under a secret that is never written down, and forget it when the window passes.

**Platform logs count.** A hosting platform's own request log normally records the client's address and the full path, and the path holds `mbx`. A relay MUST turn such logs off or exclude them from storage, and MUST NOT turn on storage audit logs that record object names or reads, unless they hold neither `mbx` nor anything linkable to it.

### 8.2 What an operator can and cannot see

| An operator with full access to the relay's storage and logs | |
|---|---|
| **can see** | each open or closed mailbox's `mbx`, `collectHash`, `exp`, creation time and state; an envelope's bytes until it is deleted, including its protected header (`alg`, `typ`, `cty` and, for a pairing, `kid`); the envelope's length; in memory only, the addresses of current callers |
| **cannot see** | any record content (the envelope is sealed to a key the relay never holds); the pairing, its public key, or its Pod reference; the collect token; who the sender or the receiver is (there are no accounts); anything at all about a mailbox after its last copy is deleted (section 7) |
| **can do** | refuse service, delay a deposit or a collect, delete an envelope early, or deposit something of its own into an open, empty mailbox it knows the id of |
| **cannot do** | read an envelope; make an envelope the receiver accepts as the sender's (sealing needs the pairing's public key, which reaches the sender only from the receiver's screen); replace a deposited envelope without the receiver seeing a different `kid` or a failed open |

The guarantee to state publicly is the one [`sealed-envelope.md`](sealed-envelope.md) section 11.9 allows: the relay cannot read what it stores. A relay operator that stores what it cannot read may still have duties under health privacy law (section 12.8).

---

## 9. Limits

| Limit | Value | Answer |
|---|---|---|
| Create body | 1,024 bytes | 413 |
| Envelope | 44,870,336 bytes ([`sealed-envelope.md`](sealed-envelope.md) section 6.1); a relay MUST accept up to this and MUST refuse more | 413 |
| Protected header segment | 16,384 characters | 422 |
| Pairing expiry at creation | at most 86,700 seconds ahead | 400 |
| Requests over a rate limit | deployment policy (below) | 429 with `Retry-After` |
| Storage or creation capacity exhausted | deployment policy | 503 with `Retry-After` |

Rate limits are a deployment's own policy and are not conformance requirements, but a relay MUST have them and MUST answer them with `429` and `Retry-After`. RECOMMENDED starting points, per client network address (an IPv6 address counted by its /64) per hour: 10 mailbox creations, 30 deposits, 128 MiB of deposited bytes, 30 failed bearer checks; per mailbox, 30 collects per minute. A relay SHOULD also cap the total bytes it holds and answer `503` with `Retry-After` past it, rather than accept what it cannot keep.

---

## 10. Outcomes

Every request ends in exactly one of these. "Type" is the problem details `type`; the six Cascade types are `https://cascadeprotocol.org/docs/spec/relay-mailbox#` followed by the code shown, and their `title` members are: `no-mailbox` "No such mailbox", `not-deposited` "Nothing deposited yet", `already-deposited` "An envelope is already deposited", `expired` "The mailbox no longer accepts deposits", `closed` "The mailbox is closed", `malformed-envelope` "Not a sealed envelope". For `about:blank` the title is the status code's reason phrase (RFC 9457 section 4.2.1).

| Status | Type | Routes | When | The caller |
|---|---|---|---|---|
| 201 | none | create, deposit | created, or stored | proceeds |
| 200 | none | collect | the envelope | stores it, deletes the mailbox, opens it |
| 204 | none | delete | closed (again) | done |
| 404 | `not-deposited` | collect | nothing yet; `Retry-After` given | waits at least `Retry-After`, then collects again |
| 404 | `no-mailbox` | deposit, collect, delete | no such mailbox, or the relay's clock reads its retention end or later | sender: the code is not recognized, start again; receiver: start again |
| 410 | `expired` | deposit, collect | the relay's clock reads `exp` or later and nothing was deposited | start again with a new pairing |
| 410 | `closed` | deposit, collect | the receiver deleted the mailbox | sender: the code was already used or cancelled |
| 412 | `already-deposited` | deposit | an envelope is already stored; `identical` says whether it is this one | `true`: delivered; `false`: the code was used by something else, start again |
| 422 | `malformed-envelope` | deposit | the body is not an envelope (section 6) | a bug in the sender; nothing was stored |
| 400 | `about:blank` | create, deposit | a malformed request, or `exp` out of range | a bug |
| 401 | `about:blank` | collect, delete | missing or wrong bearer | a bug, or not this receiver |
| 404 | `about:blank` | none | a path that is neither template | a bug |
| 405 | `about:blank` | any | method not allowed (`Allow` given) | a bug |
| 411 | `about:blank` | deposit | no `Content-Length` | resend with it |
| 412 | `about:blank` | create | the id is taken | mint a new id and token |
| 413 | `about:blank` | create, deposit | too large | the bundle is too big for this route; use a saved file |
| 415 | `about:blank` | create, deposit | wrong media type | a bug |
| 428 | `about:blank` | create, deposit | no `If-None-Match: *` | a bug |
| 429 | `about:blank` | any | over a rate limit; `Retry-After` given | waits |
| 503 | `about:blank` | any | the relay is at capacity or down; `Retry-After` given when known | waits |

---

## 11. What the Receiver and the Sender Do

**The receiver** MUST:

1. mint `mbx` (section 4.1), a pairing key ([`sealed-envelope.md`](sealed-envelope.md) section 4.6) and a collect token (section 4.2);
2. create the mailbox (section 5.2) and show the pairing only after `201`. If creation fails, it shows no pairing;
3. collect no more often than `Retry-After` allows, and stop at `exp` unless an envelope has arrived (a `410` `expired` says so);
4. after `200`, store the envelope durably on its own device, then delete the mailbox, before it opens the envelope or asks the person anything. It does not wait for the person to accept what arrived: deciding about the content is the receiver's business, and holding it is not the relay's;
5. delete the mailbox when it abandons the pairing (the person closes the code, starts again, or the pairing expires), and treat `204`, `404` and `410` from a delete as done;
6. then open and show what arrived before writing it into the Pod, as [`sealed-envelope.md`](sealed-envelope.md) section 11.4 requires.

**The sender** MUST deposit at most one envelope per pairing, sealed before it is sent, and:

1. on a network failure or a `5xx`, retry the same bytes (never a re-sealed envelope) until `exp`, respecting `Retry-After`;
2. on `412` `already-deposited` with `identical` `true`, report delivery;
3. on `412` with `identical` `false`, or `410` `closed`, tell the person the code was already used and to start again with a new one on the receiver; it MUST NOT seal again to the same pairing;
4. on `410` `expired` or `404` `no-mailbox`, tell the person to start again.

---

## 12. Security and Privacy Considerations

### 12.1 Guessing a mailbox id

`mbx` has 128 random bits. There is no listing route, refusals do not say whether a malformed id would have existed, and creation, deposit and the bearer checks are rate limited per address. A relay MUST NOT accept a shorter id or offer any route that finds a mailbox by anything but its id.

### 12.2 The credential

The collect token never leaves the receiver except in the `Authorization` header of its own requests to the relay, over HTTPS. The relay stores only its SHA-256, so a copy of the relay's storage yields nothing that collects. 256 bits cannot be guessed, so no attempt counter is needed beyond the rate limits (contrast a SMART Health Links passcode, which is short and therefore counted). The pairing never holds the token, so the photograph of section 12.4 gives no way to collect or delete.

### 12.3 Timing

Bearer checks hash and compare in constant time regardless of the presented value (section 5.1). Whether a mailbox exists, and its state, are not secret from someone who holds its id: a deposit already reveals them. The relay's response time does not depend on an envelope's content, since it parses only the protected header.

### 12.4 A photographed QR code

Someone who photographs the pairing learns `mbx` and the public key. They can deposit first. The one-deposit rule then refuses the real sender with `identical` `false`, which the sender reports, and the receiver shows the stranger's bundle before importing it so the person can refuse it ([`sealed-envelope.md`](sealed-envelope.md) section 11.4). They cannot collect, delete, read, or replace a stored envelope. Showing the code only for the pairing's short life (1 hour recommended) narrows the window.

### 12.5 Replay

An envelope captured on the way cannot be deposited into another mailbox usefully: it opens only with its own pairing's key ([`sealed-envelope.md`](sealed-envelope.md) section 11.3). It cannot be deposited again into its own mailbox: a stored envelope is never replaced, and a closed mailbox takes nothing. A request replayed by a network attacker who could see inside HTTPS would gain nothing a deposit does not already allow; HTTPS keeps the collect token from them.

### 12.6 Denial of service and misuse as storage

A relay that accepts anonymous creation is a free place to park up to 43 MiB for two days. The shape check (section 6) stops casual misuse, not a determined one. The limits of section 9 (creations, deposits and bytes per address, a total byte cap, the short retention) bound it. A later revision may put Privacy Pass ([RFC 9576](https://www.rfc-editor.org/rfc/rfc9576)) or another anonymous token in front of creation if address limits prove too weak; a relay MUST NOT require an account, because an account would link mailboxes to a person.

### 12.7 Holding the bytes

An envelope is safe to store only because the relay cannot open it, and that rests on the pairing key never reaching the relay ([`sealed-envelope.md`](sealed-envelope.md) section 4.2). A relay MUST NOT serve a page that hands senders a pairing, and MUST NOT accept a pairing or a public key on any route.

### 12.8 Regulatory status

Storing only ciphertext does not by itself change who must comply with health privacy law. United States guidance treats a cloud service that stores encrypted health information for a regulated entity as that entity's business associate even when it holds no key ([HHS, Guidance on HIPAA and Cloud Computing](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html)). Which side of that line an operator is on depends on whom it runs the relay for, which this specification does not and cannot decide.

---

## 13. Relation to Other Designs

**SMART Health Links.** A SMART Health Links server ([links specification](https://hl7.org/fhir/uv/smart-health-cards-and-links/links-specification.html), 1.0.0, STU) also holds encrypted bytes it cannot read. Its manifest URL, which lets anyone holding it read, carries at least 256 bits of entropy; a mailbox id lets its holder only deposit, and the right to read is the 256-bit collect token (section 4.2). What is shared: unguessable ids instead of accounts, `404` once a link is no longer active, `429` for clients that ask too often, `Retry-After` to pace polling, short-lived access, and a management credential separate from the content key. What differs: SMART Health Links serves one sharer to many recipients through a `POST` manifest request carrying a `recipient` label and an optional passcode, and its files are fetched from locations valid for up to an hour; a mailbox is written once and read by one receiver, needs no recipient label (it would tell the relay who collected), and has no passcode (its credential is a 256-bit token, section 12.2). The mailbox therefore reuses SMART Health Links' behavior, not its routes.

**Blind object stores for SMART Health Links.** Public designs that host SMART Health Links on an ordinary object store (for example an open-source service that stores ciphertext, a hashed management token and opaque metadata, and revokes with `DELETE` and a bearer token) use the same split this document uses: the content key in the link fragment, a management token that cannot decrypt, and storage that holds only ciphertext. The difference is direction: they publish data for many readers, a mailbox receives it for one.

**Inboxes of other protocols.** A Linked Data Notifications inbox ([W3C Recommendation](https://www.w3.org/TR/ldn/)) receives notifications by `POST` for an owner to read; it is a way to send messages to a known resource, has no one-deposit rule, and leaves authentication and retention open, so it adds nothing a mailbox needs.

---

## 14. Conformance

Request and response cases are in [`vectors/relay-mailbox/cases.json`](vectors/relay-mailbox/cases.json): 18 positive cases (the whole lifecycle; cancel before deposit; a second deposit refused with `identical` `false`; a retry with `identical` `true`; envelopes the relay must store without judging them, including one with a tampered tag, one naming another suite, a six-word envelope and one of exactly the maximum length; the bearer scheme in any case and with more than one space; media type parameters; unknown members; the expiry and retention boundaries) and 64 negative cases (every refusal of sections 5.1 to 5.5, seventeen shape failures of section 6, other paths, and the methods that are not allowed). Envelopes are taken by id from [`vectors/sealed-envelope/vectors.json`](vectors/sealed-envelope/vectors.json). Each case runs against a fresh mailbox id and token; the 8 cases marked with a controlled clock need a relay whose clock a test harness can set and advance, and the other 74 run against any relay.

A conforming relay produces the stated status, problem `type`, `identical` member and headers for every case, and returns collected envelopes byte for byte. Two of this document's requirements cannot be seen through the routes and are left to an implementation's own tests: that a deleted envelope's bytes are gone from storage (section 7), and that nothing of section 8.1 reaches a log. The cases move to the conformance repository when this document is ratified.
