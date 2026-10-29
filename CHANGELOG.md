# Changelog

## 0.3.0 - 2026-10-29

- Vendors PyMarkdown 0.9.40 (was 0.9.37) and the latest releases of its
  dependencies. 0.9.40 adds MD049, MD050, MD051, MD053, MD054, MD059,
  and MD060, all on by default. 0.9.41 is skipped because it reports
  md029 on some correctly numbered ordered lists.
- `lint_markdown.py` turns off md060 (table-column-style) unless the
  config enables it, so skills need no config change. No md060 style
  accepts spaced cells over a `|---|` delimiter row, the most common
  table layout, and the rule has no `--fix`.
- `refresh_vendor.py --requirements FILE` installs exact pins. Every
  refresh records the vendored packages in `src/vendor-requirements.txt`
  and builds wcwidth without its optional C extension.
- Dependabot proposes weekly updates for the vendored pins and the CI
  actions. CI runs on Python 3.15.
- The README, the tests, and the sync script no longer contain em-dash
  or ellipsis glyphs, and the `lint_markdown.py` docstring no longer
  cites one skill's report template.

## 0.2.7 - 2026-09-27

- `check_baseline.py` and the smoke tests say "structure" or "mapping"
  where they said "shape". No behavior change.

## 0.2.6 - 2026-09-15

- The pyjson5 shim docstring, in `refresh_vendor.py` and
  `_vendor/pyjson5/`, drops a clause-joining semicolon and "bake into".
  No behavior change.

## 0.2.5 - 2026-09-15

- Docstrings and comments in `lint_markdown.py`, `check_baseline.py`,
  and `refresh_vendor.py` drop clause-joining semicolons, colons before
  full sentences, and *whose* clauses on things. No behavior change.

## 0.2.4 - 2026-09-01

- Two comments in `refresh_vendor.py` drop literal em-dash glyphs. No
  behavior change.

## 0.2.3 - 2026-09-01

- Docstrings and comments in `lint_markdown.py` drop literal em-dash
  glyphs and "surface" as a verb. No behavior change.
- CI uses `actions/checkout` v5, `actions/setup-python` v6, and Python
  3.14.

## 0.2.2 - 2026-06-10

- `lint_markdown.py` accepts a UTF-16 config instead of crashing with a
  UnicodeDecodeError. Under `allow_blank_lines: true`, the
  `unclosed-frontmatter` message says that pymarkdown errors out, not
  that it silently demotes the block.
- `sync_to_skill.sh` stamps `unknown` for an upstream repository without
  commits instead of failing mid-sync, and no longer stamps `unknown`
  for a case-variant path on a case-insensitive filesystem.

## 0.2.1 - 2026-06-10

- The `lint_markdown.py` pre-pass follows the config. It reports no
  `unclosed-frontmatter` when the front-matter extension is off,
  respects `allow_blank_lines: true`, and tracks fences inside
  frontmatter that pymarkdown treats as body text. When pymarkdown fails
  on a file, the wrapper still prints its own findings before exiting 2.
- `check_baseline.py` exits 2 for falsy non-mappings such as
  `extensions: []`, as it does for other non-mappings.
- `sync_to_skill.sh` checks that every source exists before it deletes
  anything in the target. It stamps `unknown` instead of an unrelated
  repository's HEAD when the upstream tree is not a repository toplevel,
  and it reads a final `.syncignore` line without a trailing newline.

## 0.2.0 - 2026-06-10

- `lint_markdown.py` exits 2 on a PyMarkdown system error and on a file
  that PyMarkdown declines to scan, e.g., a non-`.md` extension. Both
  used to pass as clean.
- The pre-pass understands tilde fences and indented fences, and a
  backtick run with backticks in its info string no longer opens a
  fence. `unclosed-frontmatter` follows PyMarkdown, which abandons
  frontmatter at the first blank line, and a bare leading thematic break
  is no longer flagged.
- `check_baseline.py` requires extensions to be enabled with a boolean
  `true`. It exits 2 with a message on a non-mapping document or section
  and on a missing PyYAML, and it supports `--help`.
- `refresh_vendor.py` keeps the old `_vendor/` until the new one is in
  place and exits 2 on venv and site-packages failures. NOTICE prefers
  `License-Expression` over `License` and includes single-module
  packages such as typing_extensions. `.dll` files are rejected like
  other compiled artifacts.
- `sync_to_skill.sh` strips bytecode caches from the copy and rejects
  `.syncignore` entries nested under a synced directory. The version
  stamp is "<version> <HEAD SHA>", with a `-dirty` suffix and a warning
  when the upstream tree has uncommitted changes.
- The README describes the sync set and the version stamp, and neither
  the README nor LICENSE claims that Apache-2.0 code is bundled.

## 0.1.0 - 2026-05-15

Initial release.

- `lint_markdown.py`: the linter. It loads a sibling `schema_checks.py`
  if one exists and reads `--config <yaml>`, by default
  `lint_markdown.yaml` next to the script.
- `refresh_vendor.py`: rebuilds `_vendor/` and `_vendor/NOTICE` and
  aborts if a package has no license text. `bundled_licenses/` supplies
  the text for wheels that ship none, such as Columnar 1.4.1.
- `check_baseline.py`: checks that a skill's `lint_markdown.yaml`
  enables the five required extensions and disables md013, md033, and
  md041.
- `_vendor/`: PyMarkdown 0.9.37 and its dependencies, pure Python.
- `sync_to_skill.sh`: copies `src/` into a skill's `scripts/` and keeps
  `schema_checks.py`, `lint_markdown.yaml`, and `tests/`.
