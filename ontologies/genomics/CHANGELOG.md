# Genomics Vocabulary Changelog

All notable changes to the `genomics/` vocabulary are documented here. The
namespace is `https://ns.cascadeprotocol.org/genomics/v1#`. Pre-stable drafts
(`v1-draft`) are not registered in `spec/VOCAB_VERSIONS` per D-PATH; they land
there at v1.0 graduation.

## v1-draft.0.2 — 2026-05-05

Phase 1 evolution candidates landed after the FHIR Genomics IG importer
session surfaced gaps. All four are additive (no breaking changes):

### Added — generic GeneticTest linkage

- `genomics:reportedRecord` (ObjectProperty, no rdfs:range — deliberately
  broad). Generic predicate for GeneticTest → Diplotype / Haplotype / PGx
  implication / future genomics record links. Resolves the HLA tie-break
  raised in TASK-1.9 (cascade-coordination/tie-breaks/2026-05-05-task-1.9-hla-variantsObserved.md):
  the existing genomics:variantsObserved has rdfs:range genomics:Variant
  and cannot represent non-Variant report links.

### Added — VCF-style coordinate properties

- `genomics:refAllele`, `genomics:altAllele`, `genomics:genomicStartEnd` —
  required for VCF importer (Phase 3) and for FHIR Genomics IG variants
  that lack HGVS but carry the LOINC 69547-8/69551-0/81254-5 components
  directly. These were emitted as gap-warnings throughout Phase 1.

### Added — variant origin

- `genomics:somaticStatus` ObjectProperty + `SomaticStatus` enum with
  three named individuals: `Germline`, `Somatic`, `UnknownSomaticStatus`.
  Maps LOINC 48002-0. Critical for cancer + inheritance reasoning.

### Added — variant allele frequency

- `genomics:variantAlleleFrequency` (DatatypeProperty, xsd:decimal,
  SHACL-bounded 0.0–1.0). Distinct from existing `mosaicismFraction`:
  VAF is a sequencing-evidence fraction; mosaicism is the clinical
  conclusion that the variant is present in only a subset of cells. The
  Phase 1 importer was shoehorning VAF into mosaicismFraction; importers
  should now emit VAF on this property.

### Deferred to later draft revisions

These Phase 1 candidates are NOT included in v0.2; they need Ellen
review or more diverse importer experience first:
- `genomics:CompositeVariant` (only one Phase 1 example)
- LOINC 48013-7 Genomic ref-seq, 48019-4 DNA change type, 48001-2
  cytogenetic location (lower frequency, multiple modeling options)
- Multi-gene Diplotype (architectural change)
- SNOMED reaction-coding system in condition mappings (out-of-band)

## v1.0-draft.0.1 — 2026-05-05

Initial production version of `genomics/v1-draft`, authored in `spec/` from
the v0.1 sketch at `cascadeprotocol.org/drafts/genomics-v1/genomics.ttl`. This
release covers TASK-0.1 of the Genomics & Advisory v0.1 workstream.

### Added — variant identity (carried over from v0.1)

- `genomics:Variant` class (subClassOf `fhir:Observation`, `prov:Entity`).
- HGVS properties: `hgvsCDot`, `hgvsPDot`, `hgvsGDot`, `hgvsProteinObserved`,
  `transcriptRef`, `genomeAssembly`.
- Stable identifier properties: `clinvarVariationId`, `clinvarRcvId`,
  `dbsnpRsId`, `caId`, `vrsId`, `vrsObject`.
- Gene + consequence: `geneSymbol`, `hgncId`, `consequenceTerm` (SO URI),
  `consequenceLabel`.
- Zygosity + phase: `zygosity`, `phase`, `phasedWith`.

### Added — variant interpretation (carried over from v0.1)

- `genomics:VariantInterpretation` class (per D-Q5: cardinality 1..1 on
  `condition` and `variantInterpreted`, multi-condition cases produce
  multiple interpretation instances).
- ACMG/AMP properties: `acmgClassification`, `acmgCriteria`.
- Condition properties: `condition`, `mondoId`, `omimId`, `orphaCode`.
- Inheritance: `inheritanceMode`, `allelicRequirement`.
- Provenance: `interpretedBy`, `interpretedDate`.
- ACMG class named individuals: `Pathogenic`, `LikelyPathogenic`, `VUS`,
  `LikelyBenign`, `Benign` (LOINC answer codes annotated).
- Inheritance named individuals: `AutosomalDominant`, `AutosomalRecessive`,
  `XLinkedDominant`, `XLinkedRecessive`, `Mitochondrial`, `YLinked`,
  `MultifactorialPolygenic`, `UnknownInheritance`.
- Allelic requirement named individuals: `Monoallelic`, `Biallelic`.
- Zygosity named individuals: `Heterozygous`, `Homozygous`, `Hemizygous`,
  `CompoundHeterozygous`, `MosaicLow`, `MosaicHigh`.
- Phase named individuals: `Cis`, `Trans`, `PhaseUnknown`.

### Added — pedigree (carried over from v0.1)

- `genomics:Pedigree`, `genomics:PedigreeMember` classes.
- Properties: `proband`, `hasMember`, `relativeRole`, `relativeSex`,
  `isDeceased`, `ageAtDeath`, `carrierStatus`, `testedForVariant`,
  `hpoTerm`, `phenotypeOnsetAge`.
- Carrier status named individuals: `PositiveAffected`, `PositiveUnaffected`,
  `Negative`, `NotTested`, `Obligate`.
- HL7 v3 RoleCode named individuals on `RelationshipRole`: `Proband`,
  `MTH`, `FTH`, `SIS`, `BRO`, `DAU`, `SON`, `MAUNT`, `MUNCLE`, `PAUNT`,
  `PUNCLE`, `MGRMTH`, `MGRFTH`, `PGRMTH`, `PGRFTH`, `MCOUSN`, `PCOUSN`,
  `NIECE`, `NEPHEW`. (NEW in v1.0-draft.0.1 — not declared in v0.1, but
  used by the BRCA2 example.)

### Added — genetic test (carried over from v0.1)

- `genomics:GeneticTest` class.
- Properties: `testType`, `genePanel`, `variantsObserved`,
  `orderingProvider`, `performingLab`.
- Test type named individuals: `SingleGeneTest`, `GenePanelTest`,
  `ExomeSequencing`, `GenomeSequencing`, `ChromosomalMicroarray`,
  `KaryotypeAnalysis`, `MLPA`, `RepeatExpansionTest`, `MethylationStudy`,
  `RNASequencing`.

### Added — gap fold-ins (per GAP-ANALYSIS.md)

- `genomics:Haplotype` class — multi-variant unit traveling on one
  chromosome (PharmVar star alleles, HLA typing). Anchored on
  `fhir:Observation` per FHIR Genomics IG haplotype profile.
- `genomics:Diplotype` class — pair of haplotypes (e.g., `*1/*2`).
  Anchored on `fhir:Observation` per FHIR Genomics IG genotype profile.
- `genomics:CopyNumberVariant` class subClassOf `Variant`.
- `genomics:hasComponent`, `starAlleleSymbol`, `diplotypeNotation`,
  `hapA`, `hapB`.
- `genomics:copyNumber`, `cnvIntervalStart`, `cnvIntervalEnd`,
  `cnvIntervalRef`.
- `genomics:mosaicismFraction` (xsd:decimal) — continuous VAF
  complementing the categorical `MosaicLow`/`MosaicHigh` zygosity values.
- `genomics:SubmitterAssertion` class + 7 properties (`assertedClassification`,
  `submitter`, `submitterOrgId`, `submitterCategory`, `scvAccession`,
  `contributesToAggregate`, `assertionEvidenceLevel`).
- `genomics:aggregatedFrom` linking `VariantInterpretation` to its
  contributing `SubmitterAssertion` records (ClinVar VCV/SCV pattern).
- `SubmitterCategory` named individuals: `SubmitterLaboratory`,
  `SubmitterConsortium`, `SubmitterExpertPanel`, `SubmitterResearch`,
  `SubmitterClinician`.
- `genomics:GeneticTestOrder` class subClassOf `fhir:ServiceRequest`.
- Order properties: `orderedAt`, `orderStatus`, `resultedIn`.
- Order status named individuals: `OrderPending`, `OrderInProgress`,
  `OrderResulted`, `OrderCancelled`.
- `genomics:interpretationStatus` property + `CausalityStatus` enum
  (`Causative`, `Contributory`, `UncertainCausality`, `Rejected`)
  — Phenopacket-aligned variant-explains-phenotype semantics, distinct
  from ACMG classification.
- `genomics:reviewStatus` property + 7-value `ReviewStatus` enum
  matching the ClinVar review-status taxonomy (`NoAssertionProvided`,
  `CriteriaNotProvided`, `SingleSubmitter`, `ConflictingSubmissions`,
  `MultipleSubmittersNoConflict`, `ExpertPanelReviewed`,
  `PracticeGuideline`) with `starRating` annotation.

### Added — directory-session metadata (per D-DIRECTORY)

- `genomics:SequencingRun` class subClassOf `prov:Activity`.
- `genomics:RawFile` class subClassOf `prov:Entity`. Pointer-and-hash
  representation; Cascade does NOT ingest the bytes (per Critical
  conventions #9).
- Sequencing properties: `coverageDepth`, `sequencingTechnology`,
  `variantCallerVersion`, `laboratoryCertification`,
  `sampleCollectionDate`, `sequencingDate`, `fileGenerationDate`.
- Raw-file properties: `fileFormat`, `fileSizeBytes` (xsd:long for the
  50–100 GB BAM/CRAM cases), `fileHashSHA256`, `fileLocation`
  (xsd:anyURI; not validated by Cascade), `referenceGenome`,
  `htsgetEndpoint`.
- Sequencing technology named individuals: `ShortReadIllumina`,
  `LongReadONT`, `LongReadPacBio`, `Mixed`, `GenotypingArray`.
- Laboratory certification named individuals: `CLIA`, `CAP`,
  `ISO15189`, `Uncertified`.
- File format named individuals: `BAM`, `CRAM`, `FASTQ`, `gVCF`, `VCF`,
  `BCF`, `OtherFileFormat`.
- `genomics:dataProvenance` property + `DataProvenance` enum:
  `ConsumerArray`, `ClinicalSequencing`, `ResearchSequencing`,
  `Imported`, `AIExtractedGenomics`. Distinct from `cascade:dataProvenance`
  (broader consumer-vs-clinical classification) — this is genomics-specific
  because the consumer-array lane drives Phase 2C importer behavior.

### Added — data quality tier model (per D-QUALITY-TIER)

- `genomics:dataQualityTier` ObjectProperty on `Variant`.
- `genomics:DataQualityTier` class.
- Quality tier named individuals with rdfs:comment defining the criterion:
  `ClinicalGrade` (CLIA/CAP/ISO15189 + clinical-grade method like ≥30x
  WGS or validated panel + raw files), `ResearchGrade`, `ConsumerGrade`
  (DTC genotyping arrays explicitly land here), `UnknownQuality`.
- `genomics:requiresConfirmation` (xsd:boolean) on `VariantInterpretation`.
  SHACL safety constraint (TASK-0.2): any Pathogenic / LikelyPathogenic
  interpretation MUST either reference a ClinicalGrade Variant OR carry
  `requiresConfirmation true`.

### Design decisions made under uncertainty

- **Haplotype/Diplotype superClass.** Resolved to `fhir:Observation` after
  inspecting `Bundle-bundle-pgxexample.json` in the FHIR Genomics IG
  reference corpus. Both `haplotype` and `genotype` profiles in that bundle
  use `resourceType: Observation`. Adopted the same anchor for consistency
  with `genomics:Variant`.
- **Genomics-specific dataProvenance.** `cascade:dataProvenance` already
  exists in `core/v1`. Authored a parallel `genomics:dataProvenance` enum
  rather than reusing or subclassing the core one because the genomics
  importer routing is structurally different (ConsumerArray drives Phase 2C
  auto-tagging; ClinicalSequencing drives lab-cert tier inference). The
  two coexist; downstream interpreters can correlate them.
- **`UnknownCausality` named individual.** Renamed from the GAP-ANALYSIS
  draft `Uncertain` (the symbol `genomics:Uncertain` would have collided
  with the conceptual VUS class label and been ambiguous in casual reading).
  The CausalityStatus enum uses the longer-form `UncertainCausality`.
- **`OrderPending` / `OrderInProgress` / etc. prefix.** Used `Order`-prefix
  for the OrderStatus enum to avoid collision with the bare `Pending`
  symbol that may appear in advisory or other vocabularies.
- **`OtherFileFormat`** (vs. bare `Other`). Avoids collision with potential
  `Other`-named individuals in other vocabularies as the protocol grows.
- **`AIExtractedGenomics`** (vs. bare `AIExtracted`). The cascade core
  vocabulary already declares `cascade:AIExtracted` as a DataProvenance
  subclass; the genomics-specific lane is named distinctly to avoid
  cross-namespace symbol collision in casual SPARQL queries.

### Out of scope (future tasks)

- SHACL shapes file (`genomics.shapes.ttl`) — TASK-0.2.
- Layer 3 checkup additions (`GeneticCounselingSummary`, `VariantNarrative`)
  — separate checkup-vocab task.
- PGx vocabulary stubs — TASK-0.7.
- Downstream sync to `cascadeprotocol.org` — TASK-0.6.

### Validation

- `riot --validate` — passes with no errors or warnings.
- `rapper -i turtle --count` — 790 triples parse cleanly.
- BRCA2 counseling smoke test — all 62 `genomics:` terms used by
  `cascadeprotocol.org/drafts/genomics-v1/example-brca2-counseling.ttl`
  are declared in this ontology.
