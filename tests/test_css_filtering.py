"""
Tests for CSS filtering functionality.

Tests the filter_css_for_format() function which processes
@html, @epub, and @both directives in CSS files.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from writers.common import filter_css_for_format


def test_filter_css_empty():
    """Test filtering empty CSS returns empty string."""
    assert filter_css_for_format('', 'html') == ''
    assert filter_css_for_format('', 'epub') == ''


def test_filter_css_no_directives():
    """Test CSS without directives is included in both formats (default @both)."""
    css = "body { margin: 0; }\np { text-indent: 1em; }"
    assert filter_css_for_format(css, 'html') == css
    assert filter_css_for_format(css, 'epub') == css


def test_filter_css_html_only():
    """Test @html directive filters correctly."""
    css = "/* @html */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'html') == "body { margin: 0; }"
    assert filter_css_for_format(css, 'epub') == ""


def test_filter_css_epub_only():
    """Test @epub directive filters correctly."""
    css = "/* @epub */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'html') == ""
    assert filter_css_for_format(css, 'epub') == "body { margin: 0; }"


def test_filter_css_explicit_both():
    """Test explicit @both directive."""
    css = "/* @both */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'html') == "body { margin: 0; }"
    assert filter_css_for_format(css, 'epub') == "body { margin: 0; }"


def test_filter_css_mixed_sections():
    """Test mixed sections with multiple directives."""
    css = """/* @both */
body { font-family: serif; }
/* @html */
body { max-width: 40em; }
/* @epub */
body { margin: 0 5%; }
/* @both */
p { text-indent: 1em; }"""

    html_result = filter_css_for_format(css, 'html')
    assert 'font-family: serif' in html_result
    assert 'max-width: 40em' in html_result
    assert 'margin: 0 5%' not in html_result
    assert 'text-indent: 1em' in html_result

    epub_result = filter_css_for_format(css, 'epub')
    assert 'font-family: serif' in epub_result
    assert 'max-width: 40em' not in epub_result
    assert 'margin: 0 5%' in epub_result
    assert 'text-indent: 1em' in epub_result


def test_filter_css_whitespace_variations():
    """Test directive matching with various whitespace."""
    # No spaces
    css1 = "/*@html*/\nbody { margin: 0; }"
    assert filter_css_for_format(css1, 'html') == "body { margin: 0; }"

    # Extra spaces
    css2 = "/*  @html  */\nbody { margin: 0; }"
    assert filter_css_for_format(css2, 'html') == "body { margin: 0; }"

    # Tabs
    css3 = "/*\t@html\t*/\nbody { margin: 0; }"
    assert filter_css_for_format(css3, 'html') == "body { margin: 0; }"


def test_filter_css_case_insensitive():
    """Test directives are case-insensitive."""
    css = "/* @HTML */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'html') == "body { margin: 0; }"

    css = "/* @Epub */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'epub') == "body { margin: 0; }"


def test_filter_css_malformed_directives():
    """Test malformed directives are treated as comments."""
    # Unknown format
    css = "/* @unknown */\nbody { margin: 0; }"
    # Should be treated as comment in current mode (default 'both')
    assert filter_css_for_format(css, 'html') == "/* @unknown */\nbody { margin: 0; }"

    # Extra text
    css = "/* @html extra */\nbody { margin: 0; }"
    assert filter_css_for_format(css, 'html') == "/* @html extra */\nbody { margin: 0; }"


def test_filter_css_empty_sections():
    """Test empty sections (directive followed immediately by another directive)."""
    css = """/* @html */
/* @epub */
body { margin: 0; }"""

    # HTML section is empty, EPUB section has content
    assert filter_css_for_format(css, 'html') == ""
    assert filter_css_for_format(css, 'epub') == "body { margin: 0; }"


def test_filter_css_multiple_consecutive_directives():
    """Test multiple consecutive directives of same type."""
    css = """/* @html */
/* @html */
body { margin: 0; }"""

    # Second directive is redundant but valid
    assert filter_css_for_format(css, 'html') == "body { margin: 0; }"


def test_filter_css_mode_switching():
    """Test switching between modes multiple times."""
    css = """/* @html */
.html-only { color: blue; }
/* @epub */
.epub-only { color: red; }
/* @html */
.html-again { color: green; }"""

    html_result = filter_css_for_format(css, 'html')
    assert '.html-only { color: blue; }' in html_result
    assert '.epub-only { color: red; }' not in html_result
    assert '.html-again { color: green; }' in html_result


def test_filter_css_complex_rules():
    """Test with complex CSS rules and comments."""
    css = """/* Regular CSS comment */
body {
  font-family: serif;
  line-height: 1.4;
}

/* @html */
/* HTML-specific styles */
body {
  max-width: 40em;
  margin: 2em auto;
}

.transcriber {
  background-color: #DDDDEE;  /* Color backgrounds work in HTML */
}

/* @epub */
/* EPUB-specific styles */
.transcriber {
  border: 1px solid #999;  /* More conservative for e-readers */
}"""

    html_result = filter_css_for_format(css, 'html')
    assert 'font-family: serif' in html_result
    assert 'max-width: 40em' in html_result
    assert 'background-color: #DDDDEE' in html_result
    assert 'border: 1px solid #999' not in html_result

    epub_result = filter_css_for_format(css, 'epub')
    assert 'font-family: serif' in epub_result
    assert 'max-width: 40em' not in epub_result
    assert 'background-color: #DDDDEE' not in epub_result
    assert 'border: 1px solid #999' in epub_result


def test_filter_css_preserves_blank_lines():
    """Test that blank lines are preserved."""
    css = """/* @both */
body { margin: 0; }

p { text-indent: 1em; }"""

    result = filter_css_for_format(css, 'html')
    assert '\n\n' in result  # Blank line preserved


def test_filter_css_unknown_format():
    """Test with unknown format type (edge case)."""
    css = """/* @both */
body { margin: 0; }
/* @html */
.html-only { color: blue; }"""

    # Unknown format should only include @both sections
    result = filter_css_for_format(css, 'pdf')
    assert 'body { margin: 0; }' in result
    assert '.html-only { color: blue; }' not in result


if __name__ == '__main__':
    # Run all tests
    import traceback

    tests = [
        test_filter_css_empty,
        test_filter_css_no_directives,
        test_filter_css_html_only,
        test_filter_css_epub_only,
        test_filter_css_explicit_both,
        test_filter_css_mixed_sections,
        test_filter_css_whitespace_variations,
        test_filter_css_case_insensitive,
        test_filter_css_malformed_directives,
        test_filter_css_empty_sections,
        test_filter_css_multiple_consecutive_directives,
        test_filter_css_mode_switching,
        test_filter_css_complex_rules,
        test_filter_css_preserves_blank_lines,
        test_filter_css_unknown_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} (error)")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
