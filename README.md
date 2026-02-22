# Cascade Protocol Specification

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Spec Status](https://img.shields.io/badge/status-stable-green.svg)]()

The canonical specification for the Cascade Protocol: ontology files (OWL/Turtle), SHACL validation shapes, serialization rules, and JSON-LD contexts.

## Overview

Cascade Protocol defines a three-layer semantic vocabulary for health data:

| Layer | Namespace | Prefix | Purpose |
|---|---|---|---|
| Core | `https://ns.cascadeprotocol.org/core/v1#` | `cascade:` | Identity, provenance, Pod structure |
| Health | `https://ns.cascadeprotocol.org/health/v1#` | `health:` | Wellness and device data |
| Clinical | `https://ns.cascadeprotocol.org/clinical/v1#` | `clinical:` | EHR/clinical record data |
| Coverage | `https://ns.cascadeprotocol.org/coverage/v1#` | `coverage:` | Insurance and coverage |
| Checkup | `https://ns.cascadeprotocol.org/checkup/v1#` | `checkup:` | Patient-facing health summaries |
| POTS | `https://ns.cascadeprotocol.org/pots/v1#` | `pots:` | POTS-specific test data |

Each vocabulary maps to established standards (FHIR, SNOMED CT, LOINC, RxNorm) while providing patient-owned, local-first semantics.

## Repository Structure

```
spec/
  ontologies/
    core/v1/
      core.ttl              # Core ontology (OWL)
      core.shapes.ttl       # SHACL validation shapes
    health/v1/
      health.ttl            # Health ontology
      health.shapes.ttl     # SHACL shapes
    clinical/v1/
      clinical.ttl          # Clinical ontology
      clinical.shapes.ttl   # SHACL shapes
    coverage/v1/
      coverage.ttl          # Coverage ontology
      coverage.shapes.ttl   # SHACL shapes
    checkup/v1/
      checkup.ttl           # Checkup ontology
      checkup.shapes.ttl    # SHACL shapes
    pots/v1/
      pots.ttl              # POTS ontology
      pots.shapes.ttl       # SHACL shapes
  serialization/
    turtle-rules.md         # Turtle serialization conventions
    pod-structure.md        # Pod directory layout spec
  contexts/
    cascade-v1.jsonld       # JSON-LD context for all vocabularies
  CHANGELOG.md
```

## Vocabulary Versions

| Vocabulary | Current Version | Classes | Properties |
|---|---|---|---|
| Core | 1.3 | PatientProfile, Address, EmergencyContact, PharmacyInfo, Pod, Container | ~25 |
| Health | 1.3 | HealthProfile, WellnessStatistic | ~15 |
| Clinical | 1.3 | MedicationRecord, ConditionRecord, AllergyRecord, LabResult, VitalSign, ImmunizationRecord | ~40 |
| Coverage | 1.0 | InsurancePlan | ~12 |
| Checkup | 1.0 | CheckupSummary | ~10 |
| POTS | 1.0 | POTSTest, HeartRateMeasurement | ~8 |

## SHACL Shapes

Each vocabulary includes SHACL shapes that define validation constraints:

- **Required fields** (`sh:minCount 1`) -- e.g., every MedicationRecord must have a `medicationName`
- **Value enumerations** (`sh:in`) -- e.g., `dataProvenance` must be one of `ClinicalGenerated`, `DeviceGenerated`, `SelfReported`, `AIGenerated`
- **Pattern constraints** (`sh:pattern`) -- e.g., `schemaVersion` must match `^[0-9]+\.[0-9]+$`
- **Datatype constraints** (`sh:datatype`) -- e.g., `isActive` must be `xsd:boolean`

Validate data against shapes using the [Cascade CLI](https://github.com/the-cascade-protocol/cli):

```bash
cascade validate record.ttl
```

## Namespace Prefixes

All Cascade Protocol data uses these canonical prefixes:

```turtle
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix health:  <https://ns.cascadeprotocol.org/health/v1#> .
@prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
@prefix coverage: <https://ns.cascadeprotocol.org/coverage/v1#> .
@prefix fhir:    <http://hl7.org/fhir/> .
@prefix sct:     <http://snomed.info/sct/> .
@prefix loinc:   <http://loinc.org/rdf#> .
@prefix rxnorm:  <http://www.nlm.nih.gov/research/umls/rxnorm/> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix prov:    <http://www.w3.org/ns/prov#> .
```

## Links

- [Full Documentation](https://cascadeprotocol.org/docs/)
- [Schema Reference](https://cascadeprotocol.org/docs/cascade-protocol-schemas/)
- [Conformance Test Suite](https://github.com/the-cascade-protocol/conformance)
- [CLI Tool](https://github.com/the-cascade-protocol/cli)

## License

This specification is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
