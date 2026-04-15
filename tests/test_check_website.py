# -*- coding: utf-8 -*-
"""Tests for helper functions in lib/check_website.py.

check_website.py has extensive module-level side effects (docopt, dotenv,
database connections).  We use importlib to load only the function definitions
we want to test without executing the full module body.
"""

import importlib.util
import types
from pathlib import Path


def _load_check_website_functions():
    """Extract testable functions from check_website.py source code.

    This avoids executing module-level database operations, docopt calls, etc.
    We compile the source and extract only the function definitions.
    """
    source_path = Path(__file__).resolve().parent.parent / "lib" / "check_website.py"
    source = source_path.read_text(encoding="utf-8")

    # Create a minimal module with just the imports needed by the functions
    mod = types.ModuleType("check_website_functions")
    mod.__file__ = str(source_path)

    # Execute only the import statements and function definitions
    # by compiling and running a cleaned version of the source
    import difflib
    mod.difflib = difflib

    # Define the functions directly in the module namespace
    exec_globals = {"__builtins__": __builtins__, "difflib": difflib}
    for func_source in _extract_functions(source, ["escape_markdown_v2", "escape_markdown_v2_code", "diff_preview"]):
        exec(compile(func_source, str(source_path), "exec"), exec_globals)

    mod.escape_markdown_v2 = exec_globals["escape_markdown_v2"]
    mod.escape_markdown_v2_code = exec_globals["escape_markdown_v2_code"]
    mod.diff_preview = exec_globals["diff_preview"]
    return mod


def _extract_functions(source, func_names):
    """Extract function source code blocks from a Python source string."""
    import ast
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in func_names:
            results.append(ast.get_source_segment(source, node))
    return results


_cw = _load_check_website_functions()


# ---------------------------------------------------------------------------
# escape_markdown_v2
# ---------------------------------------------------------------------------

class TestEscapeMarkdownV2:
    def test_no_special_chars(self):
        assert _cw.escape_markdown_v2("hello world") == "hello world"

    def test_escapes_special_chars(self):
        assert _cw.escape_markdown_v2("hello_world") == "hello\\_world"
        assert _cw.escape_markdown_v2("*bold*") == "\\*bold\\*"
        assert _cw.escape_markdown_v2("[link](url)") == "\\[link\\]\\(url\\)"

    def test_escapes_all_special_chars(self):
        special = r"_*[]()~`>#+-=|{}.!"
        result = _cw.escape_markdown_v2(special)
        # Every char should be escaped
        for char in special:
            assert f"\\{char}" in result

    def test_mixed_content(self):
        result = _cw.escape_markdown_v2("Price: $10.99!")
        assert result == "Price: $10\\.99\\!"


# ---------------------------------------------------------------------------
# escape_markdown_v2_code
# ---------------------------------------------------------------------------

class TestEscapeMarkdownV2Code:
    def test_no_special_chars(self):
        assert _cw.escape_markdown_v2_code("hello world") == "hello world"

    def test_escapes_backtick(self):
        assert _cw.escape_markdown_v2_code("use `code`") == "use \\`code\\`"

    def test_escapes_backslash(self):
        assert _cw.escape_markdown_v2_code("path\\to\\file") == "path\\\\to\\\\file"

    def test_does_not_escape_other_chars(self):
        # Underscores and other special chars should NOT be escaped in code blocks
        assert _cw.escape_markdown_v2_code("hello_world") == "hello_world"
        assert _cw.escape_markdown_v2_code("*bold*") == "*bold*"


# ---------------------------------------------------------------------------
# diff_preview
# ---------------------------------------------------------------------------

class TestDiffPreview:
    def test_no_change(self):
        result = _cw.diff_preview("hello", "hello")
        assert result == ""

    def test_simple_change(self):
        result = _cw.diff_preview("old line", "new line")
        assert "+new line" in result

    def test_addition(self):
        result = _cw.diff_preview("line1\n", "line1\nline2\n")
        assert "+line2" in result

    def test_truncation(self):
        old = "old\n"
        new = "x" * 600 + "\n"
        result = _cw.diff_preview(old, new, max_len=100)
        assert len(result) <= 110  # 100 + "..." + stripping
        assert result.endswith("...")

    def test_multiline_diff(self):
        old = "a\nb\nc\n"
        new = "a\nB\nC\n"
        result = _cw.diff_preview(old, new)
        assert "+B" in result
        assert "+C" in result
