#!/usr/bin/env python3
"""run_smoke.py — pymarkdown-skill upstream smoke tests.

Exercises the canonical lint_markdown.py and refresh_vendor.py end-to-end
via subprocess. Skill-specific schema checks are covered in each consuming
skill's own test suite.

Exit codes
----------
  0  all tests passed.
  1  one or more tests failed.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
LINT = SRC / "lint_markdown.py"
CHECK_BASELINE = SRC / "check_baseline.py"
DEFAULT_YAML = SRC / "lint_markdown.default.yaml"


def run_lint(md_path, extra=()):
    """Invoke lint_markdown.py via subprocess; return (rc, stdout, stderr)."""
    cmd = ["python3", str(LINT), "--config", str(DEFAULT_YAML),
           *extra, str(md_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


PASS = 0
FAIL = 0


def case(name, fn):
    global PASS, FAIL
    try:
        fn()
    except AssertionError as e:
        FAIL += 1
        print(f"FAIL  {name}: {e}")
    except Exception as e:
        FAIL += 1
        print(f"ERROR {name}: {e!r}")
    else:
        PASS += 1
        print(f"PASS  {name}")


# --- lint core ---

def test_vendored_tree_loads():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.md"
        p.write_text("# Hi\n", encoding="utf-8")
        rc, _, err = run_lint(p)
        assert rc == 0, f"expected 0, got {rc}\n{err}"


def test_clean_file_passes():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "clean.md"
        p.write_text("# Heading\n\nA paragraph.\n", encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 0
        assert out == "", f"unexpected findings:\n{out}"


def test_pymarkdown_rule_fires():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "trailing.md"
        # md009 = no trailing spaces
        p.write_text("# Heading\n\nA line with trailing space.   \n",
                     encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "md009" in out, f"expected md009; got:\n{out}"


def test_fix_mode_normalizes():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "fixable.md"
        p.write_text("# Heading\n\nLine with trailing space.   \n",
                     encoding="utf-8")
        rc, _, _ = run_lint(p, extra=("--fix",))
        # After fix the file is clean.
        assert rc == 0
        assert "   \n" not in p.read_text(encoding="utf-8")


# --- pre-pass ---

def test_pre_pass_crlf():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "crlf.md"
        p.write_bytes(b"# Heading\r\n\r\nA paragraph.\r\n")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "crlf-line-endings" in out


def test_pre_pass_unclosed_fence():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "fence.md"
        p.write_text("# Heading\n\n```python\nprint('hi')\n",
                     encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "unclosed-fence" in out


def test_pre_pass_unclosed_frontmatter():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "fm.md"
        p.write_text("---\ntitle: hi\n\n# Heading\n", encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "unclosed-frontmatter" in out


# --- schema_checks integration ---

def test_schema_checks_loaded_when_present():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        # Stage a sibling lint_markdown.py + schema_checks.py + _vendor link
        # so the lint script picks up the schema module.
        staging = d / "scripts"
        staging.mkdir()
        (staging / "schema_checks.py").write_text(
            'SKILL_NAME = "fixture"\n'
            'def schema_findings(text, path):\n'
            '    return [(1, "fixture-rule", "fixture finding")]\n',
            encoding="utf-8",
        )
        (staging / "lint_markdown.py").write_bytes(LINT.read_bytes())
        (staging / "lint_markdown.default.yaml").write_bytes(
            DEFAULT_YAML.read_bytes())
        (staging / "_vendor").symlink_to(SRC / "_vendor")
        target = d / "x.md"
        target.write_text("# Heading\n", encoding="utf-8")
        r = subprocess.run(
            ["python3", str(staging / "lint_markdown.py"),
             "--config", str(staging / "lint_markdown.default.yaml"),
             str(target)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1
        assert "fixture-rule" in r.stdout
        assert "fixture finding" in r.stdout


def test_runs_without_schema_checks():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.md"
        p.write_text("# Heading\n", encoding="utf-8")
        rc, _, _ = run_lint(p)
        # Upstream src/ has no schema_checks.py; lint should still run.
        assert rc == 0


# --- check_baseline ---

def test_check_baseline_default_yaml_passes():
    r = subprocess.run(
        ["python3", str(CHECK_BASELINE), str(DEFAULT_YAML)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


def test_check_baseline_flags_missing_disable():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "bad.yaml"
        bad.write_text(
            "extensions:\n"
            "  front-matter: {enabled: true}\n"
            "  markdown-tables: {enabled: true}\n"
            "  markdown-task-list-items: {enabled: true}\n"
            "  markdown-strikethrough: {enabled: true}\n"
            "  markdown-extended-autolinks: {enabled: true}\n"
            "plugins:\n"
            "  md013: {enabled: false}\n"
            # md033 missing
            "  md041: {enabled: false}\n",
            encoding="utf-8",
        )
        r = subprocess.run(
            ["python3", str(CHECK_BASELINE), str(bad)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1, r.stderr
        assert "md033" in r.stderr


# --- refresh_vendor ---

def test_refresh_vendor_help():
    r = subprocess.run(
        ["python3", str(SRC / "refresh_vendor.py"), "--help"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    assert "Refresh the vendored" in r.stdout


def test_missing_config_yields_clear_error():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.md"
        p.write_text("# Heading\n", encoding="utf-8")
        bad = Path(d) / "does-not-exist.yaml"
        r = subprocess.run(
            ["python3", str(LINT), "--config", str(bad), str(p)],
            capture_output=True, text=True,
        )
        assert r.returncode == 2, f"expected 2, got {r.returncode}\n{r.stderr}"
        assert "not found" in r.stderr


if __name__ == "__main__":
    tests = [
        ("test_vendored_tree_loads", test_vendored_tree_loads),
        ("test_clean_file_passes", test_clean_file_passes),
        ("test_pymarkdown_rule_fires", test_pymarkdown_rule_fires),
        ("test_fix_mode_normalizes", test_fix_mode_normalizes),
        ("test_pre_pass_crlf", test_pre_pass_crlf),
        ("test_pre_pass_unclosed_fence", test_pre_pass_unclosed_fence),
        ("test_pre_pass_unclosed_frontmatter",
         test_pre_pass_unclosed_frontmatter),
        ("test_schema_checks_loaded_when_present",
         test_schema_checks_loaded_when_present),
        ("test_runs_without_schema_checks", test_runs_without_schema_checks),
        ("test_check_baseline_default_yaml_passes",
         test_check_baseline_default_yaml_passes),
        ("test_check_baseline_flags_missing_disable",
         test_check_baseline_flags_missing_disable),
        ("test_refresh_vendor_help", test_refresh_vendor_help),
        ("test_missing_config_yields_clear_error",
         test_missing_config_yields_clear_error),
    ]
    for name, fn in tests:
        case(name, fn)
    print()
    if FAIL:
        print(f"{FAIL} test(s) failed, {PASS} passed.")
        sys.exit(1)
    print(f"All {PASS} tests passed.")
