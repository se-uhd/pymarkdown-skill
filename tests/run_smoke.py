#!/usr/bin/env python3
"""run_smoke.py — pymarkdown-skill upstream smoke tests.

Exercises the canonical lint_markdown.py, check_baseline.py, and
refresh_vendor.py via subprocess (refresh_vendor.py only as far as its
--help; the full vendoring flow needs the network). Skill-specific
schema checks are covered in each consuming skill's own test suite.

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
    cmd = [sys.executable, str(LINT), "--config", str(DEFAULT_YAML),
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


def test_pre_pass_unclosed_tilde_fence():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "tilde.md"
        p.write_text("# Heading\n\n~~~python\nprint('hi')\n",
                     encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "unclosed-fence" in out, f"expected unclosed-fence; got:\n{out}"


def test_tilde_fence_containing_backticks_is_clean():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "nested.md"
        # A literal ``` line inside a closed tilde fence is content, not
        # an opener — the canonical reason tilde fences exist.
        p.write_text(
            "# Heading\n\n~~~markdown\n```python\nprint('hi')\n```\n~~~\n",
            encoding="utf-8",
        )
        rc, out, _ = run_lint(p)
        assert "unclosed-fence" not in out, f"false positive:\n{out}"
        assert rc == 0, f"expected 0, got {rc}:\n{out}"


def test_indented_fence_closer_is_clean():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "indent.md"
        # CommonMark allows fence lines to be indented up to 3 spaces.
        p.write_text("# Heading\n\n```text\ncode\n  ```\n",
                     encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert "unclosed-fence" not in out, f"false positive:\n{out}"
        assert rc == 0, f"expected 0, got {rc}:\n{out}"


def test_leading_thematic_break_is_not_frontmatter():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "thematic.md"
        # `---` followed by a blank line is a thematic break, which
        # pymarkdown parses without complaint; the pre-pass must not
        # flag it as abandoned frontmatter.
        p.write_text("---\n\nSome text.\n", encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert "unclosed-frontmatter" not in out, f"false positive:\n{out}"
        assert rc == 0, f"expected 0, got {rc}:\n{out}"


def test_frontmatter_abandoned_despite_later_dashes():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "abandoned.md"
        # pymarkdown abandons frontmatter at the first blank line, so the
        # `---` further down does not close it; the pre-pass must flag
        # this even though a later `---` exists.
        p.write_text("---\ntitle: hi\n\nbody text\n\n---\n",
                     encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "unclosed-frontmatter" in out, f"expected flag; got:\n{out}"


def test_non_markdown_extension_exits_2():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "notes.txt"
        p.write_text("# Heading\n", encoding="utf-8")
        rc, out, err = run_lint(p)
        assert rc == 2, f"expected 2, got {rc}\nstdout:{out}\nstderr:{err}"
        assert "did not scan" in err, f"expected explanation; got:\n{err}"


ALLOW_BLANKS_YAML = (
    "extensions:\n"
    "  front-matter:\n"
    "    enabled: true\n"
    "    allow_blank_lines: true\n"
    "  markdown-tables: {enabled: true}\n"
    "  markdown-task-list-items: {enabled: true}\n"
    "  markdown-strikethrough: {enabled: true}\n"
    "  markdown-extended-autolinks: {enabled: true}\n"
    "plugins:\n"
    "  md013: {enabled: false}\n"
    "  md033: {enabled: false}\n"
    "  md041: {enabled: false}\n"
)

FRONTMATTER_OFF_YAML = (
    "extensions:\n"
    "  front-matter: {enabled: false}\n"
    "plugins:\n"
    "  md013: {enabled: false}\n"
    "  md033: {enabled: false}\n"
    "  md041: {enabled: false}\n"
)


def test_allow_blank_lines_config_respected():
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "cfg.yaml"
        cfg.write_text(ALLOW_BLANKS_YAML, encoding="utf-8")
        p = Path(d) / "fm.md"
        # With allow_blank_lines pymarkdown accepts the blank inside the
        # frontmatter, so the pre-pass must not flag it. No `title:` key:
        # md025 would count it as the document's top-level heading.
        p.write_text("---\ngenre: a\n\nauthor: x\n---\n\n# Heading\n",
                     encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(LINT), "--config", str(cfg), str(p)],
            capture_output=True, text=True,
        )
        assert "unclosed-frontmatter" not in r.stdout, \
            f"false positive:\n{r.stdout}"
        assert r.returncode == 0, \
            f"expected 0, got {r.returncode}:\n{r.stdout}\n{r.stderr}"


def test_frontmatter_disabled_config_skips_check():
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "cfg.yaml"
        cfg.write_text(FRONTMATTER_OFF_YAML, encoding="utf-8")
        p = Path(d) / "doc.md"
        # With the extension disabled, pymarkdown parses the leading ---
        # as a thematic break; "abandoned frontmatter" is meaningless.
        p.write_text("---\ntitle: hi\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(LINT), "--config", str(cfg), str(p)],
            capture_output=True, text=True,
        )
        assert "unclosed-frontmatter" not in r.stdout, \
            f"false positive:\n{r.stdout}"
        assert r.returncode == 0, \
            f"expected 0, got {r.returncode}:\n{r.stdout}\n{r.stderr}"


def test_invalid_yaml_frontmatter_fences_tracked():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "invalid_fm.md"
        # The block is structurally closed but "```" is YAML-invalid as
        # frontmatter (a bare string), so pymarkdown re-parses the whole
        # block as body text — making line 2 a real fence opener that
        # never closes.
        p.write_text("---\n```\n---\ntext\n", encoding="utf-8")
        rc, out, _ = run_lint(p)
        assert rc == 1
        assert "unclosed-fence" in out, f"expected unclosed-fence:\n{out}"


def test_valid_frontmatter_with_fence_string_is_clean():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "fence_str.md"
        # No `title:` key: md025 would count it as the top-level heading.
        p.write_text(
            '---\nname: hi\nexample: "```"\n---\n\n# Heading\n',
            encoding="utf-8",
        )
        rc, out, _ = run_lint(p)
        assert "unclosed-fence" not in out, f"false positive:\n{out}"
        assert rc == 0, f"expected 0, got {rc}:\n{out}"


def test_prepass_findings_survive_pymarkdown_crash():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "no_newline.md"
        # pymarkdown 0.9.37 crashes on a leading --- without a final
        # newline; the wrapper must exit 2 but still print the pre-pass
        # diagnosis instead of swallowing it.
        p.write_bytes(b"---\ntitle: hi")
        rc, out, err = run_lint(p)
        assert rc == 2, f"expected 2, got {rc}\nstdout:{out}\nstderr:{err}"
        assert "unclosed-frontmatter" in out, \
            f"pre-pass finding suppressed:\n{out}\n{err}"


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
            [sys.executable, str(staging / "lint_markdown.py"),
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
        [sys.executable, str(CHECK_BASELINE), str(DEFAULT_YAML)],
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
            [sys.executable, str(CHECK_BASELINE), str(bad)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1, r.stderr
        assert "md033" in r.stderr


def test_check_baseline_rejects_string_enabled():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "stringy.yaml"
        # PyMarkdown requires a boolean; the string "true" leaves the
        # extension disabled, so the baseline check must flag it.
        bad.write_text(
            'extensions:\n'
            '  front-matter: {enabled: "true"}\n'
            '  markdown-tables: {enabled: true}\n'
            '  markdown-task-list-items: {enabled: true}\n'
            '  markdown-strikethrough: {enabled: true}\n'
            '  markdown-extended-autolinks: {enabled: true}\n'
            'plugins:\n'
            '  md013: {enabled: false}\n'
            '  md033: {enabled: false}\n'
            '  md041: {enabled: false}\n',
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(CHECK_BASELINE), str(bad)],
            capture_output=True, text=True,
        )
        assert r.returncode == 1, r.stderr
        assert "front-matter" in r.stderr
        assert "boolean" in r.stderr


def test_check_baseline_wrong_shape_exits_2():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "shape.yaml"
        bad.write_text("extensions:\n  - front-matter\n  - markdown-tables\n",
                       encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(CHECK_BASELINE), str(bad)],
            capture_output=True, text=True,
        )
        assert r.returncode == 2, f"expected 2, got {r.returncode}\n{r.stderr}"
        assert "mapping" in r.stderr


def test_check_baseline_falsy_shape_exits_2():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "falsy.yaml"
        # An empty list is falsy; it must hit the same shape error as a
        # non-empty one, not be coerced to an empty mapping.
        bad.write_text("extensions: []\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(CHECK_BASELINE), str(bad)],
            capture_output=True, text=True,
        )
        assert r.returncode == 2, f"expected 2, got {r.returncode}\n{r.stderr}"
        assert "mapping" in r.stderr


def test_check_baseline_help():
    r = subprocess.run(
        [sys.executable, str(CHECK_BASELINE), "--help"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "lint_markdown.yaml" in r.stdout


def test_check_baseline_missing_pyyaml_exits_2():
    # The import guard must turn a missing PyYAML into exit 2 with a
    # message, not an ImportError traceback (exit 1). Copy the script
    # where no _vendor/ sibling exists and run it with -S so the host's
    # site-packages PyYAML (if any) is not importable either — the only
    # deterministic way to exercise the guard on an arbitrary host.
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "check_baseline.py"
        script.write_bytes(CHECK_BASELINE.read_bytes())
        target = Path(d) / "x.yaml"
        target.write_text("extensions: {}\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-S", str(script), str(target)],
            capture_output=True, text=True,
        )
        assert r.returncode == 2, \
            f"expected 2, got {r.returncode}\nstderr:{r.stderr}"
        assert "PyYAML not importable" in r.stderr, r.stderr
        assert "Traceback" not in r.stderr, r.stderr


# --- refresh_vendor ---

def test_refresh_vendor_help():
    r = subprocess.run(
        [sys.executable, str(SRC / "refresh_vendor.py"), "--help"],
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
            [sys.executable, str(LINT), "--config", str(bad), str(p)],
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
        ("test_pre_pass_unclosed_tilde_fence",
         test_pre_pass_unclosed_tilde_fence),
        ("test_tilde_fence_containing_backticks_is_clean",
         test_tilde_fence_containing_backticks_is_clean),
        ("test_indented_fence_closer_is_clean",
         test_indented_fence_closer_is_clean),
        ("test_leading_thematic_break_is_not_frontmatter",
         test_leading_thematic_break_is_not_frontmatter),
        ("test_frontmatter_abandoned_despite_later_dashes",
         test_frontmatter_abandoned_despite_later_dashes),
        ("test_non_markdown_extension_exits_2",
         test_non_markdown_extension_exits_2),
        ("test_allow_blank_lines_config_respected",
         test_allow_blank_lines_config_respected),
        ("test_frontmatter_disabled_config_skips_check",
         test_frontmatter_disabled_config_skips_check),
        ("test_invalid_yaml_frontmatter_fences_tracked",
         test_invalid_yaml_frontmatter_fences_tracked),
        ("test_valid_frontmatter_with_fence_string_is_clean",
         test_valid_frontmatter_with_fence_string_is_clean),
        ("test_prepass_findings_survive_pymarkdown_crash",
         test_prepass_findings_survive_pymarkdown_crash),
        ("test_schema_checks_loaded_when_present",
         test_schema_checks_loaded_when_present),
        ("test_runs_without_schema_checks", test_runs_without_schema_checks),
        ("test_check_baseline_default_yaml_passes",
         test_check_baseline_default_yaml_passes),
        ("test_check_baseline_flags_missing_disable",
         test_check_baseline_flags_missing_disable),
        ("test_check_baseline_rejects_string_enabled",
         test_check_baseline_rejects_string_enabled),
        ("test_check_baseline_wrong_shape_exits_2",
         test_check_baseline_wrong_shape_exits_2),
        ("test_check_baseline_falsy_shape_exits_2",
         test_check_baseline_falsy_shape_exits_2),
        ("test_check_baseline_help", test_check_baseline_help),
        ("test_check_baseline_missing_pyyaml_exits_2",
         test_check_baseline_missing_pyyaml_exits_2),
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
