# D-WELLNESS-1: A wellness reading is a named individual; only its compound sub-values stay blank nodes

**Status:** Proposed; direction ratified by Jed Reinitz on 2026-09-19 for the vocabulary/shapes
question within his tie-break domain (`planning/collaboration/working-agreement.md` r3), open for
Jay's review before merge per the same agreement. RFC issue: the-cascade-protocol/spec#64.
**Date:** 2026-09-19
**Proposed by:** Jed Reinitz
**Prompted by:** D1 in `cascade-workbench/docs/planning/2026-07-29-apple-health-wellness-aggregator-scope.md`
(lines 138-146, 378), filed against root backlog 2.24 / Workbench `[WELLNESS-IMPORT]` while scoping
the Apple Health wellness aggregator. Applies D-CANONICAL-1's identity principle to a class of
record that document did not name.

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
nodes, unchanged, until that conflict is settled on its own terms (filed as root backlog 3.472,
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

**Recommendation:** seed from `pod subject identifier ‖ Apple's own type identifier ‖ sourceName as
the export states it ‖ the time bucket (Q2) ‖ a digest of the constituent samples (Q3)`,
length-prefixed rather than delimiter-joined, hashed through the existing deterministic-identity
functions. No record class. No LOINC or SNOMED code. Write one conformance vector before it is
normative. **Accepted cost:** a user who renames their watch gets a new source string and therefore
new identities for subsequent days. That is a split, not a merge: recoverable, and the direction
`identity.ts` says to prefer when identity is uncertain.

### Q2. Where does a day start?

**Why it matters:** Apple's timestamps carry local UTC offsets. Which day a 23:30 reading belongs to
decides which bucket it is aggregated into, and therefore the value of two days' records.

**What the options imply:**

- **UTC day** is deterministic and machine-independent, but disagrees with what the user saw in the
  Health app. For a user at UTC+13, nearly every evening reading shifts to the following day; the
  pod would report a different resting heart rate for a given date than the phone in their pocket.
- **The importing machine's local day** is non-deterministic across machines: the same export
  imported on a laptop in Denver and a desktop in London buckets differently. This one is simply
  wrong; it is named here only because it is the default a naive implementation falls into.
- **The local day carried in the sample's own UTC offset** is deterministic (the offset travels
  inside the data, not from the environment) and agrees with the Health app. Its cost is that DST
  transitions produce 23- and 25-hour days and travel can make two "local days" overlap. Both are real, but
  they affect which samples land in a bucket, never whether two importers agree.

**Recommendation:** the local day as recorded in the sample's own offset. This is the same reasoning
the scope doc's D4 already accepted for sleep ("the date it ends... matches how the Health app
presents it, so the app and the pod agree"); extending it to day boundaries generally is
consistency, not a new position. **Blood pressure does not use a day bucket at all.** The scope
doc's D5 ruled BP is never aggregated (the exact timestamp is the clinically meaningful unit, and
473 readings across eight years is already pod-sized). A day-level seed would collide a morning and
an evening cuff reading into one identity. `spec/serialization/index.md` §12.4 is written per
exact reading.

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
exists. Until it does, a reader showing "Tuesday's resting heart rate" picks the record with the
highest sample count, and that choice lives in the application, not in the pod's names.

**This needs an Apple Health exclusion list**, the same way D-CANONICAL-1 declares one per format
(FHIR `meta.versionId`, `meta.lastUpdated`, `text`). Proposed: digest over `type`, `sourceName`,
`unit`, `startDate`, `endDate` and `value`; exclude `sourceVersion`, `device` and `creationDate`,
all of which churn on app and firmware updates without the reading changing. Measure this against
the real export before it is normative. D-CANONICAL-1's own amendment found that an unmeasured
exclusion list was wrong in two places.

**One consequence worth stating plainly:** with the source in the name and no winner picked at write
time, a day on which the watch, the phone and a third-party app all recorded steps yields three
records, not one. That is deliberate. The scope doc's D3 (source priority, Watch > phone >
third-party) is a *reading* rule, and applying it at write time would mean a later import that
changes the winner also changes the identity, churn on top of data loss. Layer 1 records what each
source said; priority is applied by the reader or by layer 2. This raises the estimated record count
above the scope doc's 17,000-20,000, plausibly to 30,000-50,000 for a multi-source export. Still
pod-sized, and measurable before the build.

## What remains genuinely open

The recommendations above lean on reading D-CANONICAL-1's digest tier as covering an aggregate whose
constituent samples are the "raw source element". That reading is what lets this proceed without
blocking on rulebook item 1 (creation/merge/split/retire), and it is the part most worth a second
opinion: if a daily aggregate is instead held to be layer-2 data, the naming rule that applies to it
is a different one and Q3's recommendation changes shape. That question is put to review rather than
assumed settled.

## Why the core ruling holds regardless of the above

**The forcing requirement is citation, not the layer-1 naming rule by itself.** Workbench's
evidence-grounding mechanism (`citedRecordIds`, `cascade-workbench/packages/claims/src/runner.ts:119`)
requires a URI-shaped string to link a claim to a pod fact. A blank node has no such form. The
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
- Root backlog 2.24 / Workbench `[WELLNESS-IMPORT]`: the blank-node-vs-named-individual half of D1
  is resolved for `*History` entries by this document; Q1-Q3 carry recommendations that silence
  accepts. D2 (five undeclared `cascade:` predicates) is separately about 80% resolved: `date`,
  `sourceType`, `sampleCount` and `loincCode` landed in core v3.4 (commit `24681e2`, 2026-08-03);
  `snomedCode` was never declared and needs its own decision. All three backlog touchpoints are
  updated in this same change.
- **New follow-up filed:** root backlog 3.472, the "latest reading" convenience-property domain/range
  conflict this document found but did not fix.
- **Two measurements are owed before Q1-Q3 are normative**, both cheap against the 4.2 GB export
  already on hand: the Apple Health exclusion list (which sample attributes churn without the
  reading changing), and the real record count under per-source writing. D-CANONICAL-1's own
  amendment exists because an unmeasured naming rule was wrong in two places; this one should not
  repeat that.
- The TS wellness aggregator (`cascade-cli`) can be built on the recommendations above without
  waiting for rulebook item 1. If Q3's reading of the digest tier is rejected on review, the
  aggregator's naming changes and pods written before that are re-minted, which is the reason to
  settle it before the build rather than during.
- This document does not touch `cascade-sdk-swift`'s `HealthProfileSerializer.swift`. It serves a
  different path (live HealthKit → pod, not Apple Health export → pod) with existing production
  pods (POTS Check, shipping on the App Store) already written in the blank-node shape. Whether it
  is ever migrated is a separate, lower-priority decision, tracked as its own backlog follow-up.
