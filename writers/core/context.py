"""
Context management for TEI rendering.

The RenderContext dataclass provides an immutable container for all state
that needs to be passed through recursive rendering calls. This eliminates
parameter explosion and enables proper context inheritance.
"""

from dataclasses import dataclass, replace
from typing import Optional, Dict


@dataclass(frozen=True)
class RenderContext:
    """
    Immutable context passed through recursive rendering.

    This context object carries all state information needed during rendering,
    allowing child elements to inherit and modify context from their parents.
    Being immutable (frozen=True) makes it thread-safe and easier to reason about.

    Attributes:
        parent_tag: Tag name of the parent element (e.g., 'p', 'div', 'quote')
        parent_rend: Rendering attribute of parent element
        quote_depth: Current nesting depth of quotes (0 = not in quote, 1 = outer, etc.)
        block_depth: Current nesting depth of block-level elements
        indent_level: Current indentation level (for text output)
        indent_string: String used for one level of indentation (default: 4 spaces)
        line_width: Maximum line width for text wrapping (default: 72)
        xhtml: Whether to generate XHTML-compliant output
        id_map: Mapping of IDs to file paths (for EPUB multi-file support)
    """

    # Parent element info
    parent_tag: str = ''
    parent_rend: str = ''

    # Nesting depth tracking
    quote_depth: int = 0
    block_depth: int = 0

    # Indentation (for text output)
    indent_level: int = 0
    indent_string: str = '    '  # 4 spaces per level

    # Format-specific settings
    line_width: int = 72
    xhtml: bool = False

    # Cross-references (for EPUB)
    id_map: Optional[Dict[str, str]] = None

    def with_parent(self, tag: str, rend: str = '') -> 'RenderContext':
        """
        Return new context with updated parent information.

        Args:
            tag: Parent element tag name
            rend: Parent element rend attribute value

        Returns:
            New RenderContext with updated parent fields
        """
        return replace(self, parent_tag=tag, parent_rend=rend)

    def with_deeper_quote(self) -> 'RenderContext':
        """
        Return new context with incremented quote depth.

        Use this when entering a nested quote to track nesting level
        for alternating quote character selection.

        Returns:
            New RenderContext with quote_depth incremented by 1
        """
        return replace(self, quote_depth=self.quote_depth + 1)

    def with_deeper_block(self) -> 'RenderContext':
        """
        Return new context with incremented block depth.

        Use this when entering a nested block-level element like
        a blockquote or div.

        Returns:
            New RenderContext with block_depth incremented by 1
        """
        return replace(self, block_depth=self.block_depth + 1)

    def with_indent(self, levels: int) -> 'RenderContext':
        """
        Return new context with adjusted indentation level.

        Args:
            levels: Number of indentation levels to add (can be negative to decrease)

        Returns:
            New RenderContext with indent_level adjusted
        """
        return replace(self, indent_level=self.indent_level + levels)

    def with_xhtml(self, xhtml: bool) -> 'RenderContext':
        """
        Return new context with updated XHTML mode.

        Args:
            xhtml: Whether to use XHTML-compliant output

        Returns:
            New RenderContext with updated xhtml setting
        """
        return replace(self, xhtml=xhtml)

    def with_id_map(self, id_map: Dict[str, str]) -> 'RenderContext':
        """
        Return new context with updated ID mapping.

        Args:
            id_map: Dictionary mapping IDs to file paths

        Returns:
            New RenderContext with updated id_map
        """
        return replace(self, id_map=id_map)

    @property
    def current_indent(self) -> str:
        """
        Get the current indentation string.

        Returns:
            String of spaces representing current indentation level
        """
        return self.indent_string * self.indent_level

    @property
    def is_inline_parent(self) -> bool:
        """
        Check if parent element is an inline container.

        Inline containers are elements that contain text and inline markup
        but not block-level elements.

        Returns:
            True if parent is an inline element
        """
        return self.parent_tag in {'p', 'item', 'cell', 'note', 'head', 'l'}

    @property
    def is_block_parent(self) -> bool:
        """
        Check if parent element is a block-level container.

        Returns:
            True if parent is a block-level element
        """
        return self.parent_tag in {'div', 'body', 'front', 'back', 'quote', 'figure'}
