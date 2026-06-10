# Changelog

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
  `true` (PyMarkdown ignores truthy non-booleans); wrong-shaped yaml
  (non-mapping document or sections) exits 2 with a message instead of
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
