#!/usr/bin/env bash
# sync_to_skill.sh --target <skill-scripts-dir>
#
# Propagate the canonical pymarkdown-skill files into a target skill's
# scripts/ directory. Refuses to run if the target has no schema_checks.py
# (the marker that this is a skill); refuses to overwrite anything listed
# in .syncignore.
set -euo pipefail

usage() {
    cat >&2 <<EOF
usage: sync_to_skill.sh --target <skill-scripts-dir>

Replaces in the target:
  lint_markdown.py
  refresh_vendor.py
  check_baseline.py
  _vendor/
  bundled_licenses/

Preserves in the target (listed in .syncignore):
  schema_checks.py
  lint_markdown.yaml
  tests/

Stamps the target with .pymarkdown-skill-version (the upstream HEAD SHA).
EOF
}

target=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) target="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) usage; exit 2 ;;
    esac
done

if [[ -z "$target" ]]; then
    usage
    exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
upstream="$(cd "$here/.." && pwd)"
src="$upstream/src"

if [[ ! -d "$target" ]]; then
    echo "sync_to_skill.sh: target does not exist: $target" >&2
    exit 2
fi
if [[ ! -f "$target/schema_checks.py" ]]; then
    echo "sync_to_skill.sh: $target has no schema_checks.py" >&2
    echo "(refusing to sync into a directory that is not a skill)" >&2
    exit 2
fi

# Hardcoded sync set. Each entry is a path under src/ that gets force-
# replaced in the target. Adding to this list requires updating .syncignore
# at the same time (the consistency check below enforces this).
sync_files=(lint_markdown.py refresh_vendor.py check_baseline.py)
sync_dirs=(_vendor bundled_licenses)

# Consistency check: nothing being synced may also be marked
# "preserved per skill" in .syncignore. This catches the bug where a new
# upstream file is added to the sync set without being removed from the
# preserve set (or vice versa).
syncignore="$here/.syncignore"
if [[ -f "$syncignore" ]]; then
    for entry in "${sync_files[@]}" "${sync_dirs[@]}"; do
        if grep -Fxq "$entry"  "$syncignore" 2>/dev/null \
        || grep -Fxq "$entry/" "$syncignore" 2>/dev/null; then
            echo "sync_to_skill.sh: inconsistency:" >&2
            echo "  '$entry' is in the sync set but also in .syncignore" >&2
            exit 2
        fi
    done
fi

for d in "${sync_dirs[@]}"; do
    if [[ -d "$target/$d" ]]; then rm -rf "$target/$d"; fi
done

for f in "${sync_files[@]}"; do
    cp "$src/$f" "$target/$f"
done
for d in "${sync_dirs[@]}"; do
    cp -R "$src/$d" "$target/$d"
done

sha="$(git -C "$upstream" rev-parse HEAD 2>/dev/null || echo unknown)"
printf '%s\n' "$sha" > "$target/.pymarkdown-skill-version"

echo "synced pymarkdown-skill@${sha:0:12} into $target" >&2
