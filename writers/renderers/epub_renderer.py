"""
EPUB renderer for TEI conversion.

This module extends the HTMLRenderer to provide EPUB3-compliant XHTML output.
The main differences are XHTML compliance (self-closing tags, proper escaping)
and support for cross-file references via id_map in context.
"""

import html
from typing import List, Dict, Optional
from lxml import etree

from .html_renderer import HTMLRenderer
from ..core.context import RenderContext
from ..core.traverser import TEITraverser


class EPUBRenderer(HTMLRenderer):
    """
    EPUB3-compliant XHTML renderer for TEI documents.

    Extends HTMLRenderer with XHTML mode enabled by default.
    Produces output suitable for EPUB chapter files.
    """

    def __init__(self, css_file: Optional[str] = None):
        """
        Initialize EPUB renderer.

        Args:
            css_file: Optional path to CSS file (for documentation; not used in chapter rendering)
        """
        # Initialize parent with XHTML mode
        super().__init__(css_file=css_file)
        self.xhtml = True  # Force XHTML mode

    def render_chapter(self, div: etree._Element, book_title: str,
                      id_map: Optional[Dict[str, str]] = None) -> str:
        """
        Render a single chapter (div element) as complete XHTML document.

        Args:
            div: The div element containing chapter content
            book_title: Book title for fallback
            id_map: Optional mapping of xml:id to filename for cross-references

        Returns:
            Complete XHTML document as string
        """
        # Get chapter title from head element
        head = div.find('tei:head', {'tei': 'http://www.tei-c.org/ns/1.0'})
        chapter_title = self.extract_plain_text(head).strip() if head is not None else book_title

        # Create context with id_map
        context = RenderContext(
            parent_tag='body',
            xhtml=True,
            id_map=id_map or {}
        )

        # Create traverser
        from ..core.traverser import TEITraverser
        traverser = TEITraverser(self)

        # Start XHTML document
        parts = []
        parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        parts.append('<!DOCTYPE html>')
        parts.append('<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">')
        parts.append('<head>')
        parts.append(f'  <title>{html.escape(chapter_title)}</title>')
        parts.append('  <link rel="stylesheet" type="text/css" href="styles.css"/>')
        parts.append('</head>')
        parts.append('<body>')

        # Add chapter heading if present
        if head is not None:
            div_id = div.get('{http://www.w3.org/1998/namespace}id', '')
            if div_id:
                heading_text = self.extract_plain_text(head).strip()
                parts.append(f'<h2 id="{html.escape(div_id)}">{html.escape(heading_text)}</h2>')
            else:
                heading_text = self.extract_plain_text(head).strip()
                parts.append(f'<h2>{html.escape(heading_text)}</h2>')

        # Render all child elements (skipping the head we already processed)
        for elem in div:
            if not isinstance(elem.tag, str):
                continue

            tag = self.strip_namespace(elem.tag)
            if tag == 'head':
                continue  # Already rendered

            # Render element with context
            child_context = context.with_parent('div')
            result = traverser.traverse_element(elem, child_context)

            if result:
                if isinstance(result, list):
                    parts.extend(result)
                else:
                    parts.append(result)

        # Close XHTML document
        parts.append('</body>')
        parts.append('</html>')

        return '\n'.join(parts)

    def render_ref(self, elem: etree._Element, context: RenderContext,
                   traverser: TEITraverser) -> str:
        """
        Render a reference/link with EPUB cross-file support.

        If context has id_map and target points to different file,
        generates proper cross-file reference.

        Args:
            elem: The ref element
            context: Current rendering context
            traverser: Traverser for recursive calls

        Returns:
            HTML anchor element or plain text
        """
        target = elem.get('target', '')
        link_text = self._extract_text_with_markup(elem, context).strip()

        if not target:
            # No target - just render as plain text
            return link_text

        # Check if we have id_map for cross-file references
        if context.id_map and target in context.id_map:
            # Cross-file reference
            filename = context.id_map[target]
            href = f'{filename}#{target}'
            return f'<a href="{html.escape(href)}">{link_text}</a>'
        elif target.startswith('#'):
            # Same-file reference (already has #)
            return f'<a href="{html.escape(target)}">{link_text}</a>'
        elif target.startswith('http://') or target.startswith('https://'):
            # External URL
            return f'<a href="{html.escape(target)}">{link_text}</a>'
        else:
            # Assume it's an ID reference
            return f'<a href="#{html.escape(target)}">{link_text}</a>'

    def render_milestone(self, elem: etree._Element, context: RenderContext,
                        traverser: TEITraverser) -> str:
        """
        Render a milestone (section break) in XHTML.

        XHTML requires self-closing tags to have explicit close.

        Args:
            elem: The milestone element
            context: Current rendering context
            traverser: Traverser for recursive calls

        Returns:
            HTML div element
        """
        rend = self.get_rend_class(elem, default='space')

        if rend == 'stars':
            return '<div class="milestone stars"></div>'
        else:
            return '<div class="milestone space"></div>'

    def render_lb(self, elem: etree._Element, context: RenderContext,
                  traverser: TEITraverser) -> str:
        """
        Render a line break in XHTML.

        XHTML requires <br /> instead of <br>.

        Args:
            elem: The lb element
            context: Current rendering context
            traverser: Traverser for recursive calls

        Returns:
            XHTML line break
        """
        return '<br />'

    def render_graphic(self, elem: etree._Element, context: RenderContext,
                      traverser: TEITraverser) -> str:
        """
        Render a graphic (image) in XHTML.

        XHTML requires self-closing img tags to have explicit close.

        Args:
            elem: The graphic element
            context: Current rendering context
            traverser: Traverser for recursive calls

        Returns:
            XHTML img element
        """
        url = elem.get('url', '')
        if url:
            # Note: Image path mapping is handled by to_epub.py's image_map
            return f'<img src="{html.escape(url)}" alt="" />'
        return ''
