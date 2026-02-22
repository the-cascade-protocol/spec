# Contributing to Cascade Protocol Specification

Thank you for your interest in contributing to the Cascade Protocol specification. This document describes how to propose changes to vocabularies, add SHACL shapes, and follow our development process.

## Types of Contributions

### Vocabulary Changes (RFC Process)

Changes to ontology files (adding classes, properties, or modifying existing terms) follow a lightweight RFC process:

1. **Open an issue** describing the proposed change, including:
   - Which vocabulary is affected (core, health, clinical, coverage, etc.)
   - New classes or properties being added
   - Rationale and use case
   - Mapping to established standards (FHIR, SNOMED CT, LOINC) if applicable

2. **Discussion period**: Allow at least 7 days for community feedback.

3. **Submit a PR** implementing the change once consensus is reached. The PR must update all affected artifacts (see checklist below).

4. **Review**: At least one maintainer must approve vocabulary changes.

### Adding SHACL Shapes

When adding validation shapes for new or existing classes:

1. Place shapes in the appropriate `ontologies/<vocab>/v1/<vocab>.shapes.ttl` file
2. Each shape must define:
   - `sh:targetClass` pointing to the ontology class
   - Required field constraints (`sh:minCount 1`)
   - Datatype constraints (`sh:datatype`)
   - Enumeration constraints (`sh:in`) where applicable
3. Add corresponding conformance test fixtures in the [conformance](https://github.com/the-cascade-protocol/conformance) repository

### Documentation Fixes

Typos, clarifications, and improved examples are always welcome. Open a PR directly -- no RFC needed.

## Vocabulary Change Checklist

When modifying any Cascade Protocol vocabulary, update ALL of the following artifacts:

- [ ] **TTL ontology file** (source of truth) -- bump `owl:versionInfo`, update `dct:modified`, add changelog comment
- [ ] **SHACL shapes file** -- add/update shapes for new classes or properties
- [ ] **HTML documentation page** (e.g., `docs/clinical/v1/index.html`) -- update version refs, add class/property sections, add changelog entry
- [ ] **`cascade-protocol-schemas.md`** -- update section heading version, class count, version history
- [ ] **`docs/index.html`** -- update vocabulary card version badge
- [ ] **Conformance fixtures** -- add test fixtures for new classes/properties in the [conformance repo](https://github.com/the-cascade-protocol/conformance)

## Commit Message Conventions

We use structured commit messages to maintain a clear changelog:

```
docs(schema): <vocab>: <description>

Examples:
  docs(schema): clinical: add ImmunizationRecord class
  docs(schema): core: bump version to 1.4, add PharmacyInfo
  docs(schema): coverage: fix InsurancePlan sh:pattern constraint
  fix(shapes): clinical: correct MedicationShape required fields
```

Format: `<type>(scope): <vocab>: <description>`

Types:
- `docs(schema)` -- vocabulary or documentation changes
- `fix(shapes)` -- SHACL shape corrections
- `feat(vocab)` -- new vocabulary terms
- `chore` -- maintenance, tooling

## Design Principles

When proposing new vocabulary terms, follow these principles:

1. **Three-layer mapping**: Every data type should map through established standards (FHIR, SNOMED CT, LOINC) at Layer 1, domain vocabulary at Layer 2, and patient-facing vocabulary at Layer 3.

2. **Provenance-first**: All data must carry provenance metadata (`cascade:dataProvenance`). New classes must support the standard provenance values.

3. **Local-first**: Vocabulary design must not require network access for validation or processing.

4. **Minimal but complete**: Add only what is needed. Each property should have a clear use case in at least one consuming application.

## Development Setup

To work with the ontology files locally:

```bash
# Clone the repo
git clone https://github.com/the-cascade-protocol/spec.git
cd spec

# Validate shapes with the CLI
npm install -g @cascade-protocol/cli
cascade validate ontologies/clinical/v1/clinical.shapes.ttl
```

## Questions?

Open a [discussion](https://github.com/the-cascade-protocol/spec/discussions) for questions about the specification, vocabulary design, or mapping to external standards.
