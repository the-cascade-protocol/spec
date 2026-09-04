# D-BROWSER-1: The published SDK loads in a browser

**Status:** Ratified
**Date:** 2026-09-03
**Decided by:** Jed Reinitz
**Prompted by:** the derive-from-spec proposal (jayostis/sdk-typescript PR #89), whose parser
loading path is not bundleable for a browser, and whose dependency guard states in a comment
that whether the package "should run outside Node" is a question "nothing here asks." The
requirement existed (sdk-typescript#10: "write against web APIs from the start") but was
written nowhere a guard would see it, and was already violated upstream by a `node:crypto`
import on the package barrel. This document is where it is written down.

---

## The decision

**`@the-cascade-protocol/sdk` MUST load and run in a browser.** Concretely: importing the
package's public entry point in a page bundled by an ordinary bundler (esbuild, Vite, webpack)
for a browser target MUST succeed, and `serialize`, `deserialize`, `validate`, `toJsonLd` and
`fromJsonLd` MUST work there.

## Why

A Cascade pod is patient-carried data, and the places a patient or caregiver meets it are
overwhelmingly browsers: the protocol playground, a Tauri desktop app's renderer (Cascade
Workbench's UI is a WebView; a `node:crypto` import has already crashed its mount once), and
any patient-facing web application. An SDK that runs only under Node is a library for the CLI,
not a library for applications. The playground plan (the playground plan) and the demonstrability
argument for landing importers in this SDK both depend on this property.

## What it forbids and what it allows

- **Forbidden on any path reachable from the public entry point:** `node:` builtin imports
  with no browser equivalent (`node:module`, `node:fs`), `createRequire`, dynamic CommonJS
  `require()`, and vendored code that itself requires Node builtins (`require("buffer")`).
- **Allowed with care:** APIs that exist in both environments (`crypto.subtle`, `TextEncoder`,
  `fetch`). Where Node offers a convenience the browser lacks (`node:crypto`'s `createHash`),
  the shared API is used where one exists; where the browser API is async-only
  (`crypto.subtle`) and the SDK's API is synchronous, a small vendored pure-JS implementation
  with identical output is used instead, so identity stays synchronous, aligned with the cli
  and the desktop app.
- **Vendoring is allowed** and the current vendored parser is welcome, in its ESM build with
  static imports so a bundler can see it. The problem in PR #89 is the loading mechanism, not
  the decision to vendor.
- **Node-only functionality** (reading a pod directory from disk, for example) MAY exist behind
  a separate, clearly named entry point that the browser entry never imports.

## The gate

A statement without a check is a document, so: the SDK's CI MUST bundle the public entry
point for a browser target (e.g. `esbuild --bundle --platform=browser`) and fail if the bundle
fails, and SHOULD execute the bundled `serialize`/`deserialize` round-trip under a browser-like
runtime. Until that job exists, this decision is unenforced and every phase built without it is
at risk of the same premise mismatch. The upstream `node:crypto` import is the first thing that
gate will catch; it goes in the same change.

## Consequences

1. PR #89's `createRequire` + CommonJS loading path is replaced before the epic proceeds:
   vendor n3's ESM build, static imports, resolve the vendored `buffer` reference.
2. `src/utils/deterministic-uri.ts` drops `node:crypto` for a vendored synchronous pure-JS
   SHA-1 with byte-identical output, so identity stays synchronous, aligned with the cli and
   the desktop app. (Amended 2026-09-04: this originally said `crypto.subtle`, which is
   async-only and would have changed the identity API.)
3. The browser-bundle CI gate lands in upstream `sdk-typescript` and is a merge
   gate for the derive-from-spec epic.
4. Nothing here applies to `cascade-cli`, which is a Node program by design.
