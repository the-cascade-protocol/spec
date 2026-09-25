# D-WELLNESS-1: A wellness reading is a named individual; only its compound sub-values stay blank nodes

**Status:** Ratified. Direction ratified by Jed Reinitz on 2026-09-19 (vocabulary/shapes, his
tie-break under the ratified working agreement, r3); merged 2026-09-24 as spec#65 with
no objection posted, the review window waived by Jed after a conversation with Jay the same day in
which the vocabulary was agreed to be the contract between the application and the import pipeline.
RFC issue: the-cascade-protocol/spec#64. Q3's layer classification is superseded in direction by
that conversation (a computed aggregate is a derived view, not a layer-1 record); an amendment
follows.
**Date:** 2026-09-19
**Proposed by:** Jed Reinitz
**Prompted by:** D1 in the wellness aggregator scope decision (lines 138-146, 378), tracked
separately while scoping the Apple Health wellness aggregator. Applies D-CANONICAL-1's identity
principle to a class of record that document did not name.

---

## What this decides, precisely

Each entry in a wellness `*History` list is serialized as a **named individual** with a minted IRI,
not as a blank node inside an RDF collection. The lists are `restingHeartRateHistory`,
`walkingHeartRateHistory`, `hrvHistory`, `bloodPressureHistory`, `vo2MaxHistory`,
`bodyMassHistory`, `dailyActivityHistory` and `dailySleepHistory`: every `owl:ObjectProperty` with
domain `health:HealthProfile` in `spec/serialization/index.md` §12's time-series container pattern.

**This decision does not extend to the separate "latest reading" convenience properties**
(`health:restingHeartRate`, `health:heartRateVariability`, `health:bodyMass`, `health:bodyHeight`,
and similar). Those are declared `owl:DatatypeProperty` with `rdfs:range xsd:double` in
`health.ttl` (e.g. lines 287-296, 402-422), which already conflicts with their use in
`spec/serialization/index.md`'s worked examples as object-valued links to a nested reading
resource, a pre-existing inconsistency this decision found but does not resolve. They stay blank
nodes, unchanged, until that conflict is settled on its own terms (a follow-up is filed,
see Consequences).

**What stays a blank node in the readings this decision does cover:**
- `prov:wasGeneratedBy`, the activity attached to each reading. It has no identity independent of
  the reading it describes.
- Period-level statistics containers (`health:HRVStatistics`, `health:VO2MaxStatistics`). These
  summarize many readings over a rolling window and have no single record to seed an identity from.

## Three questions the core ruling does not answer, each with a recommendation

Naming a reading is not the same as saying what its name is made of. Three sub-questions follow,
and an earlier draft of this document answered two of them badly and the third by inventing a
mechanism that does not exist. Each is stated below with what the options actually imply and a
recommendation. Following the pattern the wellness-aggregator scope doc already used for its own
D3-D7, **these are recommendations open to objection, not rulings; silence accepts them.**

### Q1. What is the identity seed made of?

**Why it matters:** two devices importing the same export, or one device importing it twice, must
mint the same IRI or the pod grows duplicates. The seed's exact composition decides that. It also
decides what *re-mints* when something upstream changes.

**What the options imply:**

- **Including the record class** (`health:DailyVitalReading`, etc.) is redundant, since the metric
  axis already determines the class, and it is actively dangerous: this document's own first draft
  claimed a "latest reading" and a history entry were the same individual, which was impossible
  precisely because the two carry different classes. A component that can disagree with itself is a
  component that can split one record into two.
- **Using the LOINC or SNOMED code as the metric axis** names the record from its *meaning*. Our
  LOINC mappings live in `WellnessVocabulary.swift`, were ratified 2026-01-29, and can be revised.
  If a mapping is ever corrected, every wellness IRI in every pod re-mints and every citation that
  pointed at one breaks. D-CANONICAL-1 retired meaning-derived naming for exactly this reason.
- **Using Apple's own type identifier** (`HKQuantityTypeIdentifierRestingHeartRate`, the literal
  `type` attribute in the export) names the record from its *input*, which is what D-CANONICAL-1
  requires. A later re-mapping of LOINC codes then changes what the record *says*, not what it *is*.
- **Omitting a pod/subject component is a latent cross-person collision.** "Resting heart rate,
  2026-01-20, Apple Watch Series 9" is a low-entropy tuple shared by every person who owns that
  watch. Within one pod that is harmless. Across pods it is not, and D-LAYERS-1's query amendment
  already names federation (one question over several pods, the caregiver case) as a direction of
  travel. Two people's readings minting one IRI is the unrecoverable merge failure, arriving later
  and in the worst possible place.
- **Separator choice** is the ordinary injection problem: a source named `a|b` and a source named
  `a` with a metric starting `b` must not produce the same seed string.

**Recommendation (amended 2026-09-24, after the Google measurement and the v2.10 build; the
original text is in this file's history):** two seeds, one per naming tier of D-CANONICAL-1.

For a record whose source supplies an identifier (a workout, a sleep session, a blood-pressure
reading, a third-party sample with `HKMetadataKeySyncIdentifier`; Fitbit `logId`; Google
`sleep_id`/`exercise_id`), tier 1:

```
pod subject ‖ id space ‖ the raw source identifier
```

For an aggregate the importer computes, which no source names, the digest tier:

```
pod subject ‖ id space ‖ device ‖ metric ‖ statistic ‖ UTC interval ‖ digest of the constituent samples
```

where: **pod subject** is the pod owner's identifier (what that identifier is belongs to spec#63,
pod identity; the seed only requires that it be stable for the life of the pod); **id space** is
`health:sourceIdSpace`, the closed set `healthkit`, `google-health`, `fitbit`, needed because one
Google export holds two id spaces whose values never coincide; **device** is `health:Device`
identity, the normalized name plus hardware model, never the raw Apple string (it embeds a memory
address) and never `manufacturer` (it flips between `Apple` and `Apple Inc.`); **metric** is the
source's own type identifier (`HKQuantityTypeIdentifierRestingHeartRate`, Google's metric name),
never a LOINC or SNOMED code, so a corrected mapping re-mints nothing; **statistic** is
`cascade:statistic`, because a mean and a maximum over one window are two records; **UTC
interval** is `periodStart`/`periodEnd` as Q2 now defines them; and the **digest** covers the
measured field set from Q3 with the device address stripped. Components are length-prefixed rather
than delimiter-joined and hashed through the existing deterministic-identity functions. No record
class in either seed (redundant with the metric or the id space, and a component that can disagree
with itself). One conformance vector is owed before either seed is normative; that vector, and
whether the minter lives in the SDK's layer C or in the cli, are open (see "What remains genuinely
open"). **Accepted cost:** a user who renames a device gets a new device identity and therefore new
identities for subsequent aggregates. That is a split, not a merge: recoverable, and the direction
`identity.ts` says to prefer when identity is uncertain.

### Q2. Where does a day start?

**Why it matters:** which day a 23:30 reading belongs to decides which bucket it is aggregated into,
and therefore the value of two days' records. It also decides whether two exports of the same data
produce the same buckets, which is what identity depends on.

**What measurement found (2026-09-23, two real exports three months apart, write-up tracked
separately):** every one of the 10.2 million
samples in both exports carries the offset `-0700`, across twelve years, ski trips, and `HKTimeZone`
metadata naming Denver, Honolulu and London. The export renders every timestamp in the exporting
device's *current* zone. **There is no per-sample offset in the file.** An earlier draft of this
section recommended "the local day carried in the sample's own offset"; that data does not exist.
Apple does record an IANA zone name as `HKTimeZone` metadata, but only on sleep, workout and
downhill-snow-distance samples (17,485 entries), never on the high-frequency quantity samples that
daily aggregates are built from. The disagreement is not cosmetic: 1.65 million samples (16%) sit
on different sides of midnight in UTC versus the rendered local day.

**What the options imply:**

- **The rendered local day** is stable only while every export is made in the same zone. Export
  from London and every day shifts, so every identity built on the day changes. Reject.
- **The importing machine's local day** is non-deterministic across machines. Reject.
- **UTC** is invariant across exports and machines. Its cost is that a UTC day disagrees with what
  the user saw in the Health app, by the 16% above.
- **A declared zone.** A day is cut in a zone the pod states once (the owner's home zone, a pod
  setting defaulting to the zone the first import ran in). Deterministic because the setting
  travels with the pod rather than with the export, and it agrees with the Health app for anyone
  who lives where the setting says.

**Recommendation:** identity is built from the UTC interval the aggregate covers, and the aggregate
stores that interval explicitly (start and end instants), so the cut is visible in the data rather
than implied. The day is cut in the pod's declared zone, never in the export's rendered offset.
Sessions that carry `HKTimeZone` (sleep, workouts) use the metadata zone for their own local date,
which keeps D4 ("the date it ends") true for them. **Blood pressure does not use a day bucket at
all.** The scope doc's D5 ruled BP is never aggregated (the exact timestamp is the clinically
meaningful unit). Its "473 readings" is the T4 double count it itself warned about: 251 top-level
readings plus 222 repeated inside `<Correlation>` elements. A day-level seed would collide a
morning and an evening cuff reading into one identity. `spec/serialization/index.md` §12.4 is
written per exact reading.

### Q3. What happens when a re-import produces a different value for the same period?

**Why it matters:** this is not hypothetical. Import an export at noon and Tuesday's resting heart
rate is computed from a partial day; re-export on Friday and Tuesday now has a full day of samples
and a different mean. Every user who re-runs an export hits this.

**What the options imply:**

- **Stable identity, last write wins.** One record per day, no reconciler needed, trivially simple,
  and it silently destroys the earlier value. This is the failure direction D-CANONICAL-1 calls
  unrecoverable and `identity.ts` was written to prevent. Reject.
- **Stable identity, amend in place.** What this document's first draft proposed, and it was wrong
  twice over. No protocol-level amend mechanism exists: the nearest thing, `workbench:Amendment`, is
  app-level draft vocabulary that overrides one property on an immutable base record, carries the
  new value on the *overlay* rather than the base (the opposite of what the draft claimed), and
  cannot address a value living on a nested blank node, which several of these readings' values do.
  Beyond the missing mechanism, "one name, changing content" is layer-2 semantics applied to
  layer-1 data, which quietly decides a classification question this document has no business
  deciding alone.
- **Make identity sensitive to the input instead of blind to it.** The first draft excluded sample
  count from the seed specifically so a fuller re-import would resolve to the same identity. That is
  backwards: identity blind to its input is precisely what manufactures merges. If the constituent
  sample set is part of the name, a partial day and a full day are simply two different records,
  both retained, nothing overwritten, which is what "layer 1 only adds" already requires.
- **Refuse to aggregate incomplete days.** A day is aggregated only once it is closed (the export's
  coverage ends strictly after the day does). The partial-day aggregate is then never written in
  the first place, and re-importing a closed day yields a byte-identical aggregate from an identical
  sample set: genuine idempotency rather than idempotency forced by looking away from the data.

**Recommendation: the last two together.** Aggregate only closed days, and name each aggregate with
a digest of the raw samples that fed it (D-CANONICAL-1's existing digest tier for records whose
source supplies no identifier. The digest covers the *input samples*, not the derived aggregate,
so the name stays input-derived exactly as layer 1 requires). Together these dissolve the collision
instead of handling it: the ordinary re-import is a true no-op, and the rare genuine case (a watch
that syncs days late and adds samples to an already-closed day) produces a second record rather
than destroying the first, leaving both visible for layer 2 to reconcile when a wellness reconciler
exists. Until it does, a reader showing "Tuesday's resting heart rate" picks the record from the
**most recent import**, and that choice lives in the application, not in the pod's names. An
earlier draft said "highest sample count"; measurement showed why that is wrong. Of the 34
closed-day buckets whose sample count changed between the June and September exports, 27 shrank.
HealthKit removes samples from closed days (third-party re-syncs, deduplication) more often than a
late sync adds them, and "highest sample count" would keep the pre-deletion aggregate forever.

**Measured, not proposed: the claim holds.** Of 74,969 (type, source, day) buckets closed before
the June export, 74,933 (99.95%) are byte-identical in the September export on the digest fields
below; 34 differ in sample count, 2 in content, and 1 appeared only in September.

**The Apple Health exclusion list, measured.** D-CANONICAL-1 declares one per format (FHIR
`meta.versionId`, `meta.lastUpdated`, `text`), and its amendment records that the unmeasured first
draft of the FHIR list was wrong in two places. The wellness list was measured before being
written. The digest covers `type`, `sourceName`, `unit`, `startDate`, `endDate`, `value`,
`sourceVersion`, `creationDate` and `device` **with the memory address Apple prints inside it
removed** (`<<HKDevice: 0x78a564f00>, name:…`; the `0x…` changes on every export). That address is
the only volatile attribute: with it stripped, all 74,933 matching buckets stay identical with
`sourceVersion` and `creationDate` included. An earlier draft proposed excluding both; neither
needed it. Two further facts for the device axis: `manufacturer:` flips between `Apple` and
`Apple Inc.` by software version, so device identity is built from name and hardware model, never
the raw string; and where Apple carries a source-supplied identifier (`HKMetadataKeySyncIdentifier`
with `SyncVersion` on 48,519 third-party samples, `HKExternalUUID` on 1,767), D-CANONICAL-1's tier
1 applies to that sample and the digest tier does not.

**Some daily aggregates need no aggregation.** The export carries 3,157 `<ActivitySummary>`
elements, one per day, holding Apple's own active energy, exercise minutes and stand hours, already
de-duplicated across sources. Those are source-supplied daily aggregates, input-named by their
date, and are imported as such. Only steps and the vitals need this document's aggregation, which
also removes the source-priority question for the three ring metrics.

**One consequence worth stating plainly:** with the source in the name and no winner picked at write
time, a day on which the watch, the phone and a third-party app all recorded steps yields three
records, not one. That is deliberate. The scope doc's D3 (source priority, Watch > phone >
third-party) is a *reading* rule, and applying it at write time would mean a later import that
changes the winner also changes the identity, churn on top of data loss. Layer 1 records what each
source said; priority is applied by the reader or by layer 2. Measured cost: 77,265 (type, source,
day) units across all 72 sample types in the September export, against 65,722 with a winner picked
per day, an 18% increase. The scope doc's 17,000-20,000 was a clinically useful subset; either way
the result is pod-sized.

## Amendment 2026-09-24: what the second source and the build changed

The Google Health Takeout measurement (write-up tracked separately)
and the health v2.10 build (spec#68, stacked on this branch) settled or moved the following since
this RFC was posted:

- Q1's seed gained an id-space component and a statistic component, and its "sourceName" component
  became the `health:Device` identity; the text above is the current recommendation.
- Q2 holds for Google: its new-format samples are true UTC with no per-sample offset. Zones arrive
  as numeric offsets, never names, so `cascade:dayZone` (core v3.10) has a default chain:
  `HKTimeZone` where present, else the Google profile zone, else the importing machine, logged.
- Q3's closed-day claim is proven for Apple (74,933 of 74,969 buckets) and unproven for Google
  until a second export exists (tracked separately). Google's own daily rollups carry `cascade:date` only
  and take the aggregate shape's Warning rather than a fabricated interval.
- Source-supplied identifiers are stored raw in `health:sourceRecordId`, with the space in
  `health:sourceIdSpace`; the build's first draft wrote `"{space}:{id}"` into one literal and a
  review reversed it so that this seed, not a string grammar, decides identity.
- Apple's `ActivitySummary` is treated as a source in its own right: its three ring values form one
  per-day snapshot with `statistic sum`, step snapshots stay per device, one record per (source, day).
- Nothing here decides T6 (derived interpretations) or the seed vector; both are held for the
  2026-09-24 conversation.

## What remains genuinely open

The recommendations above lean on reading D-CANONICAL-1's digest tier as covering an aggregate whose
constituent samples are the "raw source element". That reading is what lets this proceed without
blocking on rulebook item 1 (creation/merge/split/retire), and it is the part most worth a second
opinion: if a daily aggregate is instead held to be layer-2 data, the naming rule that applies to it
is a different one and Q3's recommendation changes shape. That question is put to review rather than
assumed settled.

## Why the core ruling holds regardless of the above

**The forcing requirement is citation, not the layer-1 naming rule by itself.** Workbench's
evidence-grounding mechanism (`citedRecordIds`) requires a URI-shaped string to link a claim to a
pod fact. A blank node has no such form. The
current `HealthProfileSerializer.swift` (`cascade-sdk-swift`, lines ~187-196, ~850-858) emits
exactly this shape today, with no per-entry identifier of any kind. Wellness data in the current
shape cannot durably ground an answer, independent of how Q1-Q3 are eventually resolved. Whatever
the seed formula and reconciliation rule end up being, the entries need to be individually
addressable, which a blank node structurally cannot be.

**D-CANONICAL-1 already treats blank-node subjects as a symptom of failure, not a sanctioned
choice for source data.** Its own measurement (`2026-09-05-two-layer-pod.md:181`) names "250 of 448
typed subjects are blank nodes" as evidence the reference pod "cannot show layer 1." A wellness
reading, imported directly from a source export with no clinical judgment applied, is exactly the
kind of record that measurement is about, though, per "What remains genuinely open" above, whether
a daily *aggregate* is layer 1 in D-CANONICAL-1's strict "named from input, never edited" sense is
the one question this document leans on rather than settles.

**Minting must go through this codebase's existing deterministic-identity discipline, not around
it.** `cascade-cli/src/lib/identity.ts` documents the governing rule (prefer a split over a merge)
and `tests/identity-chokepoint.test.ts` enforces that every identity-minting call
(`deterministicUuid`, `contentHashedUri`, `identitySeed`, `identityKey`, `medicationUri`) uses
deterministic arguments, never `Math.random()`, `randomUUID()`, or a per-run timestamp. Several
converters already call `deterministicUuid` directly with a hand-built seed string; a wellness
minter should do the same, seeded per Q1.

## Consequences

- `spec/serialization/index.md` §12 is revised in this same change: the pattern statement (§12.2)
  and the `*History`-list examples (§12.3, §12.4, §12.5, §12.6, §12.11) show named individuals; the
  "latest reading" convenience properties (§12.3.1, §12.7's `heartRateVariability`, all of §12.9)
  are explicitly left as blank nodes with a note explaining why.
- The wellness aggregator scope decision's D1 (tracked separately): the blank-node-vs-named-individual
  half of D1 is resolved for `*History` entries by this document; Q1-Q3 carry recommendations that
  silence accepts. D2 (five undeclared `cascade:` predicates) is separately about 80% resolved: `date`,
  `sourceType`, `sampleCount` and `loincCode` landed in core v3.4 (commit `24681e2`, 2026-08-03);
  `snomedCode` was never declared and needs its own decision. All three tracked touchpoints are
  updated in this same change.
- **New follow-up filed:** the "latest reading" convenience-property domain/range
  conflict this document found but did not fix.
- **The two measurements this document owed are done** (2026-09-23, two real exports diffed;
  write-up tracked separately). They overturned the first
  draft's Q2 and its reader tiebreak, and settled the exclusion list. Still owed before Q1-Q3 are
  normative: one conformance vector for the seed. D-CANONICAL-1's own amendment exists because an
  unmeasured naming rule was wrong in two places; this document has now had the same experience
  and records it rather than hiding it.
- The TS wellness aggregator (`cascade-cli`) can be built on the recommendations above without
  waiting for rulebook item 1. If Q3's reading of the digest tier is rejected on review, the
  aggregator's naming changes and pods written before that are re-minted, which is the reason to
  settle it before the build rather than during.
- This document does not touch `cascade-sdk-swift`'s `HealthProfileSerializer.swift`. It serves a
  different path (live HealthKit → pod, not Apple Health export → pod) with existing production
  pods (POTS Check, shipping on the App Store) already written in the blank-node shape. Whether it
  is ever migrated is a separate, lower-priority decision, tracked as its own backlog follow-up.
