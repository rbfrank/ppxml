"""
Text renderer for TEI conversion.

This module implements plain text rendering with line wrapping and indentation.
Uses the visitor pattern with proper context management for recursive rendering.
"""

import textwrap
import re
from typing import List
from lxml import etree

from ..core.base_renderer import BaseRenderer, TEI_NS
from ..core.context import RenderContext
from ..core.traverser import TEITraverser
from ..common import get_title


class TextRenderer(BaseRenderer):
    """
    Plain text renderer for TEI documents.

    Converts TEI XML to plain text with proper line wrapping,
    indentation for blockquotes and poetry, and emphasis marking.
    """

    def __init__(self, line_width: int = 72):
        """
        Initialize text renderer.

        Args:
            line_width: Maximum line width for text wrapping (default: 72)
        """
        self.line_width = line_width
        self.title = ''

    def render_document_start(self, doc: etree._ElementTree) -> List[str]:
        """
        Render document header (returns empty list for text).

        Args:
            doc: Parsed TEI document

        Returns:
            Empty list (no header in plain text)
        """
        self.title = get_title(doc)
        return []

    def render_document_end(self) -> List[str]:
        """
        Render document footer (returns empty list for text).

        Returns:
            Empty list (no footer in plain text)
        """
        return []

    def render_element(self, elem: etree._Element, tag: str,
                      context: RenderContext, traverser: TEITraverser) -> List[str]:
        """
        Render a single element with given context.

        Args:
            elem: The XML element to render
            tag: Tag name (without namespace)
            context: Current rendering context
            traverser: Traverser instance for recursive calls

        Returns:
            List of output lines
        """
        # Dispatch to specific handler
        if tag == 'div':
            return self.render_div(elem, context, traverser)
        elif tag == 'head':
            return self.render_head(elem, context, traverser)
        elif tag == 'p':
            return self.render_paragraph(elem, context, traverser)
        elif tag == 'quote':
            return self.render_quote(elem, context, traverser)
        elif tag == 'lg':
            return self.render_line_group(elem, context, traverser)
        elif tag == 'list':
            return self.render_list(elem, context, traverser)
        elif tag == 'table':
            return self.render_table(elem, context, traverser)
        elif tag == 'figure':
            return self.render_figure(elem, context, traverser)
        elif tag == 'milestone':
            return self.render_milestone(elem, context, traverser)
        else:
            # Unknown element - skip
            return []

    def render_div(self, elem: etree._Element, context: RenderContext,
                   traverser: TEITraverser) -> List[str]:
        """Render a div element."""
        lines = []
        child_context = context.with_parent('div')
        children = self.render_children(elem, child_context, traverser)

        for child in children:
            if isinstance(child, list):
                lines.extend(child)
            else:
                lines.append(child)

        return lines

    def render_head(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> List[str]:
        """Render a heading element."""
        heading_text = self.extract_plain_text(elem).strip()
        if not heading_text:
            return []

        lines = []

        if context.parent_tag == 'body':
            # Chapter heading: 3 blank lines before, uppercase, 2 blank after
            lines.extend(['', '', ''])
            lines.append(heading_text.upper())
            lines.extend(['', ''])
        elif context.parent_tag == 'front':
            # Front matter heading: underline with =
            lines.append(heading_text)
            lines.append('=' * len(heading_text))
            lines.append('')
        elif context.parent_tag == 'back':
            # Back matter heading: uppercase, blank after
            lines.append(heading_text.upper())
            lines.append('')
        elif context.parent_tag == 'div':
            # Section heading
            lines.append(heading_text.upper())
            lines.extend(['', ''])
        # else: inline heading (like poem title) - handled by parent element

        return lines

    def render_paragraph(self, elem: etree._Element, context: RenderContext,
                        traverser: TEITraverser) -> List[str]:
        """Render a paragraph with text wrapping."""
        text = self._extract_text_with_emphasis(elem, context).strip()
        if not text:
            return []

        # Normalize whitespace (collapse internal line breaks)
        normalized = ' '.join(text.split())

        # Wrap text with indentation
        # Use textwrap's indent parameters so it accounts for indent in width calculation
        wrapped = textwrap.fill(
            normalized,
            width=self.line_width,
            initial_indent=context.current_indent,
            subsequent_indent=context.current_indent,
            break_long_words=False,
            break_on_hyphens=False
        )

        # Split into lines
        lines = wrapped.split('\n')
        lines.append('')  # Blank line after paragraph
        return lines

    def render_quote(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> List[str]:
        """
        Render a quote - inline quotes handled in text extraction,
        block quotes indented.
        """
        if context.is_inline_parent:
            # Inline quotes are handled in _extract_text_with_emphasis
            # This shouldn't be reached, but just in case
            return []

        # Block quote - indent by one level
        child_context = context.with_indent(1).with_deeper_block()

        # Find block-level children
        block_children = [child for child in elem
                        if isinstance(child.tag, str) and
                        self.strip_namespace(child.tag) in
                        ['p', 'lg', 'list', 'table', 'figure', 'div', 'quote']]

        if block_children:
            lines = []
            for child in block_children:
                child_tag = self.strip_namespace(child.tag)
                grandchild_context = child_context.with_parent(child_tag)
                result = traverser.traverse_element(child, grandchild_context)
                if result:
                    if isinstance(result, list):
                        lines.extend(result)
                    else:
                        lines.append(result)
            return lines
        else:
            # Fallback: wrap text with indentation
            text = self._extract_text_with_emphasis(elem, child_context).strip()
            if not text:
                return []

            normalized = ' '.join(text.split())

            wrapped = textwrap.fill(
                normalized,
                width=self.line_width,
                initial_indent=child_context.current_indent,
                subsequent_indent=child_context.current_indent,
                break_long_words=False,
                break_on_hyphens=False
            )

            lines = wrapped.split('\n')
            lines.append('')
            return lines

    def render_line_group(self, elem: etree._Element, context: RenderContext,
                         traverser: TEITraverser) -> List[str]:
        """Render a line group (poetry/verse)."""
        lines = []
        rend = self.get_rend_class(elem)
        child_context = context.with_parent('lg', rend)

        for child in elem:
            if not isinstance(child.tag, str):
                continue

            child_tag = self.strip_namespace(child.tag)

            if child_tag == 'head':
                # Poem title
                title = self.extract_plain_text(child).strip()
                if title:
                    if rend == 'center':
                        padding = (self.line_width - len(title)) // 2
                        lines.append(' ' * padding + title.upper())
                    else:
                        lines.append(context.current_indent + '    ' + title.upper())
                    lines.append('')

            elif child_tag == 'lg':
                # Nested stanza
                stanza_lines = self._render_stanza(child, context)
                lines.extend(stanza_lines)

            elif child_tag == 'l':
                # Line of verse (not in stanza)
                line_text = self._extract_text_with_emphasis(child, context).strip()
                line_rend = child.get('rend', '')
                formatted_line = self._format_verse_line(line_text, line_rend, rend, context)
                lines.append(formatted_line)

            else:
                # Other block elements in poem
                result = traverser.traverse_element(child, child_context)
                if result:
                    if isinstance(result, list):
                        lines.extend(result)
                    else:
                        lines.append(result)

        lines.append('')  # Blank after poem
        return lines

    def _render_stanza(self, stanza_elem: etree._Element, context: RenderContext) -> List[str]:
        """Render a stanza (nested lg)."""
        stanza_lines = []
        stanza_rend = stanza_elem.get('rend', '')
        line_texts = []
        line_rends = []

        for child in stanza_elem:
            if not isinstance(child.tag, str):
                continue

            child_tag = self.strip_namespace(child.tag)
            if child_tag == 'l':
                line_text = self._extract_text_with_emphasis(child, context).strip()
                line_rend = child.get('rend', '')
                line_rends.append(line_rend)

                # Apply individual line rendering
                if line_rend == 'center':
                    padding = (self.line_width - self._visual_length(line_text)) // 2
                    line_text = ' ' * padding + line_text
                elif line_rend == 'indent':
                    line_text = '  ' + line_text
                elif line_rend == 'indent2':
                    line_text = '    ' + line_text
                elif line_rend == 'indent3':
                    line_text = '      ' + line_text

                line_texts.append(line_text)

        # Apply stanza-level centering if needed
        if stanza_rend == 'center' and line_texts:
            max_len = max(self._visual_length(l) for l in line_texts)
            block_padding = (self.line_width - max_len) // 2
            for line_text in line_texts:
                stanza_lines.append(' ' * block_padding + line_text)
        else:
            # Add base indentation for non-centered stanzas
            for i, line_text in enumerate(line_texts):
                if i < len(line_rends) and line_rends[i] == 'center':
                    # Already centered
                    stanza_lines.append(line_text)
                else:
                    stanza_lines.append(context.current_indent + '    ' + line_text)

        stanza_lines.append('')  # Blank after stanza
        return stanza_lines

    def _format_verse_line(self, line_text: str, line_rend: str,
                          poem_rend: str, context: RenderContext) -> str:
        """Format a single line of verse."""
        if line_rend == 'center':
            padding = (self.line_width - self._visual_length(line_text)) // 2
            return ' ' * padding + line_text
        elif line_rend == 'indent':
            return context.current_indent + '      ' + line_text
        elif line_rend == 'indent2':
            return context.current_indent + '        ' + line_text
        elif line_rend == 'indent3':
            return context.current_indent + '          ' + line_text
        else:
            return context.current_indent + '    ' + line_text

    def render_list(self, elem: etree._Element, context: RenderContext,
                   traverser: TEITraverser) -> List[str]:
        """Render a list with bullet points."""
        lines = []
        child_context = context.with_parent('list')

        for item in elem.findall('tei:item', TEI_NS):
            item_context = child_context.with_parent('item')
            item_text = self._extract_text_with_emphasis(item, item_context).strip()
            if item_text:
                # Use textwrap with indent parameters
                indent = context.current_indent

                wrapped = textwrap.fill(
                    item_text,
                    width=self.line_width,
                    initial_indent=indent + '  • ',
                    subsequent_indent=indent + '    ',
                    break_long_words=False,
                    break_on_hyphens=False
                )
                lines.append(wrapped)

        lines.append('')  # Blank after list
        return lines

    def render_table(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> List[str]:
        """Render a simple text table."""
        lines = []
        rows_data = []

        # Collect all cell data
        for row in elem.findall('tei:row', TEI_NS):
            cells = []
            for cell in row.findall('tei:cell', TEI_NS):
                cell_text = self.extract_plain_text(cell).strip()
                cells.append(cell_text)
            if cells:
                rows_data.append(cells)

        if rows_data:
            # Calculate column widths
            num_cols = max(len(row) for row in rows_data)
            col_widths = [0] * num_cols
            for row in rows_data:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell))

            # Render table with indentation
            indent = context.current_indent
            for row in rows_data:
                row_text = '  '.join(
                    cell.ljust(col_widths[i]) for i, cell in enumerate(row)
                )
                lines.append(indent + '  ' + row_text)

        lines.append('')  # Blank after table
        return lines

    def render_figure(self, elem: etree._Element, context: RenderContext,
                     traverser: TEITraverser) -> List[str]:
        """Render a figure as caption text."""
        lines = []

        # Get caption from head element
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            caption = self.extract_plain_text(head).strip()
            if caption:
                indent = context.current_indent

                wrapped = textwrap.fill(
                    f'[Illustration: {caption}]',
                    width=self.line_width,
                    initial_indent=indent,
                    subsequent_indent=indent,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                lines.extend(wrapped.split('\n'))
            else:
                lines.append(context.current_indent + '[Illustration]')
        else:
            lines.append(context.current_indent + '[Illustration]')

        lines.append('')  # Blank after figure
        return lines

    def render_milestone(self, elem: etree._Element, context: RenderContext,
                        traverser: TEITraverser) -> List[str]:
        """Render a milestone (section break)."""
        rend = self.get_rend_class(elem, default='space')

        if rend == 'stars':
            # Center the asterisks
            stars = '*       *       *       *       *'
            padding = (self.line_width - len(stars)) // 2
            return [' ' * padding + stars, '']
        else:
            # Just blank lines for other types
            return ['', '']

    def _extract_text_with_emphasis(self, elem: etree._Element,
                                    context: RenderContext) -> str:
        """
        Extract text content with emphasis markers and inline quotes.

        Uses underscores to mark emphasis in plain text.
        Properly handles nested inline quotes with context.

        Args:
            elem: Element to extract text from
            context: Current rendering context

        Returns:
            Text string with emphasis markers
        """
        result = ''

        if elem.text:
            result = elem.text

        for child in elem:
            if not isinstance(child.tag, str):
                continue

            tag = self.strip_namespace(child.tag)

            if tag == 'lb':
                # Line break
                result += '\n'

            elif tag == 'quote':
                # Nested inline quote - use context for depth
                child_context = context.with_deeper_quote()
                child_text = self._extract_text_with_emphasis(child, child_context)
                open_quote, close_quote = self.get_smart_quotes(context.quote_depth)
                result += f'{open_quote}{child_text}{close_quote}'

            elif tag in ['emph', 'hi']:
                # Emphasis - mark with underscores
                child_text = self.extract_plain_text(child)
                result += f'_{child_text}_'

            elif tag == 'note':
                # Footnote
                child_text = self.extract_plain_text(child)
                result += f' [{child_text}]'

            elif tag == 'ref':
                # Reference - just include the text
                child_text = self.extract_plain_text(child)
                result += child_text

            elif tag in ['title', 'foreign']:
                # Title/foreign - mark like emphasis
                child_text = self.extract_plain_text(child)
                result += f'_{child_text}_'

            else:
                # Unknown inline element - just extract text
                child_text = self.extract_plain_text(child)
                result += child_text

            if child.tail:
                result += child.tail

        return result

    def _visual_length(self, text: str) -> int:
        """
        Calculate visual length of text, excluding emphasis markers.

        Args:
            text: Text possibly containing _emphasis_ markers

        Returns:
            Visual length without markers
        """
        # Remove underscore pairs that mark emphasis
        visual = re.sub(r'_([^_]+)_', r'\1', text)
        return len(visual)
