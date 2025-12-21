"""
Unit tests for RenderContext.

Tests the immutable context object and its helper methods.
"""

import pytest
from writers.core.context import RenderContext


class TestRenderContext:
    """Test RenderContext dataclass and its methods."""

    def test_default_initialization(self):
        """Test context with default values."""
        ctx = RenderContext()

        assert ctx.parent_tag == ''
        assert ctx.parent_rend == ''
        assert ctx.quote_depth == 0
        assert ctx.block_depth == 0
        assert ctx.indent_level == 0
        assert ctx.indent_string == '    '
        assert ctx.line_width == 72
        assert ctx.xhtml is False
        assert ctx.id_map is None

    def test_custom_initialization(self):
        """Test context with custom values."""
        id_map = {'id1': 'file1.html'}
        ctx = RenderContext(
            parent_tag='div',
            quote_depth=2,
            indent_level=3,
            line_width=80,
            xhtml=True,
            id_map=id_map
        )

        assert ctx.parent_tag == 'div'
        assert ctx.quote_depth == 2
        assert ctx.indent_level == 3
        assert ctx.line_width == 80
        assert ctx.xhtml is True
        assert ctx.id_map == id_map

    def test_with_parent(self):
        """Test with_parent() returns new context with updated parent."""
        ctx = RenderContext()
        new_ctx = ctx.with_parent('p', 'italic')

        # Original unchanged
        assert ctx.parent_tag == ''
        assert ctx.parent_rend == ''

        # New context updated
        assert new_ctx.parent_tag == 'p'
        assert new_ctx.parent_rend == 'italic'

        # Other fields preserved
        assert new_ctx.quote_depth == ctx.quote_depth
        assert new_ctx.indent_level == ctx.indent_level

    def test_with_deeper_quote(self):
        """Test with_deeper_quote() increments quote depth."""
        ctx = RenderContext(quote_depth=0)

        ctx1 = ctx.with_deeper_quote()
        assert ctx1.quote_depth == 1
        assert ctx.quote_depth == 0  # Original unchanged

        ctx2 = ctx1.with_deeper_quote()
        assert ctx2.quote_depth == 2
        assert ctx1.quote_depth == 1  # Previous unchanged

    def test_with_deeper_block(self):
        """Test with_deeper_block() increments block depth."""
        ctx = RenderContext(block_depth=0)

        ctx1 = ctx.with_deeper_block()
        assert ctx1.block_depth == 1
        assert ctx.block_depth == 0  # Original unchanged

        ctx2 = ctx1.with_deeper_block()
        assert ctx2.block_depth == 2

    def test_with_indent(self):
        """Test with_indent() adjusts indentation level."""
        ctx = RenderContext(indent_level=0)

        # Increase indent
        ctx1 = ctx.with_indent(2)
        assert ctx1.indent_level == 2
        assert ctx.indent_level == 0  # Original unchanged

        # Decrease indent (negative)
        ctx2 = ctx1.with_indent(-1)
        assert ctx2.indent_level == 1

    def test_with_xhtml(self):
        """Test with_xhtml() updates XHTML mode."""
        ctx = RenderContext(xhtml=False)

        ctx1 = ctx.with_xhtml(True)
        assert ctx1.xhtml is True
        assert ctx.xhtml is False  # Original unchanged

    def test_with_id_map(self):
        """Test with_id_map() updates ID mapping."""
        ctx = RenderContext()
        id_map = {'ch1': 'chapter1.html', 'ch2': 'chapter2.html'}

        ctx1 = ctx.with_id_map(id_map)
        assert ctx1.id_map == id_map
        assert ctx.id_map is None  # Original unchanged

    def test_current_indent_property(self):
        """Test current_indent property calculates indentation correctly."""
        ctx = RenderContext(indent_level=0)
        assert ctx.current_indent == ''

        ctx = RenderContext(indent_level=1)
        assert ctx.current_indent == '    '  # 4 spaces

        ctx = RenderContext(indent_level=3)
        assert ctx.current_indent == '            '  # 12 spaces

    def test_current_indent_with_custom_string(self):
        """Test current_indent with custom indent string."""
        ctx = RenderContext(indent_level=2, indent_string='  ')  # 2 spaces
        assert ctx.current_indent == '    '  # 2 levels * 2 spaces

    def test_is_inline_parent(self):
        """Test is_inline_parent property."""
        # Inline parents
        for tag in ['p', 'item', 'cell', 'note', 'head', 'l']:
            ctx = RenderContext(parent_tag=tag)
            assert ctx.is_inline_parent is True, f"{tag} should be inline parent"

        # Block parents
        for tag in ['div', 'body', 'quote', 'lg']:
            ctx = RenderContext(parent_tag=tag)
            assert ctx.is_inline_parent is False, f"{tag} should not be inline parent"

    def test_is_block_parent(self):
        """Test is_block_parent property."""
        # Block parents
        for tag in ['div', 'body', 'front', 'back', 'quote', 'figure']:
            ctx = RenderContext(parent_tag=tag)
            assert ctx.is_block_parent is True, f"{tag} should be block parent"

        # Inline parents
        for tag in ['p', 'item', 'l']:
            ctx = RenderContext(parent_tag=tag)
            assert ctx.is_block_parent is False, f"{tag} should not be block parent"

    def test_immutability(self):
        """Test that context is truly immutable."""
        ctx = RenderContext(quote_depth=0)

        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            ctx.quote_depth = 5

    def test_chaining_methods(self):
        """Test that context methods can be chained."""
        ctx = RenderContext()

        # Chain multiple context modifications
        new_ctx = ctx.with_parent('quote').with_deeper_quote().with_indent(1)

        assert new_ctx.parent_tag == 'quote'
        assert new_ctx.quote_depth == 1
        assert new_ctx.indent_level == 1

        # Original unchanged
        assert ctx.parent_tag == ''
        assert ctx.quote_depth == 0
        assert ctx.indent_level == 0

    def test_context_preserves_unrelated_fields(self):
        """Test that modifying one field doesn't affect others."""
        ctx = RenderContext(
            parent_tag='div',
            quote_depth=2,
            indent_level=1,
            line_width=80,
            xhtml=True
        )

        # Modify just quote depth
        new_ctx = ctx.with_deeper_quote()

        # Only quote_depth changes
        assert new_ctx.quote_depth == 3
        assert new_ctx.parent_tag == 'div'
        assert new_ctx.indent_level == 1
        assert new_ctx.line_width == 80
        assert new_ctx.xhtml is True
