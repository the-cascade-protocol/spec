#!/usr/bin/env node
// check-contexts.mjs
//
// Every published JSON-LD context must be ACCEPTED by the reference JSON-LD
// processor (jsonld.js) when applied to a document.
//
// Why a real processor and not a structural check written here: three of the
// seven files under contexts/v1/ carried prose-valued keys for months --
//
//     "__comment_core": "=== Core Vocabulary (cascade:) ==="
//
// -- written as section dividers. A term definition's value must be an IRI, a
// compact IRI or a keyword; prose is none of those, and the processor refuses
// the ENTIRE document ("invalid IRI mapping"), not the one term. Every in-house
// consumer of these files was hand-rolled and read straight past the keys, so
// nothing noticed that no conformant consumer could apply cascade.jsonld,
// core.jsonld or health.jsonld at all. Found by an external contributor
// (jayostis/spec#48, 2026-09-03). An approximation of the processor's rules,
// maintained here, could disagree with it in either direction; the processor
// is the oracle.
//
// Usage:  node scripts/check-contexts.mjs
//         CONTEXTS_DIR=<dir> node scripts/check-contexts.mjs   (for the tests)
// Exit:   0  every context accepted
//         1  at least one context refused or unreadable
//         2  the check itself could not run (jsonld not installed, no files
//            found). Never a silent skip: a check that cannot run must not
//            report green.

import { createRequire } from 'node:module';
import { readdirSync, readFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(here, 'package.json'));

let jsonld;
try {
  jsonld = require('jsonld');
} catch {
  console.error('ERROR: jsonld is not installed under scripts/. Run: npm ci --prefix scripts');
  process.exit(2);
}
const processorVersion = require('jsonld/package.json').version;

const dir = resolve(process.env.CONTEXTS_DIR ?? join(here, '..', 'contexts', 'v1'));
let files;
try {
  files = readdirSync(dir).filter((f) => f.endsWith('.jsonld')).sort();
} catch (e) {
  console.error(`ERROR: cannot read ${dir}: ${e.message}`);
  process.exit(2);
}
if (files.length === 0) {
  console.error(`ERROR: no .jsonld files under ${dir}; nothing was checked`);
  process.exit(2);
}

// Nothing under contexts/v1/ imports a remote context, and a check that reaches
// the network is not deterministic. Refuse rather than fetch.
const documentLoader = async (url) => {
  throw new Error(`remote context fetch refused: ${url}`);
};

console.log(`Checking ${files.length} context(s) under ${dir} with jsonld.js ${processorVersion}\n`);

let failed = 0;
for (const f of files) {
  const path = join(dir, f);

  let doc;
  try {
    doc = JSON.parse(readFileSync(path, 'utf8'));
  } catch (e) {
    console.log(`  FAIL: ${f}: not JSON (${e.message})`);
    failed++;
    continue;
  }
  const ctx = doc['@context'];
  if (ctx === undefined) {
    console.log(`  FAIL: ${f}: no @context member`);
    failed++;
    continue;
  }

  // The oracle: expand a minimal document under this context.
  const probe = { '@context': ctx, '@id': 'urn:cascade:probe', '@type': 'urn:cascade:probe:Type' };
  try {
    await jsonld.expand(probe, { documentLoader });
    const termCount = ctx && typeof ctx === 'object' && !Array.isArray(ctx) ? Object.keys(ctx).length : '?';
    console.log(`  ok: ${f} (${termCount} terms)`);
  } catch (e) {
    const code = e?.details?.code ?? e?.code ?? e?.name ?? 'error';
    const term = e?.details?.term;
    // Name the term the processor stopped at when it tells us; otherwise point
    // at the likeliest culprits (string-valued terms containing whitespace,
    // which can never be an IRI) so the failure is actionable without a
    // debugger.
    let where = term !== undefined ? ` at term ${JSON.stringify(term)}` : '';
    if (!where && ctx && typeof ctx === 'object' && !Array.isArray(ctx)) {
      const prose = Object.entries(ctx)
        .filter(([k, v]) => !k.startsWith('@') && typeof v === 'string' && /\s/.test(v))
        .map(([k]) => k);
      if (prose.length) where = ` (prose-valued term(s): ${prose.join(', ')})`;
    }
    console.log(`  FAIL: ${f}: refused by the processor (${code})${where}`);
    failed++;
  }
}

console.log('');
if (failed) {
  console.log(`FAILED: ${failed} context(s) refused. A conformant consumer cannot apply a refused context at all.`);
  process.exit(1);
}
console.log('All contexts accepted.');
