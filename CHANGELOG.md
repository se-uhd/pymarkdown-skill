# Changelog

## Unreleased

Initial scaffold.

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
- `tests/run_smoke.py`: 12 subprocess tests covering the lint core,
  pre-pass rules, fix mode, `schema_checks.py` loading,
  `check_baseline.py`, and `refresh_vendor.py` invocation.
