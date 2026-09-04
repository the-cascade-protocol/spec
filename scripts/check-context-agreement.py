#!/usr/bin/env python3
"""check-context-agreement.py: every published per-vocabulary JSON-LD context
must agree with the ontology and the shapes it claims to describe.

THE RULE

The ontologies and shapes are the source of truth for the JSON to RDF mapping.
A context is a published artefact that MUST agree with them: a context that
disagrees is the defect, never the ontology. That is D-CONTEXT-1 C1, and this
check is what makes it a gate rather than a sentence.

Three questions are asked of every term in the six per-vocabulary contexts under
contexts/v1/ (core, health, clinical, coverage, checkup, pots):

  1. DECLARED. The term's @id, expanded through the context's own prefixes, is a
     property, class or individual actually declared in that vocabulary's
     ontology, or it lives in an allow-listed external namespace. A term whose
     @id names nothing is a dictionary entry pointing at an IRI no vocabulary
     defines, and a consumer that writes it produces a graph nothing can read.
     A term drawn from ANOTHER Cascade vocabulary is legal but is reported
     (foreign-vocabulary-term), because a context is per-vocabulary and every
     borrowed term is a place two files must be kept in step.

  2. TYPE AGREES WITH RANGE. A datatype property with rdfs:range xsd:T needs
     "@type": "xsd:T" on its term; a bare term publishes a plain string where
     the vocabulary promised a typed literal, so a date round-trips as text
     (#46 found bare performedDate, onsetDate, reportedDate, administrationDate
     in health and procedureDate, encounterStart, encounterEnd in clinical). An
     object property whose range class has named individuals is an enumeration
     and needs "@type": "@vocab": with "@type": "@id" a bare token such as
     "ClinicalGenerated" resolves against the DOCUMENT BASE and produces a
     different IRI for every consumer (#47). An object property whose range is a
     structured class with its own shape needs a term that names the class and
     scopes its children (D-CONTEXT-1 C4); at the time this check was written no
     context has made the 1.1 move, so structured-term-unscoped fires on every
     such term and is baselined.

  3. CONTAINER AGREES WITH CARDINALITY. A path a shape constrains to
     sh:maxCount 1 must not be published with "@container": "@set" or "@list".
     The context would invite a consumer to write an array the shapes reject.

WHAT THIS CHECK IS NOT: it is not a JSON-LD processor. scripts/check-contexts.mjs
already answers "is this file a context at all" with the reference processor as
its oracle. This check answers a question the processor cannot: does the
dictionary say what the vocabulary says. Neither can see the other's defect.

SHAPES ARE LOADED IN A SEPARATE GRAPH FROM THE ONTOLOGY, ALWAYS. Merging them is
the mistake validation/index.md exists to forbid: SHACL resolves class membership
over the data graph, so a check that reasons over ontology+shapes as one graph
sees entailments no validator will see and reports agreement that does not hold
for a consumer. Ranges are read from the ontology graph, cardinality from the
shapes graph, and the two are never in the same Graph object.

cascade.jsonld IS REPORT-ONLY. It merges seven one-meaning dictionaries and must
therefore pick one meaning per colliding key and drop the rest; that is a
property of merging, not a defect a per-vocabulary rule can fix, and
D-CONTEXT-1 C3 retires it as a mapping. Its collisions, and the terms whose
@container does not survive the merge, are printed on every run and never fail
the gate.

THE BASELINE

scripts/known-context-disagreements.json enumerates the disagreements that exist
at the time the check landed. It is a GATE INPUT, not a filter: every term is
still examined and every finding is still printed. The run fails when

  * a finding appears that the baseline does not list, and
  * a baselined finding no longer occurs (reported STALE),

so the file can only shrink, and shrinking it is an explicit committed edit.

Usage:  python3 scripts/check-context-agreement.py [spec-root]
        CONTEXTS_DIR=<dir>              override the contexts directory
        CONTEXT_AGREEMENT_BASELINE=<f>  override the baseline file
Exit:   0  every term agrees or is baselined
        1  at least one new finding, or a stale baseline entry
        2  the check could not run (rdflib missing, no contexts, no ontologies).
           Never a silent skip: a check that cannot run must not report green.
Requires: rdflib (see scripts/requirements.txt)
"""

import json
import os
import sys

try:
    from rdflib import Graph, RDF, RDFS, OWL, URIRef, Namespace
except ImportError:  # pragma: no cover - environment guard
    sys.stderr.write(
        "ERROR: rdflib is not installed. This check parses Turtle and cannot\n"
        "       degrade to a text scan without becoming unsound.\n"
        "       Install it with:  python3 -m pip install -r scripts/requirements.txt\n"
    )
    sys.exit(2)

SH = Namespace("http://www.w3.org/ns/shacl#")
XSD = "http://www.w3.org/2001/XMLSchema#"
CASCADE_NS_PREFIX = "https://ns.cascadeprotocol.org/"

VOCABS = ("core", "health", "clinical", "coverage", "checkup", "pots")
AGGREGATE = "cascade"
BASELINE = "scripts/known-context-disagreements.json"

# Namespaces a term may be drawn from without being a Cascade vocabulary term.
# Enumerated from what the published contexts actually declare; a term in any
# other namespace is reported rather than assumed benign.
EXTERNAL_NAMESPACES = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://www.w3.org/ns/shacl#": "sh",
    "http://www.w3.org/ns/prov#": "prov",
    "http://purl.org/dc/terms/": "dct",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://schema.org/": "schema",
    "https://schema.org/": "schema",
    "http://xmlns.com/foaf/0.1/": "foaf",
    "http://www.w3.org/2004/02/skos/core#": "skos",
    "http://hl7.org/fhir/": "fhir",
    "http://hl7.org/fhir/sid/icd-10-cm/": "icd10",
    "http://snomed.info/sct/": "sct",
    "http://loinc.org/rdf#": "loinc",
    "http://www.nlm.nih.gov/research/umls/rxnorm/": "rxnorm",
    "http://unitsofmeasure.org/": "ucum",
    "http://terminology.hl7.org/CodeSystem/": "hl7cs",
}

PROPERTY_TYPES = (
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    RDF.Property,
    OWL.FunctionalProperty,
)
CLASS_TYPES = (OWL.Class, RDFS.Class)

CONTAINERS = ("@set", "@list")

# Finding classes. Each is a distinct disagreement with a distinct cure.
CLASS_UNDECLARED = "undeclared-term"
CLASS_FOREIGN = "foreign-vocabulary-term"
CLASS_UNKNOWN_NS = "unknown-namespace"
CLASS_MISSING_DATATYPE = "missing-datatype"
CLASS_DATATYPE_MISMATCH = "datatype-mismatch"
CLASS_ENUM_NOT_VOCAB = "enumeration-not-vocab"
CLASS_STRUCTURED = "structured-term-unscoped"
CLASS_CONTAINER = "container-vs-cardinality"

FINDING_CLASSES = (
    CLASS_UNDECLARED,
    CLASS_FOREIGN,
    CLASS_UNKNOWN_NS,
    CLASS_MISSING_DATATYPE,
    CLASS_DATATYPE_MISMATCH,
    CLASS_ENUM_NOT_VOCAB,
    CLASS_STRUCTURED,
    CLASS_CONTAINER,
)


def die(message):
    sys.stderr.write("ERROR: %s\n" % message)
    sys.exit(2)


def qname(iri):
    """Render a Cascade term as prefix:Local, xsd as xsd:Local, else the IRI."""
    text = str(iri)
    if text.startswith(CASCADE_NS_PREFIX):
        rest = text[len(CASCADE_NS_PREFIX):]
        vocab, _, local = rest.partition("#")
        vocab = vocab.split("/")[0]
        prefix = "cascade" if vocab == "core" else vocab
        return "%s:%s" % (prefix, local)
    for ns, prefix in EXTERNAL_NAMESPACES.items():
        if text.startswith(ns):
            return "%s:%s" % (prefix, text[len(ns):])
    return "<%s>" % text


def vocab_of(iri):
    """The Cascade vocabulary an IRI belongs to, or None."""
    text = str(iri)
    if not text.startswith(CASCADE_NS_PREFIX):
        return None
    rest = text[len(CASCADE_NS_PREFIX):]
    return rest.partition("#")[0].split("/")[0] or None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

class VocabGraphs(object):
    """One vocabulary's ontology and shapes, in two graphs that never merge.

    Ranges and declarations are read from `onto`; cardinality from `shapes`.
    Keeping them apart is the rule in validation/index.md: a merged graph
    entails class memberships and property axioms that no SHACL validator sees
    over pod data, so a check reading the merged graph would report agreement a
    consumer does not get.
    """

    def __init__(self, name, onto, shapes):
        self.name = name
        self.onto = onto
        self.shapes = shapes


def load_vocabularies(root):
    graphs = {}
    for vocab in VOCABS:
        onto_path = os.path.join(root, "ontologies", vocab, "v1", "%s.ttl" % vocab)
        shapes_path = os.path.join(root, "ontologies", vocab, "v1", "%s.shapes.ttl" % vocab)
        if not os.path.exists(onto_path):
            die("ontology %s not found; nothing to check the contexts against" % onto_path)
        onto = Graph()
        onto.parse(onto_path, format="turtle")
        shapes = Graph()
        if os.path.exists(shapes_path):
            shapes.parse(shapes_path, format="turtle")
        graphs[vocab] = VocabGraphs(vocab, onto, shapes)
    return graphs


def load_contexts(contexts_dir):
    contexts = {}
    if not os.path.isdir(contexts_dir):
        die("cannot read contexts directory %s" % contexts_dir)
    present = sorted(f for f in os.listdir(contexts_dir) if f.endswith(".jsonld"))
    if not present:
        die("no .jsonld files under %s; nothing was checked" % contexts_dir)
    for name in list(VOCABS) + [AGGREGATE]:
        path = os.path.join(contexts_dir, "%s.jsonld" % name)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        ctx = doc.get("@context")
        if not isinstance(ctx, dict):
            die("%s has no object-valued @context; run check-contexts.mjs first" % path)
        contexts[name] = ctx
    missing = [v for v in VOCABS if v not in contexts]
    if len(missing) == len(VOCABS):
        die("none of the six per-vocabulary contexts were found under %s" % contexts_dir)
    return contexts, missing


# ---------------------------------------------------------------------------
# Context reading
# ---------------------------------------------------------------------------

def prefix_map(ctx):
    """Prefix declarations: a string value that is an IRI ending in a delimiter."""
    out = {}
    for key, value in ctx.items():
        if key.startswith("@") or not isinstance(value, str):
            continue
        if "://" in value and (value.endswith("#") or value.endswith("/") or value.endswith(":")):
            out[key] = value
    return out


def expand(value, prefixes):
    """Expand a compact IRI through the context's own prefixes. None if it cannot."""
    if not isinstance(value, str) or value.startswith("@"):
        return None
    if "://" in value:
        return value
    prefix, sep, local = value.partition(":")
    if not sep:
        return None
    base = prefixes.get(prefix)
    if base is None:
        return None
    return base + local


def terms_of(ctx):
    """Yield (key, definition dict) for every real term, prefixes excluded."""
    prefixes = prefix_map(ctx)
    for key, value in ctx.items():
        if key.startswith("@") or key in prefixes:
            continue
        definition = {"@id": value} if isinstance(value, str) else dict(value)
        if not isinstance(definition.get("@id"), str):
            continue
        yield key, definition


# ---------------------------------------------------------------------------
# Ontology facts
# ---------------------------------------------------------------------------

def declared_kind(graphs, iri):
    """'property', 'class', 'individual' or None, read from the owning vocabulary."""
    vocab = vocab_of(iri)
    if vocab is None or vocab not in graphs:
        return None
    onto = graphs[vocab].onto
    node = URIRef(iri)
    types = set(onto.objects(node, RDF.type))
    if types & set(PROPERTY_TYPES):
        return "property"
    if types & set(CLASS_TYPES):
        return "class"
    if OWL.NamedIndividual in types:
        return "individual"
    if types:
        return "individual"
    return None


def property_facts(graphs, iri):
    """(is_object_property, is_datatype_property, [ranges]) from the ontology graph."""
    vocab = vocab_of(iri)
    if vocab is None or vocab not in graphs:
        return False, False, []
    onto = graphs[vocab].onto
    node = URIRef(iri)
    types = set(onto.objects(node, RDF.type))
    ranges = [str(r) for r in onto.objects(node, RDFS.range)]
    return OWL.ObjectProperty in types, (
        OWL.DatatypeProperty in types or OWL.AnnotationProperty in types
    ), ranges


def enumeration_members(graphs, class_iri):
    """The named values of a range class, across every vocabulary.

    A value is named either as an owl:NamedIndividual typed with the class, or
    as a named subclass of it. Both forms occur here: core v3.1 PROMOTED the
    cascade:DataProvenance values from individuals to subclasses, and the JSON
    written against them did not change ("dataProvenance": "ClinicalGenerated").
    The mapping question is identical in both forms -- the value is a bare token
    naming a term of the vocabulary, which is what "@type": "@vocab" resolves
    and what "@type": "@id" resolves against the document base instead.
    """
    individuals = []
    subclasses = []
    node = URIRef(class_iri)
    for vocab in graphs.values():
        for member in vocab.onto.subjects(RDF.type, node):
            if (member, RDF.type, OWL.NamedIndividual) in vocab.onto:
                individuals.append(str(member))
        for member in vocab.onto.subjects(RDFS.subClassOf, node):
            if isinstance(member, URIRef):
                subclasses.append(str(member))
    if individuals:
        return sorted(set(individuals)), "named individual"
    return sorted(set(subclasses)), "named subclass"


def shaped_classes(graphs):
    """Every class any shapes file targets, with the shape that targets it."""
    out = {}
    for vocab in graphs.values():
        for shape, target in vocab.shapes.subject_objects(SH.targetClass):
            out.setdefault(str(target), qname(shape))
    return out


def max_count_one_shapes(graphs):
    """path IRI -> (shapes declaring sh:maxCount 1, shapes leaving it open)."""
    single = {}
    open_ended = {}
    for vocab in graphs.values():
        shapes = vocab.shapes
        for prop_shape, path in shapes.subject_objects(SH.path):
            if not isinstance(path, URIRef):
                continue
            counts = [int(c) for c in shapes.objects(prop_shape, SH.maxCount)]
            owner = owning_shape(shapes, prop_shape)
            bucket = single if 1 in counts else open_ended
            bucket.setdefault(str(path), set()).add(owner)
    return single, open_ended


def owning_shape(shapes, prop_shape):
    """Name the IRI shape a (usually blank-node) property shape hangs off."""
    if isinstance(prop_shape, URIRef):
        return qname(prop_shape)
    seen = set()
    stack = [prop_shape]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for owner in shapes.subjects(SH.property, node):
            if isinstance(owner, URIRef):
                return qname(owner)
            stack.append(owner)
    return "(anonymous shape)"


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------

def check_context(name, ctx, graphs, shaped, single_paths, open_paths):
    """Yield findings for one per-vocabulary context."""
    prefixes = prefix_map(ctx)
    findings = []
    examined = 0

    def note(term, cls, detail):
        findings.append(
            {
                "key": "%s.jsonld:%s:%s" % (name, term, cls),
                "file": "%s.jsonld" % name,
                "term": term,
                "class": cls,
                "detail": detail,
            }
        )

    for term, definition in terms_of(ctx):
        raw_id = definition["@id"]
        if raw_id.startswith("@"):
            continue  # a keyword alias ("type": "@type"); nothing to agree with
        examined += 1
        iri = expand(raw_id, prefixes)
        if iri is None:
            note(term, CLASS_UNKNOWN_NS,
                 'context says @id "%s", which no prefix in this context expands' % raw_id)
            continue

        term_vocab = vocab_of(iri)
        declared = declared_kind(graphs, iri)

        # --- 1. Declared -----------------------------------------------------
        if term_vocab is None:
            if not any(iri.startswith(ns) for ns in EXTERNAL_NAMESPACES):
                note(term, CLASS_UNKNOWN_NS,
                     "context says %s, which is in no Cascade vocabulary and no "
                     "allow-listed external namespace" % qname(iri))
            continue  # external terms have no local ontology to disagree with
        if term_vocab not in graphs:
            note(term, CLASS_UNKNOWN_NS,
                 "context says %s, a Cascade namespace with no ontology in this repo"
                 % qname(iri))
            continue
        if term_vocab != name:
            note(term, CLASS_FOREIGN,
                 "context for %s maps this key to %s, declared by the %s vocabulary"
                 % (name, qname(iri), term_vocab))
        if declared is None:
            note(term, CLASS_UNDECLARED,
                 "context says %s; ontologies/%s/v1/%s.ttl declares no such property, "
                 "class or individual" % (qname(iri), term_vocab, term_vocab))
            continue
        if declared != "property":
            continue  # a class or individual key carries no range or cardinality

        ctx_type = definition.get("@type")
        ctx_container = definition.get("@container")

        # --- 2. Type agrees with range ---------------------------------------
        is_object, is_datatype, ranges = property_facts(graphs, iri)
        xsd_ranges = [r for r in ranges if r.startswith(XSD)]
        class_ranges = [r for r in ranges if vocab_of(r) is not None]

        if is_datatype and xsd_ranges:
            expected = xsd_ranges[0]
            if ctx_type is None:
                note(term, CLASS_MISSING_DATATYPE,
                     "ontology says rdfs:range %s; context declares no @type, so a "
                     "consumer writes an untyped string" % qname(expected))
            elif expand(ctx_type, prefixes) != expected and ctx_type != "@vocab":
                note(term, CLASS_DATATYPE_MISMATCH,
                     'ontology says rdfs:range %s; context says "@type": "%s"'
                     % (qname(expected), ctx_type))
        elif is_object and class_ranges:
            range_class = class_ranges[0]
            members, member_kind = enumeration_members(graphs, range_class)
            structured = range_class in shaped and member_kind != "named individual"
            if members and not structured:
                if ctx_type != "@vocab":
                    note(term, CLASS_ENUM_NOT_VOCAB,
                         "ontology says rdfs:range %s, an enumeration with %d %s(s) "
                         "(%s); context says %s, so a bare token resolves against "
                         "the document base"
                         % (qname(range_class), len(members), member_kind,
                            ", ".join(qname(m) for m in members[:3]),
                            ('"@type": "%s"' % ctx_type) if ctx_type else "no @type"))
            elif range_class in shaped:  # structured: a class with its own shape
                expanded_type = expand(ctx_type, prefixes) if ctx_type else None
                if expanded_type != range_class or not isinstance(
                    definition.get("@context"), dict
                ):
                    note(term, CLASS_STRUCTURED,
                         "ontology says rdfs:range %s, a structured class shaped by %s; "
                         "context says %s and no scoped @context, so the nested node's "
                         "class and children are stated nowhere"
                         % (qname(range_class), shaped[range_class],
                            ('"@type": "%s"' % ctx_type) if ctx_type else "no @type"))

        # --- 3. Container agrees with cardinality -----------------------------
        if ctx_container in CONTAINERS and iri in single_paths:
            owners = sorted(single_paths[iri])
            others = sorted(open_paths.get(iri, set()))
            detail = ("shapes constrain this path to sh:maxCount 1 (%s); context says "
                      '"@container": "%s"' % (", ".join(owners), ctx_container))
            if others:
                detail += " (%d other shape(s) leave it repeatable: %s)" % (
                    len(others), ", ".join(others))
            note(term, CLASS_CONTAINER, detail)

    return examined, findings


# ---------------------------------------------------------------------------
# cascade.jsonld: reported, never failed
# ---------------------------------------------------------------------------

def report_aggregate(contexts):
    merged = contexts.get(AGGREGATE)
    print("cascade.jsonld (report-only; D-CONTEXT-1 C3 retires it as a mapping)")
    if merged is None:
        print("  not present under this contexts directory")
        print()
        return
    merged_prefixes = prefix_map(merged)
    merged_terms = dict(terms_of(merged))

    meanings = {}
    containers = {}
    for name in VOCABS:
        ctx = contexts.get(name)
        if ctx is None:
            continue
        prefixes = prefix_map(ctx)
        for term, definition in terms_of(ctx):
            iri = expand(definition["@id"], prefixes)
            if iri is None:
                continue
            meanings.setdefault(term, {})[name] = iri
            if definition.get("@container"):
                containers.setdefault(term, {})[name] = definition["@container"]

    collisions = sorted(t for t, m in meanings.items() if len(set(m.values())) > 1)
    lost = []
    absent = []
    for term, declared in sorted(containers.items()):
        entry = merged_terms.get(term)
        shapes = sorted(set(declared.values()))
        if entry is None:
            absent.append((term, shapes))
        elif not entry.get("@container"):
            lost.append((term, shapes))

    print("  keys whose meaning collides across the six vocabularies: %d" % len(collisions))
    for term in collisions:
        seen = meanings[term]
        print("    %-28s %s" % (term, "; ".join(
            "%s -> %s" % (v, qname(i)) for v, i in sorted(seen.items()))))
    print("  terms whose @container does not survive the merge: %d" % (len(lost) + len(absent)))
    for term, declared in lost:
        print("    %-28s per-vocabulary files declare %s; merged entry has none"
              % (term, ", ".join(declared)))
    for term, declared in absent:
        print("    %-28s per-vocabulary files declare %s; no merged entry at all"
              % (term, ", ".join(declared)))
    print("  A merged dictionary must pick one meaning per key; this is a property of")
    print("  merging, not a defect a per-vocabulary rule can fix. Never fails the gate.")
    print()


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

def load_baseline(path):
    if not os.path.exists(path):
        die("baseline %s not found. It is a required input: without it this check\n"
            "       cannot tell a pre-existing disagreement from a new one." % path)
    with open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    entries = doc.get("entries")
    if not isinstance(entries, dict):
        die("baseline %s has no object-valued \"entries\"" % path)
    return entries


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."
    )
    root = os.path.abspath(root)
    contexts_dir = os.path.abspath(
        os.environ.get("CONTEXTS_DIR") or os.path.join(root, "contexts", "v1")
    )
    baseline_path = os.path.abspath(
        os.environ.get("CONTEXT_AGREEMENT_BASELINE") or os.path.join(root, BASELINE)
    )

    graphs = load_vocabularies(root)
    contexts, missing = load_contexts(contexts_dir)
    baseline = load_baseline(baseline_path)

    shaped = shaped_classes(graphs)
    single_paths, open_paths = max_count_one_shapes(graphs)

    print("Context agreement check (context versus ontology versus shapes)")
    print("  root:              %s" % root)
    print("  contexts:          %s" % contexts_dir)
    print("  baseline:          %s" % baseline_path)
    print("  vocabularies:      %d ontologies, %d shapes files loaded separately"
          % (len(graphs), sum(1 for g in graphs.values() if len(g.shapes))))
    print()

    all_findings = []
    total_examined = 0
    for name in VOCABS:
        ctx = contexts.get(name)
        if ctx is None:
            print("  %-10s NOT PRESENT under %s" % (name, contexts_dir))
            continue
        examined, findings = check_context(
            name, ctx, graphs, shaped, single_paths, open_paths
        )
        total_examined += examined
        all_findings.extend(findings)
        counts = {}
        for item in findings:
            counts[item["class"]] = counts.get(item["class"], 0) + 1
        summary = ", ".join("%s %d" % (c, counts[c]) for c in FINDING_CLASSES if c in counts)
        print("  %-10s %4d terms examined, %3d finding(s)%s"
              % (name, examined, len(findings), (": " + summary) if summary else ""))
    print()

    if total_examined == 0:
        print("EMPTY: no context term was examined. A check with no material to")
        print("inspect has proven nothing.")
        return 2

    report_aggregate(contexts)

    all_findings.sort(key=lambda item: item["key"])
    new = [item for item in all_findings if item["key"] not in baseline]
    found_keys = {item["key"] for item in all_findings}
    stale = sorted(set(baseline) - found_keys)

    by_class = {}
    for item in all_findings:
        by_class[item["class"]] = by_class.get(item["class"], 0) + 1
    print("Findings by class (every finding, baselined or not)")
    for cls in FINDING_CLASSES:
        if cls in by_class:
            print("  %-26s %4d" % (cls, by_class[cls]))
    print("  %-26s %4d" % ("TOTAL", len(all_findings)))
    print("  %-26s %4d" % ("baselined", len(baseline)))
    print()

    if new:
        print("FAIL  %d finding(s) not in the baseline:" % len(new))
        for item in new:
            print("        %s  [%s]" % (item["key"], item["class"]))
            print("          %s: %s" % (item["term"], item["detail"]))
        print()
        print("      The ontologies and shapes are normative (D-CONTEXT-1 C1): fix the")
        print("      context, not the vocabulary. Adding an entry to the baseline is a")
        print("      committed admission that a published dictionary misdescribes the")
        print("      graph a consumer will write.")
        print()

    if stale:
        print("FAIL  %d baselined finding(s) no longer occur:" % len(stale))
        for key in stale:
            print("        %s" % key)
        print()
        print("      Good news that must be recorded: remove the entry from")
        print("      %s so the baseline keeps" % BASELINE)
        print("      matching reality and cannot silently re-absorb the disagreement.")
        print()

    if missing:
        print("FAIL  per-vocabulary context(s) missing entirely: %s" % ", ".join(missing))
        print()

    if new or stale or missing:
        print("RESULT: FAIL")
        return 1

    print("RESULT: PASS, %d term(s) examined across %d context(s), %d baselined "
          "disagreement(s) unchanged."
          % (total_examined, len([v for v in VOCABS if v in contexts]), len(baseline)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
