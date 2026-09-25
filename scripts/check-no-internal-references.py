#!/usr/bin/env python3
"""check-no-internal-references.py -- this repository is public, and ships no
private tracker references.

Run from the spec repo root:
    python3 scripts/check-no-internal-references.py
    python3 scripts/check-no-internal-references.py /path/to/other/checkout

An explicit path argument scans that tree instead of this repository. This is
what test-check-no-internal-references.sh uses to run the check against
scratch fixtures without touching this repository's own history.

When the target is a git working tree, files are enumerated as tracked PLUS
untracked-but-not-`.gitignore`d (so a violation that has been written but not
yet `git add`ed is still caught before the commit that would ship it, while a
vendored, ignored directory like `scripts/node_modules` is correctly never
scanned). When the target is not a git working tree (a bare scratch fixture,
typically), every file is walked directly except the contents of any `.git`
directory.

WHY THIS EXISTS
----------------
`spec` is a PUBLIC repository (github.com/the-cascade-protocol/spec) that
downstream repos sync from, including `cascade-cli`, whose own
`tests/no-internal-references.test.ts` bans the same class of reference in its
own shipped source because its `dist/` reaches npm and a release cannot be
withdrawn after 72 hours. On 2026-09-25 that cli test went red after a routine
shapes sync because comments carrying private-tracker references -- item
numbers from the root ecosystem backlog, an app-internal source path, and a
private planning-repo path -- had been merged into `spec` TTL and Markdown.
Those comments were written upstream, in this repo, so the leak has to be
caught here: catching it only downstream, after every sync, means every
consuming repo re-discovers the same defect on every affected release.

This script is `spec`'s half of that same check: it scans every file in this
repository (see the walk note above) for the same categories of private
reference, plus two categories specific to a citation
grammar this repo's own decision documents use that cli's shipped source does
not need: a path into the private partner-facing planning repository, and a
path into the company-only local drafts folder. Neither of those two is a
thing cli's `dist/` would ever contain, but both are things a `spec` decision
document -- written by an agent working across the whole Cascade ecosystem --
can accidentally cite.

PATTERNS are assembled from fragments and never spelled out contiguously
anywhere in this file, docstring included, for the same reason
cascade-cli/tests/no-internal-references.test.ts does it: written out
literally, this file would match its own scan, and the tempting fix for that
-- excluding this file from the scan -- would create the one place in the
repository a real reference could hide instead. Categories banned:

  - a private root-ecosystem backlog item, named either with its noun
    ("backlog") or bare, as "N.N" or "N.NN[a-z]"
  - a path fragment naming an app-internal planning-docs folder
  - the Workbench app repository, named directly
  - a Workbench-internal backlog slug: all-caps words joined by hyphens,
    in square brackets
  - a path into the private partner-facing planning repository
  - a path into the company-only local drafts folder

Exit 0 if none are found. Exit 1 with one "file:line: pattern: text" line per
hit, so a failure is actionable without re-running the scan by hand.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

NUM = r"[0-9]+\.[0-9]+"

# Every fragment below is a single inert piece: no fragment, read alone, is
# itself a banned string, and none of them is written adjacent to the next
# one anywhere outside this dict's own values.
_ROOT = "root"
_BACKLOG = "back" + "log"
_DOCS = "docs"
_PLANNING_WORD = "plan" + "ning"
_WORKBENCH_REPO = "cascade" + "-" + "work" + "bench"
_DEV_ROOT_DOCS = "Dev" + "-root" + "-docs"

PATTERNS = {
    "root_backlog": rf"{_ROOT} {_BACKLOG} {NUM}",
    "bare_root_num": rf"\b{_ROOT} {NUM}[a-z]?\b",
    "docs_planning_path": rf"{_DOCS}/{_PLANNING_WORD}",
    "workbench_repo_name": re.escape(_WORKBENCH_REPO),
    "bracket_slug": r"\[[A-Z]{2,}(?:-[A-Z]{2,})+\]",
    "planning_repo_path": rf"\b{_PLANNING_WORD}/[A-Za-z0-9_.-]",
    "dev_root_docs_path": re.escape(_DEV_ROOT_DOCS),
}

COMBINED = re.compile("|".join(f"(?P<{name}>{pat})" for name, pat in PATTERNS.items()))


def all_files(root):
    if (root / ".git").is_dir():
        # Tracked + untracked-but-not-ignored, so an ignored/vendored
        # directory (scripts/node_modules, __pycache__) is never scanned, but
        # a real file that simply has not been `git add`ed yet still is.
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
        )
        if result.returncode == 0:
            return sorted(
                root / p for p in result.stdout.decode("utf-8").split("\0") if p
            )

    # Not a git working tree: walk it directly.
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    )


def scan(path):
    hits = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return hits  # binary or unreadable; nothing to scan as text
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in COMBINED.finditer(line):
            kind = m.lastgroup
            hits.append((path, lineno, kind, m.group().strip()))
    return hits


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO_ROOT
    min_files = 10 if root == REPO_ROOT else 1
    files = all_files(root)
    if len(files) < min_files:
        # A tree walk that turned up implausibly little is not a clean scan,
        # it is a broken one -- `git ls-files` run from the wrong directory,
        # or against a shallow/sparse checkout. An empty result must mean
        # "clean", never "did not look".
        print(
            f"ERROR: only {len(files)} file(s) found under {root}; "
            "refusing to report a scan that did not really happen.",
            file=sys.stderr,
        )
        return 2

    all_hits = []
    for path in files:
        all_hits.extend(scan(path))

    if all_hits:
        print(f"FAIL: {len(all_hits)} internal reference(s) found in scanned files:\n")
        for path, lineno, kind, text in all_hits:
            rel = path.relative_to(root)
            print(f"  {rel}:{lineno}: {kind}: {text}")
        print(
            "\nThis is a public repository. Rewrite each hit so the meaning "
            'survives without the private identifier ("tracked separately", '
            '"a follow-up is filed", or a link to a PUBLIC issue), never '
            "delete the surrounding sentence's substance."
        )
        return 1

    print(f"PASS: {len(files)} file(s) scanned, no internal references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
