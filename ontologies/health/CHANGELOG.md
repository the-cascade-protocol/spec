# Health Vocabulary Changelog

This file starts at v2.12. The history of v1.0 to v2.11 is the changelog block
at the top of `v1/health.ttl`, which remains the full record for every
version, this one included.

## v2.12 - 2026-09-26

The deferred wellness metrics: sleep sessions assembled from stage segments,
blood pressure, VO2 max and basal energy, each checked against the ratified
standards and the platforms' published models before an importer writes it,
plus two LOINC annotations that claimed more than their codes mean. Paired
with clinical v1.21. `health.shapes.ttl` goes to v1.10.

**Added**

- **`health:isMainSleep`** (`xsd:boolean`, domain `health:SleepSession`):
  IEEE 1752.1 sleep-episode
  [`is_main_sleep`](https://w3id.org/ieee/ieee-1752-schema/sleep-episode.json),
  written only where the source supplies the flag (Fitbit `isMainSleep`,
  WHOOP `nap` negated). Absent is not false; Apple supplies none, and the
  main sleep of an Apple date is a derived view.
- **`health:basalEnergyKcal`** (`xsd:decimal`, domain
  `health:DailyActivitySnapshot`): basal (resting) energy burned over a day,
  summed per (source, device, day) from HealthKit
  [`basalEnergyBurned`](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/basalenergyburned)
  samples, `cascade:statistic "sum"`. A distinct property because no LOINC
  code separates basal from active energy over an interval; no LOINC
  annotation. Energy, not a rate: a basal metabolic rate is never written
  here, and LOINC 50042-1 is not a metabolic rate.

**Changed**

- **`health:sourceIdSpace`**: `rdfs:domain` widens from `health:Workout` and
  `health:SleepSession` to the union with `health:DailyVitalReading`,
  `health:DailyActivitySnapshot` and `health:DailySleepSnapshot`, since the
  D-WELLNESS-1 name seed carries the id space on every wellness record. The
  closed range (`healthkit`, `google-health`, `fitbit`) is unchanged.
- **`health:vo2Max`**: LOINC 60842-2 removed (it is oxygen consumption in
  mL/min, not VO2 max per kilogram) and no code substituted. The comment maps
  each source method value to measured or estimated.
- **`health:activeEnergyBurnedKcal`**: its LOINC 41981-2 annotation is kept
  but corrected: 41981-2 means "Calories burned" of any kind and is broader
  than the property. Active versus basal is carried by the property.
- **`health:SleepSession`** comment: a night is dated by the day of waking in
  the session's recorded zone, falling back to the pod's `cascade:dayZone`;
  naps are separate sessions; a source's own sessions (Google, Fitbit, Health
  Connect) are never regrouped; Apple stage segments are grouped at a one-hour
  gap, with a run of `awake` of an hour or more counting as a gap; the raw
  segments are retained as the session's samples and linked by
  `prov:wasDerivedFrom`.
- **`health:BloodPressureReading`** and **`health:BPStatistics`** comments:
  one paired reading per record (FHIR panel 85354-9, components 8480-6 and
  8462-4), never bucketed by day; an average is a view, coded LOINC 96607-7 if
  ever stored.
- Comments on `health:activeEnergyKcal`, `health:VitalSignReading`,
  `health:DailyVitalReading` and `health:DailyActivitySnapshot` point to the
  above.

**Reused, not minted**

- The VO2 max method is **`clinical:measurementMethod`** (FHIR
  `Observation.method`), whose `rdfs:domain clinical:VitalSign` clinical v1.21
  drops. Values are the source's own, namespaced: the four HealthKit
  `HKVO2MaxTestType` cases, the six Health Connect `Vo2MaxRecord` methods, and
  Google's two daily series.
- The Apple sleep grouping rule is recorded as the session's generating
  activity's **`cascade:version`** (`"{rule}/{version}"`), the form the
  computed daily aggregates carry. Rejected: `health:algorithmVersion` (the
  source's own algorithm, verbatim), `sosa:usedProcedure` (how an observation
  is made, not how a record is assembled), `prov:hadPlan` (reached only
  through a qualified association).

**SHACL (`health.shapes.ttl` v1.10)**, all `sh:Warning`:
`health:AggregateReadingShape` binds `health:sourceIdSpace`; new
`health:SleepSessionSoftShape` (`isMainSleep`), `health:DailyActivitySoftShape`
(`basalEnergyKcal`), `health:BloodPressureReadingShape` (subjects of
`health:systolic` / `health:diastolic`: exactly one of each) and
`health:MeasurementMethodShape` (subjects of `clinical:measurementMethod`
other than a `clinical:VitalSign`: the closed method set). The last two target
a predicate rather than a class.

**JSON-LD:** `isMainSleep` and `basalEnergyKcal` in `health.jsonld` and the
merged `cascade.jsonld`. `measurementMethod` was already mapped in
`clinical.jsonld` and `cascade.jsonld`.

**Compatibility:** additive. Nothing that validated under v2.11 stops
validating; every new finding is at `sh:Warning`. Removing an annotation and
widening a domain add no constraint.
