# pymarkdown-skill

A vendored Python Markdown linter, packaged for sync into multiple
[Agent Skills](https://agentskills.io/home). Each consuming skill plugs
in its own schema checks; the linter core, the vendored PyMarkdown tree,
and the licensing scaffolding are maintained here in one place.

## What it gives a skill

- `lint_markdown.py` wraps [PyMarkdown](https://github.com/jackdewinter/pymarkdown),
  vendored pure-Python under `_vendor/` so users do not have to `pip install`
  anything.
- The pre-pass catches findings PyMarkdown silently accepts: CRLF line
  endings, unclosed fenced code blocks, unclosed YAML frontmatter.
- `--fix` mode runs PyMarkdown's auto-fix in place, then re-scans.
- `check_baseline.py` verifies that the skill's own `lint_markdown.yaml`
  still carries the baseline rules shipped here.
- `refresh_vendor.py` rebuilds `_vendor/` and `_vendor/NOTICE` from the
  upstream wheels. It honors `LICENSE_LABEL_OVERRIDES` for wheels that
  misdeclare their license and falls through to `bundled_licenses/`
  when a wheel ships no LICENSE file at all.

## How it ships

Skills do not depend on this repo at runtime. Instead, the canonical
files are copied into each skill's `scripts/` directory by `sync_to_skill.sh`:

```bash
sync/sync_to_skill.sh --target /path/to/skill/scripts/
```

The sync overwrites `lint_markdown.py`, `refresh_vendor.py`,
`check_baseline.py`, `_vendor/`, and `bundled_licenses/` — a hardcoded
list in the script. The files each skill owns — `schema_checks.py`,
`lint_markdown.yaml`, and `tests/` — are never part of that list;
`sync/.syncignore` records them, and the script refuses to run if the
two sets ever overlap or if a `.syncignore` entry is nested inside a
synced directory. The target directory must contain a
`schema_checks.py` for sync to run; that is the marker that says "this
is a skill".

A `.pymarkdown-skill-version` file (release version plus upstream HEAD
SHA, with a `-dirty` suffix when synced from an uncommitted tree) is
dropped at the target so drift against upstream is detectable.

## The customization seam

Each consuming skill provides one Python file next to the synced
linter: `scripts/schema_checks.py`. The linter loads it at startup via
`importlib`; if missing, the linter runs without skill-specific checks.

```python
# scripts/schema_checks.py — per-skill
SKILL_NAME = "ai-slop"   # shown in --help

def schema_findings(text, path):
    # return list of (line_no, rule_id, message) tuples
    ...
```

Contract:

- `SKILL_NAME` is a string. Used only for the `--help` description line.
  Optional; if absent, `--help` reads "Lint a Markdown file via the
  vendored PyMarkdown tree."
- `schema_findings(text, path)` takes the raw file body (a `str`, with
  CR/CRLF preserved) and a `pathlib.Path` for the file under lint, and
  returns a list of `(int, str, str)` tuples: line number (1-indexed),
  short rule id (kebab-case is the convention used by existing schemas),
  and a human-readable message. The linter merges these findings with
  its own pre-pass and PyMarkdown findings and sorts by line number.
- The `path` argument is unused by the current skill schemas but is
  passed so future schemas can read or cross-reference sibling files.

That is the entire extension surface. The synced `lint_markdown.py` is
never patched by a skill.

## Repository layout

```text
src/
  lint_markdown.py            canonical linter; loads schema_checks.py if present
  refresh_vendor.py           maintainer-only; rebuilds _vendor/ and NOTICE
  check_baseline.py           asserts a skill yaml carries the baseline
  lint_markdown.default.yaml  baseline PyMarkdown config (informational)
  _vendor/                    vendored PyMarkdown tree + NOTICE
  bundled_licenses/           LICENSE texts for wheels that ship none
sync/
  sync_to_skill.sh
  .syncignore
tests/
  run_smoke.py                subprocess tests for the canonical CLI
```

## Refreshing the vendored tree

Maintainer-only. End users never run this.

```bash
python3 src/refresh_vendor.py --version pymarkdownlnt==0.9.37
```

The script creates a clean venv, installs `pymarkdownlnt` with
`--no-binary :all:`, copies the resolved tree into `_vendor/`, replaces
`pyjson5/` with a stdlib shim (the CLI is always invoked with
`--no-json5`), strips `__pycache__`, asserts no compiled extensions
landed, and regenerates `_vendor/NOTICE` from each package's dist-info
plus the manual entries in `bundled_licenses/`. If any package yields
no license text, the script aborts before touching `_vendor/`.

## Testing

```bash
python3 tests/run_smoke.py
```

The suite is subprocess-based: it shells out to `lint_markdown.py`,
`check_baseline.py`, and `refresh_vendor.py` against temp-directory
fixtures. Skill-specific schema checks are covered in each consuming
skill's own test suite.

## License

First-party content is MIT-licensed. See [`LICENSE`](LICENSE).

Third-party software bundled under `src/_vendor/` is distributed
verbatim under its own licenses (currently MIT, BSD-3-Clause, and
PSF-2.0). [`src/_vendor/NOTICE`](src/_vendor/NOTICE) is the
authoritative per-package list, with attribution and full license
texts.
