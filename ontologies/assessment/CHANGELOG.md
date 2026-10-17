# Assessment Vocabulary Changelog

`assessment:` (`https://ns.cascadeprotocol.org/assessment/v1#`) describes standardized rating
instruments as published, the responses raters give to them, multi-rater response waves, and the
scores and screen results an instrument's own published scoring rules define.

## v1.0 - 2026-10-16

First ratified release. The 0.1 draft (2026-08-05) was staged outside this repository at the same
namespace, so this release is ratified in place: every term that kept its meaning kept its IRI.
`assessment.shapes.ttl` v1.0 and `contexts/v1/assessment.jsonld` are new.

Counts: 18 classes, 38 properties (28 datatype, 10 object), 9 named individuals. Against the
draft's 17 classes, 70 properties and 8 individuals: 54 terms kept, 11 added, 41 removed.

### Removed: a ratified standard already defines the term

Each removed draft term is replaced by the standard term on the right. Data written against the
draft keeps its subject IRIs (identity keys use values, not predicate names) but must be rewritten
predicate by predicate.

| Draft term | Replaced by |
|---|---|
| `instrumentId`, `itemId`, `scaleId`, `screenId`, `responseScaleId` | `dct:identifier` |
| `instrumentTitle` | `dct:title` |
| `instrumentCitation` | `dct:bibliographicCitation` |
| `instrumentAttribution` | `dct:rights` |
| `hasItem`, `hasScale`, `hasItemResponse` | `dct:hasPart` |
| `memberOfScale`, `inWave` | `dct:isPartOf` |
| `aboutSubject` | `dct:subject` |
| `draftVocabulary` | `dct:conformsTo` |
| `draftVocabularyVersion` | `cascade:schemaVersion` |
| `displayLabel`, `scaleLabel`, `screenLabel`, `producerName` | `rdfs:label` |
| `responseValue`, `scoreValue` | `rdf:value` |
| `itemNumber`, `waveNumber` | `schema:position` |
| `hasAssignment` | `prov:hadMember` (a wave is a `prov:Collection`) |
| `inSetting` | `prov:atLocation` |
| `dataAbsentReason` | `cascade:dataAbsentReason` (core v3.6; all 15 FHIR codes) |
| `instrumentCode`, `itemCode`, `scaleCode` | `cascade:loincCode` |
| `algorithmVersion` | `health:algorithmVersion` |
| `producerVersion` | `cascade:version` |
| `caseReference` | `cascade:sourceRecordId` |
| `BundleFile`, `hasFile`, `filePath`, `fileDigestSha256` | SPDX 2.3 `spdx:File`, `spdx:hasFile`, `spdx:fileName`, `spdx:checksum` |

### Removed without replacement

- **`responseLabel`.** The label of a chosen value is the `skos:prefLabel` of the matching
  `assessment:ResponseOption`, which every serialized instrument now carries.
- **`subjectDisplayLabel`.** The manifest names the subject with `dct:subject`, and the subject
  node's own `rdfs:label` is repeated in the manifest file.
- **`draftVocabularyStatus`.** `cascade:schemaVersion` already says which version a bundle uses;
  a 0.x version is a draft.
- **`fileByteCount`.** A file's checksum is what a consumer verifies. `dcat:byteSize` is defined on
  `dcat:Distribution` and `cascade:byteSize` on `cascade:Attachment`, and reusing either on a bundle
  file would assert a class the file is not.

### Added

- **`ResponseScale`** (a `skos:ConceptScheme`) and **`ResponseOption`** (a `skos:Concept`): every
  instrument carries, for each response scale it uses, every permitted value (`skos:notation`), the
  label the edition prints for it (`skos:prefLabel`), and **`problemEnd`**, which end of the scale
  is the problem end. **`usesResponseScale`** links an item to its scale. Editions of one
  instrument can run the same scale in opposite directions, so a raw answer is read against its
  edition's definition and never rewritten.
- **`ratingWindowKind`** and **`ratingWindowDuration`** on an instrument: the period the edition
  asks a rater to think about. The period a particular response set describes uses
  `health:periodStart` and `health:periodEnd`.
- **`medicationStatusAtRating`**: the rater's own answer to whether the rated period was a time on
  medication, as a LOINC answer code (LA34443-4 Was on medication, LA34444-2 Was not on medication,
  LA12693-0 Not sure).
- **`treatmentPeriod`**: a link from a response set to the record of the treatment period its
  window fell in. No range is stated and no class for the period is defined here.
- **`raterObservationLength`**: how long the rater says they could observe, as they stated it.
- **`consentTextVersion`**: which notice or consent text a rater acknowledged.
- **`CaregiverRater`**: a non-parent caregiver at home.

### Changed

- **`instrumentVersion`** is required and names the published edition. The producer's own
  reproduction of that edition is `schema:version`.
- **`assignmentStatus`** takes the HL7 FHIR R4 task-status codes (normally `requested`,
  `in-progress`, `completed`, `cancelled`) in place of the draft's `invited`, `started`,
  `completed`, `revoked`.
- **Identity keys** of `Instrument`, `Item` and `Scale` now include the edition and the
  reproduction version, and `ResponseScale` and `ResponseOption` have keys of their own. Subject
  IRIs of those classes therefore differ from the draft's. All other keys are unchanged. A key
  segment may not contain `:`, and the shapes enforce it.
- **Inputs hash.** `cascade-assessment-inputs-sha256-v2` (length-framed, binds the instrument and
  the algorithm version) is accepted and is what producers write. `-v1` keeps its meaning, is
  accepted on read, and draws a Warning.
- **Answers** are numeric literals (`xsd:integer` or `xsd:decimal`), one of the item's options.
- **The item shape is closed**: an item carries only its identifier, printed position, response
  scale, scale membership and LOINC code, so no predicate can carry item wording.
- **Cross-property invariants** are in the shapes, all in SHACL Core: counts never exceed what
  they count, a score is counted or computed but not both, an answer has a value or an absence
  reason but not both, a screen has a verdict or an absence with the missing input but not both,
  an assignment is completed exactly when it has a response set, every assignment is listed by its
  wave, the rated period does not run backwards, and a fixed look-back window has a duration.
- **`BundleManifest`** is no longer declared a subclass of `cascade:ExportManifest`; manifests are
  typed as both in data. The subclass axiom would require the assessment manifest shape to reach
  the core export-manifest shape by `sh:node`, which carries Warning-severity constraints
  (validation rule S5).
