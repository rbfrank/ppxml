"""
HTML renderer for TEI conversion.

This module implements HTML-specific rendering logic using the visitor pattern
with context management. It properly handles nested elements with context inheritance.
"""

import os
import glob
import html as html_module
from datetime import datetime
from typing import Any
from lxml import etree

from ..core.base_renderer import BaseRenderer, TEI_NS
from ..core.context import RenderContext
from ..core.traverser import TEITraverser
from ..common import get_title


class HTMLRenderer(BaseRenderer):
    """
    HTML renderer for TEI documents.

    Converts TEI XML to HTML with proper CSS styling and semantic markup.
    Supports all 33 elements defined in element-set.md.
    """

    def __init__(self, css_file: str = None):
        """
        Initialize HTML renderer.

        Args:
            css_file: Optional path to external CSS file
        """
        self.css_file = css_file
        self.title = ''

    def render_document_start(self, doc: etree._ElementTree) -> str:
        """
        Render HTML document header with embedded CSS.

        Args:
            doc: Parsed TEI document

        Returns:
            HTML header string
        """
        self.title = get_title(doc)

        parts = []
        parts.append('<!DOCTYPE html>')
        parts.append('<html lang="en">')
        parts.append('<head>')
        parts.append('  <meta charset="UTF-8">')
        parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        parts.append(f'  <title>{self.title}</title>')

        # Embed default styles
        parts.append('  <style>')
        parts.extend(self._get_default_css())

        # Append custom CSS if provided
        if self.css_file and os.path.exists(self.css_file):
            with open(self.css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            parts.append('')
            parts.append('    /* Custom styles */')
            for line in css_content.splitlines():
                parts.append('    ' + line)

        parts.append('  </style>')
        parts.append('</head>')
        parts.append('<body>')
        parts.append(f'<h1>{self.title}</h1>')

        return '\n'.join(parts)

    def render_document_end(self) -> str:
        """
        Render HTML document footer.

        Returns:
            HTML footer string
        """
        return '\n</body>\n</html>'

    def _get_default_css(self) -> list:
        """Get default CSS rules as list of strings."""
        return [
            '    body { max-width: 40em; margin: 2em auto; padding: 0 1em; font-family: serif; line-height: 1.6; }',
            '    h1 { text-align: center; }',
            '    h2 { margin-top: 2em; }',
            '    .italic { font-style: italic; }',
            '    .bold { font-weight: bold; }',
            '    .underline { text-decoration: underline; }',
            '    .small-caps { font-variant: small-caps; }',
            '    .signature { text-align: right; font-style: italic; margin-top: 0.5em; }',
            '    blockquote { margin: 1em 2em; }',
            '    figure { margin: 2em auto; width: 80%; max-width: 100%; text-align: center; }',
            '    figure.left { float: left; margin: 0 2em 1em 0; width: 50%; max-width: 50%; }',
            '    figure.right { float: right; margin: 0 0 1em 2em; width: 50%; max-width: 50%; }',
            '    figure.center { margin: 2em auto; display: block; }',
            '    figure img { width: 100%; height: auto; }',
            '    figcaption { margin-top: 0.5em; font-style: italic; }',
            '    .poem { margin: 1em 0; }',
            '    .poem.center { text-align: center; }',
            '    .poem.center .stanza { display: inline-block; text-align: left; }',
            '    .poem-title { text-align: center; font-weight: bold; margin-bottom: 1em; }',
            '    .stanza { margin-bottom: 1em; }',
            '    .line { margin-top: 0; margin-bottom: 0; }',
            '    .indent { margin-left: 2em; }',
            '    .indent2 { margin-left: 4em; }',
            '    .indent3 { margin-left: 6em; }',
            '    .center { text-align: center; }',
            '    .milestone { text-align: center; margin: 2em 0; }',
            '    .milestone.stars::before { content: "*       *       *       *       *"; white-space: pre; }',
            '    .milestone.space { height: 2em; }',
            '    table { border-collapse: collapse; margin: 1em 0; }',
            '    td, th { border: 1px solid #ccc; padding: 0.5em; }',
        ]

    def render_element(self, elem: etree._Element, tag: str,
                      context: RenderContext, traverser: TEITraverser) -> str:
        """
        Render a single element with given context.

        Dispatches to appropriate handler based on tag name.

        Args:
            elem: The XML element to render
            tag: Tag name (without namespace)
            context: Current rendering context
            traverser: Traverser instance for recursive calls

        Returns:
            Rendered HTML string
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
        elif tag == 'signed':
            return self.render_signed(elem, context, traverser)
        else:
            # Unknown block element - just render text
            return self.render_text_content(elem, context)

    def render_div(self, elem: etree._Element, context: RenderContext,
                   traverser: TEITraverser) -> str:
        """Render a div element."""
        div_type = elem.get('type', '')
        div_id = elem.get('{http://www.w3.org/XML/1998/namespace}id', '')

        parts = []

        # Build opening div tag
        if div_id and div_type:
            parts.append(f'<div id="{div_id}" class="{div_type}">')
        elif div_id:
            parts.append(f'<div id="{div_id}">')
        elif div_type:
            parts.append(f'<div class="{div_type}">')
        else:
            parts.append('<div>')

        # Process children
        child_context = context.with_parent('div', div_type)
        children = self.render_children(elem, child_context, traverser)
        parts.extend(children)

        parts.append('</div>')
        return '\n'.join(parts)

    def render_head(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> str:
        """Render a heading element."""
        # Determine heading level based on context
        if context.parent_tag in ('div', 'front', 'back', 'body'):
            # Chapter/section heading
            div_id = elem.getparent().get('{http://www.w3.org/XML/1998/namespace}id', '')
            if div_id:
                return f'<h2 id="{div_id}">{self.render_text_content(elem, context)}</h2>'
            else:
                return f'<h2>{self.render_text_content(elem, context)}</h2>'
        else:
            # Inline heading (like poem title or figure caption)
            # These are handled by their parent elements
            return ''

    def render_paragraph(self, elem: etree._Element, context: RenderContext,
                        traverser: TEITraverser) -> str:
        """Render a paragraph element."""
        rend = self.get_rend_class(elem)
        child_context = context.with_parent('p', rend)
        content = self.render_text_content(elem, child_context)

        if rend:
            return f'<p class="{rend}">{content}</p>'
        else:
            return f'<p>{content}</p>'

    def render_quote(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> str:
        """
        Render a quote element - inline or block depending on context.

        This demonstrates true recursion with context passing.
        """
        if context.is_inline_parent:
            # Inline quote - use smart quotes with depth tracking
            child_context = context.with_deeper_quote()
            content = self.render_text_content(elem, child_context)
            open_quote, close_quote = self.get_smart_quotes(context.quote_depth)
            return f'{open_quote}{content}{close_quote}'
        else:
            # Block quote - recursively render children
            block_children = [child for child in elem
                            if isinstance(child.tag, str) and
                            self.strip_namespace(child.tag) in
                            ['p', 'lg', 'list', 'table', 'figure', 'div', 'quote', 'signed']]

            if block_children:
                # Render children with blockquote context
                child_context = context.with_deeper_block()
                children = []
                for child in block_children:
                    child_tag = self.strip_namespace(child.tag)
                    child_rend = child.get('rend', '')
                    grandchild_context = child_context.with_parent(child_tag, child_rend)
                    result = traverser.traverse_element(child, grandchild_context)
                    if result:
                        children.append(result)

                inner = '\n'.join(children)
                return f'<blockquote>\n{inner}\n</blockquote>'
            else:
                # Fallback: wrap text in paragraph
                child_context = context.with_parent('quote')
                content = self.render_text_content(elem, child_context)
                return f'<blockquote><p>{content}</p></blockquote>'

    def render_line_group(self, elem: etree._Element, context: RenderContext,
                         traverser: TEITraverser) -> str:
        """Render a line group (poetry/verse)."""
        rend = self.get_rend_class(elem)
        parts = []

        if rend:
            parts.append(f'<div class="poem {rend}">')
        else:
            parts.append('<div class="poem">')

        child_context = context.with_parent('lg', rend)

        for child in elem:
            if not isinstance(child.tag, str):
                continue

            child_tag = self.strip_namespace(child.tag)

            if child_tag == 'head':
                # Poem title
                content = self.render_text_content(child, child_context)
                parts.append(f'  <div class="poem-title">{content}</div>')

            elif child_tag == 'lg':
                # Nested stanza
                parts.append('  <div class="stanza">')
                stanza_context = child_context.with_parent('lg')

                for stanza_child in child:
                    if not isinstance(stanza_child.tag, str):
                        continue
                    stanza_child_tag = self.strip_namespace(stanza_child.tag)

                    if stanza_child_tag == 'l':
                        # Line of verse
                        line_rend = stanza_child.get('rend', '')
                        line_class = f'line {line_rend}' if line_rend else 'line'
                        line_content = self.render_text_content(stanza_child, stanza_context)
                        parts.append(f'    <div class="{line_class}">{line_content}</div>')
                    else:
                        # Other elements in stanza (recursive)
                        result = traverser.traverse_element(stanza_child, stanza_context)
                        if result:
                            for line in result.split('\n'):
                                parts.append('    ' + line)

                parts.append('  </div>')

            elif child_tag == 'l':
                # Line of verse (not in stanza)
                line_rend = child.get('rend', '')
                line_class = f'line {line_rend}' if line_rend else 'line'
                line_content = self.render_text_content(child, child_context)
                parts.append(f'  <div class="{line_class}">{line_content}</div>')

            else:
                # Other block elements in poem
                result = traverser.traverse_element(child, child_context)
                if result:
                    for line in result.split('\n'):
                        parts.append('  ' + line)

        parts.append('</div>')
        return '\n'.join(parts)

    def render_list(self, elem: etree._Element, context: RenderContext,
                   traverser: TEITraverser) -> str:
        """Render a list element."""
        items = []
        child_context = context.with_parent('list')

        for item in elem.findall('tei:item', TEI_NS):
            item_context = child_context.with_parent('item')
            content = self.render_text_content(item, item_context)
            items.append(f'  <li>{content}</li>')

        return '<ul>\n' + '\n'.join(items) + '\n</ul>'

    def render_table(self, elem: etree._Element, context: RenderContext,
                    traverser: TEITraverser) -> str:
        """Render a table element."""
        rows = []
        child_context = context.with_parent('table')

        for row in elem.findall('tei:row', TEI_NS):
            cells = []
            row_context = child_context.with_parent('row')

            for cell in row.findall('tei:cell', TEI_NS):
                cell_tag = 'th' if cell.get('role') == 'label' else 'td'
                cell_context = row_context.with_parent('cell')
                content = self.render_text_content(cell, cell_context)
                cells.append(f'    <{cell_tag}>{content}</{cell_tag}>')

            rows.append('  <tr>\n' + '\n'.join(cells) + '\n  </tr>')

        return '<table>\n' + '\n'.join(rows) + '\n</table>'

    def render_figure(self, elem: etree._Element, context: RenderContext,
                     traverser: TEITraverser) -> str:
        """Render a figure with image and caption."""
        graphic = elem.find('tei:graphic', TEI_NS)
        width = graphic.get('width', '') if graphic is not None else ''
        rend = self.get_rend_class(elem)

        parts = []

        # Build opening figure tag
        if width and rend:
            parts.append(f'<figure class="{rend}" style="width: {width};">')
        elif width:
            parts.append(f'<figure style="width: {width};">')
        elif rend:
            parts.append(f'<figure class="{rend}">')
        else:
            parts.append('<figure>')

        # Render image
        if graphic is not None:
            url = graphic.get('url', '')

            # Get alt text from figDesc
            figdesc = elem.find('tei:figDesc', TEI_NS)
            alt_text = self.extract_plain_text(figdesc) if figdesc is not None else ''
            if context.xhtml:
                alt_text = html_module.escape(alt_text)

            if context.xhtml:
                parts.append(f'  <img src="{url}" alt="{alt_text}"/>')
            else:
                parts.append(f'  <img src="{url}" alt="{alt_text}">')

        # Add caption from head
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            child_context = context.with_parent('figure')
            caption = self.render_text_content(head, child_context)
            parts.append(f'  <figcaption>{caption}</figcaption>')

        parts.append('</figure>')
        return '\n'.join(parts)

    def render_milestone(self, elem: etree._Element, context: RenderContext,
                        traverser: TEITraverser) -> str:
        """Render a milestone (section break)."""
        rend = self.get_rend_class(elem, default='space')
        return f'<div class="milestone {rend}"></div>'

    def render_signed(self, elem: etree._Element, context: RenderContext,
                     traverser: TEITraverser) -> str:
        """Render a signature line."""
        text = self.render_text_content(elem, context)
        return f'<div class="signature">{text}</div>'

    def render_text_content(self, elem: etree._Element, context: RenderContext) -> str:
        """
        Extract and render text content with inline markup.

        This handles all inline elements like <hi>, <quote>, <ref>, etc.
        Properly tracks quote depth for nested inline quotes.

        Args:
            elem: Element to extract text from
            context: Current rendering context

        Returns:
            HTML string with inline markup
        """
        result = ''

        # Add initial text
        if elem.text:
            if context.xhtml:
                result = html_module.escape(elem.text)
            else:
                result = elem.text

        # Process child elements
        for child in elem:
            if not isinstance(child.tag, str):
                continue

            tag = self.strip_namespace(child.tag)

            if tag == 'lb':
                # Line break
                result += '<br/>' if context.xhtml else '<br>'

            elif tag == 'quote':
                # Nested inline quote - increment depth
                child_context = context.with_deeper_quote()
                child_text = self.render_text_content(child, child_context)
                open_quote, close_quote = self.get_smart_quotes(context.quote_depth)
                result += f'{open_quote}{child_text}{close_quote}'

            elif tag == 'hi':
                # Highlighted text
                rend = child.get('rend', 'italic')
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)

                if rend == 'italic':
                    result += f'<i>{child_text}</i>'
                elif rend == 'bold':
                    result += f'<b>{child_text}</b>'
                else:
                    result += f'<span class="{rend}">{child_text}</span>'

            elif tag == 'emph':
                # Emphasis
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += f'<em>{child_text}</em>'

            elif tag == 'ref':
                # Reference/link
                target = child.get('target', '#')

                # Handle cross-references
                if context.id_map and not target.startswith(('#', 'http://', 'https://', '//')):
                    if target in context.id_map:
                        target_file = context.id_map[target]
                        target = f'{target_file}#{target}'
                    else:
                        target = '#' + target
                elif not target.startswith(('#', 'http://', 'https://', '//')):
                    target = '#' + target

                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += f'<a href="{target}">{child_text}</a>'

            elif tag == 'note':
                # Footnote/annotation
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += f'<sup>[{child_text}]</sup>'

            elif tag == 'foreign':
                # Foreign language text
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += f'<i>{child_text}</i>'

            elif tag == 'title':
                # Title of a work
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += f'<i>{child_text}</i>'

            else:
                # Unknown inline element - just extract text
                child_text = self.extract_plain_text(child)
                if context.xhtml:
                    child_text = html_module.escape(child_text)
                result += child_text

            # Add tail text
            if child.tail:
                if context.xhtml:
                    result += html_module.escape(child.tail)
                else:
                    result += child.tail

        return result
