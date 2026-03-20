## Vocabulary Change Summary

**Vocabulary:** <!-- e.g., clinical -->
**Version bump:** <!-- e.g., v1.7 → v1.8 -->
**Type of change:** <!-- minor (new class/property) / patch (clarification) / major (breaking) -->

### What changed

<!-- Brief description of new classes, properties, or named individuals -->

---

## Pre-merge Checklist

### In this PR (`spec`)
- [ ] `owl:versionInfo` bumped in modified TTL file(s)
- [ ] `dct:modified` updated to today
- [ ] Changelog comment added to top of TTL file
- [ ] Corresponding `.shapes.ttl` updated for new classes/properties
- [ ] JSON-LD context updated (`contexts/v1/{name}.jsonld`) if new terms added
- [ ] `VOCAB_VERSIONS` updated for this vocabulary
- [ ] Commit tag planned: `vocab/{name}-v{X.Y}`

### Downstream (complete after merge, in order)
- [ ] `cascadeprotocol.org`: run `sync-from-spec.sh`, update HTML docs + schemas.md
- [ ] `conformance`: fixtures added for new classes/properties; release tagged
- [ ] `cascade-cli`: shapes synced, `VOCAB_VERSIONS` updated
- [ ] `sdk-typescript`: models added, `VOCAB_VERSIONS` updated
- [ ] `sdk-python`: models added, `VOCAB_VERSIONS` updated
- [ ] `cascade-agent`: system prompt updated, `VOCAB_VERSIONS` updated
