#!/usr/bin/env bash
# sync_to_skill.sh --target <skill-scripts-dir>
#
# Propagate the canonical pymarkdown-skill files into a target skill's
# scripts/ directory. Refuses to run if the target has no schema_checks.py
# (the marker that this is a skill). The sync set is hardcoded below;
# .syncignore lists the files each skill owns, and the script refuses to
# run if the two sets ever overlap (it does not consult .syncignore
# during the copy itself).
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

Stamps the target with .pymarkdown-skill-version, containing
"<version> <HEAD SHA>"; the SHA gets a -dirty suffix when the upstream
working tree has uncommitted changes.
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
    # A .syncignore entry nested under a synced directory cannot be
    # preserved: the whole directory is removed and re-copied below.
    while IFS= read -r line; do
        [[ -z "$line" || "$line" == \#* ]] && continue
        for d in "${sync_dirs[@]}"; do
            if [[ "$line" == "$d/"?* ]]; then
                echo "sync_to_skill.sh: inconsistency:" >&2
                echo "  '$line' in .syncignore is nested under synced" \
                     "directory '$d/' and would be destroyed" >&2
                exit 2
            fi
        done
    done < "$syncignore"
fi

for d in "${sync_dirs[@]}"; do
    if [[ -d "$target/$d" ]]; then rm -rf "$target/$d"; fi
done

for f in "${sync_files[@]}"; do
    cp "$src/$f" "$target/$f"
done
for d in "${sync_dirs[@]}"; do
    cp -R "$src/$d" "$target/$d"
    # cp -R also copies any bytecode caches the upstream working tree
    # accumulated from local runs; consuming skills must get the same
    # pycache-free tree refresh_vendor.py produces.
    find "$target/$d" -name '__pycache__' -type d -prune -exec rm -rf {} +
    find "$target/$d" -name '*.py[co]' -type f -delete
done

version="$(cat "$upstream/VERSION" 2>/dev/null || echo unknown)"
sha="$(git -C "$upstream" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$sha" != unknown && -n "$(git -C "$upstream" status --porcelain 2>/dev/null)" ]]; then
    sha="${sha}-dirty"
    echo "sync_to_skill.sh: warning: upstream working tree has" \
         "uncommitted changes; stamping ${sha:0:12}…-dirty" >&2
fi
printf '%s %s\n' "$version" "$sha" > "$target/.pymarkdown-skill-version"

echo "synced pymarkdown-skill ${version}@${sha:0:12} into $target" >&2
