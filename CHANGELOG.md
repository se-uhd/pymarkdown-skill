# Changelog

## 0.2.7 — 2026-09-27

- `src/check_baseline.py`: the exit-code docstring says "the wrong
  structure" and a comment says "the mapping check" where both said
  "shape", which the consuming ai-slop-skill repo now lists as a word
  to replace. `tests/run_smoke.py` names the two tests of that exit code
  after the mapping check. The 0.2.0 and 0.2.1 entries below say
  "non-mapping" where they said "shape". No behavior change.

## 0.2.6 — 2026-09-15

- `src/refresh_vendor.py` and `src/_vendor/pyjson5/__init__.py`: the
  pyjson5 shim docstring restated without a semicolon that joins
  clauses and without "bake into". The `PYJSON5_SHIM` constant and the
  vendored shim changed together and stay byte-identical. These are the
  two findings from the same prose review that 0.2.5 left out, because
  the text is a string constant rather than a comment. No behavior
  change.

## 0.2.5 — 2026-09-15

- `src/lint_markdown.py`, `src/check_baseline.py`, and
  `src/refresh_vendor.py`: docstrings and comments restated without
  semicolons that join clauses, colons before a complete sentence, or
  *whose* clauses on things, as flagged by a prose review of the
  consuming ai-slop-skill repo. The `refresh_vendor.py` module docstring
  now gives its steps as a numbered list in the order the code runs
  them. No behavior change.

## 0.2.4 — 2026-09-01

- `src/refresh_vendor.py`: two comments restated without literal em-dash
  glyphs; no behavior change. (Same sweep as 0.2.3, which had covered
  only `lint_markdown.py`.)

## 0.2.3 — 2026-09-01

- `src/lint_markdown.py`: docstrings and comments restated without
  literal em-dash glyphs and without "surface" as a verb; no behavior
  change. (Applied in the consuming ai-slop-skill repo and synced back.)
- `.github/workflows/smoke.yml`: bump `actions/checkout` to v5 and
  `actions/setup-python` to v6 (off Node.js 20), and pin Python to
  the latest stable (3.14), matching the consuming skills' CI.

## 0.2.2 — 2026-06-10

- `src/lint_markdown.py`: the config is read in binary so PyYAML's BOM
  detection applies — a UTF-16 config, which pymarkdown itself accepts,
  no longer crashes the wrapper with an uncaught UnicodeDecodeError.
  The `unclosed-frontmatter` message under `allow_blank_lines: true` no
  longer claims pymarkdown "silently" demotes the block; in that mode
  pymarkdown 0.9.37 errors out on any unclosed block (the wrapper exits
  2 and still prints the finding).
- `sync/sync_to_skill.sh`: an upstream repository with an unborn HEAD
  (`git init`, no commits) stamps `unknown` instead of dying mid-sync
  under `set -e` after the target was already overwritten; the
  toplevel comparison uses `-ef` (device and inode) instead of string
  equality, so a case-variant path on a case-insensitive filesystem no
  longer stamps `unknown` spuriously.
- `tests/run_smoke.py`: UTF-16 config regression test (30 total).

## 0.2.1 — 2026-06-10

- `src/lint_markdown.py` pre-pass: frontmatter handling now follows the
  config handed to pymarkdown — no `unclosed-frontmatter` when the
  front-matter extension is not enabled, and `allow_blank_lines: true`
  is respected. Structurally closed blocks are YAML-validated the same
  way pymarkdown validates them, so fences inside a block pymarkdown
  demotes to body text are tracked again. When pymarkdown itself fails
  on a file (e.g. the 0.9.37 crash on a leading `---` without a final
  newline), the wrapper still prints its pre-pass and schema findings
  before exiting 2.
- `src/check_baseline.py`: falsy non-mappings (`extensions: []`,
  a `false` document) now exit 2 like their truthy counterparts.
- `sync/sync_to_skill.sh`: verifies every sync source exists before
  deleting anything in the target; the version stamp trusts git
  metadata only when the upstream tree is the repository toplevel, so
  a git-less copy nested in another repository stamps `unknown` instead
  of that repository's HEAD; the nested-`.syncignore` guard no longer
  misses a final line lacking a trailing newline.
- `tests/run_smoke.py`: six new tests (28 total), plus a test for the
  0.2.0 PyYAML import guard in `check_baseline.py` (29 total) — run via
  `python -S` against a copy with no `_vendor/` sibling, so the import
  failure is deterministic on hosts with PyYAML installed.

## 0.2.0 — 2026-06-10

- `src/lint_markdown.py`: invoke PyMarkdown with the `explicit`
  return-code scheme and check the codes it actually produces. The
  previous checks were written against the default scheme, so under the
  requested `minimal` scheme a PyMarkdown system error was reported as
  "clean" (exit 0) and a file PyMarkdown declined to scan (e.g. a
  non-`.md` extension) passed silently; both now exit 2 with a message.
- `src/lint_markdown.py` pre-pass: the fence tracker now understands
  tilde fences and the 1–3 spaces of indentation CommonMark allows, and
  no longer treats a backtick run with backticks in its info string as
  an opener. `unclosed-frontmatter` now mirrors PyMarkdown's actual
  rule — frontmatter is abandoned at the first blank line — instead of
  accepting any later `---` as a closer; a bare leading thematic break
  is no longer flagged.
- `src/check_baseline.py`: extensions must be enabled with a boolean
  `true` (PyMarkdown ignores truthy non-booleans); yaml with a
  non-mapping document or section exits 2 with a message instead of
  an uncaught traceback; `--help` works; a missing PyYAML exits 2.
- `src/refresh_vendor.py`: the `_vendor/` swap uses two renames so the
  old tree is never deleted before the new one is in place, and an
  unexpected failure cleans up `_vendor.new/`; venv-creation and
  site-packages failures exit 2 per the docstring; METADATA is parsed
  as RFC 822 with `License-Expression` preferred over the deprecated
  `License` field; NOTICE matching compares module names (not file
  names) against `top_level.txt`; the compiled-artifact guard also
  rejects `.dll`.
- `sync/sync_to_skill.sh`: strips `__pycache__`/bytecode after copying
  so local caches never reach consuming skills; the version stamp is
  now "<version> <HEAD SHA>" with a `-dirty` suffix (and warning) when
  the upstream tree has uncommitted changes; `.syncignore` entries
  nested under a synced directory are rejected as inconsistent.
- `.gitignore`: cover `src/_vendor.new/` and `src/_vendor.old/`.
- `tests/run_smoke.py`: subprocesses use `sys.executable` instead of a
  literal `python3`; nine new tests cover the fixed behaviors (22
  total).
- Docs: README/LICENSE no longer claim Apache-2.0 code is bundled;
  README describes the sync-set/`.syncignore` mechanism and the new
  version stamp accurately.

## 0.1.0 — 2026-05-15

Initial release.

- `src/lint_markdown.py`: canonical linter. Loads sibling
  `schema_checks.py` via `importlib`; runs with no schema checks if
  absent. Takes `--config <yaml>` (defaults to `lint_markdown.yaml`
  next to the script).
- `src/refresh_vendor.py`: rebuilds `_vendor/` and `_vendor/NOTICE`
  from the upstream wheels. Includes `LICENSE_LABEL_OVERRIDES`
  (sly → BSD-3-Clause; Columnar → MIT), a `bundled_licenses/`
  fallback for wheels that ship no LICENSE file, and an Apache 2.0
  NOTICE pass-through. Aborts before overwriting `_vendor/` if any
  package yields no license text.
- `src/check_baseline.py`: asserts a skill's `lint_markdown.yaml`
  carries the five required extensions and the three baseline
  plugin disables (md013, md033, md041).
- `src/_vendor/`: PyMarkdown 0.9.37 + deps, vendored pure-Python.
- `src/bundled_licenses/Columnar.txt`: MIT text for Columnar 1.4.1,
  whose wheel ships no LICENSE in its dist-info.
- `sync/sync_to_skill.sh`: one-way sync from `src/` into a target
  skill's `scripts/`. Preserves `schema_checks.py`,
  `lint_markdown.yaml`, and `tests/`.
- `tests/run_smoke.py`: 13 subprocess tests covering the lint core,
  pre-pass rules, fix mode, `schema_checks.py` loading,
  `check_baseline.py`, `refresh_vendor.py` invocation, and the
  missing-config error path.
