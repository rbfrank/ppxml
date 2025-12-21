"""
Generic TEI tree traverser.

The TEITraverser class walks the TEI document tree and delegates rendering
decisions to a format-specific renderer. This separation allows the same
traversal logic to be reused across all output formats.
"""

from typing import Any
from lxml import etree

from .context import RenderContext
from .base_renderer import BaseRenderer, TEI_NS


class TEITraverser:
    """
    Generic TEI tree walker that delegates rendering to a renderer.

    The traverser knows about TEI document structure but nothing about
    how to render it. All rendering decisions are delegated to the renderer.
    """

    def __init__(self, renderer: BaseRenderer):
        """
        Initialize traverser with a format-specific renderer.

        Args:
            renderer: Renderer instance that will handle actual rendering
        """
        self.renderer = renderer

    def traverse_document(self, doc: etree._ElementTree) -> Any:
        """
        Traverse entire TEI document from root to leaves.

        Processes front matter, body, and back matter sections in order.

        Args:
            doc: Parsed TEI document

        Returns:
            Complete rendered document (type depends on renderer)
        """
        # Start with document header
        parts = [self.renderer.render_document_start(doc)]

        # Initial context for top-level elements
        root_context = RenderContext(parent_tag='TEI')

        # Process front matter if present
        front = doc.find('.//tei:front', TEI_NS)
        if front is not None:
            front_context = root_context.with_parent('front')
            parts.append(self.traverse_section(front, front_context))

        # Process main body
        body = doc.find('.//tei:body', TEI_NS)
        if body is not None:
            body_context = root_context.with_parent('body')
            parts.append(self.traverse_section(body, body_context))

        # Process back matter if present
        back = doc.find('.//tei:back', TEI_NS)
        if back is not None:
            back_context = root_context.with_parent('back')
            parts.append(self.traverse_section(back, back_context))

        # End with document footer
        parts.append(self.renderer.render_document_end())

        # Combine parts (handling different return types)
        return self._combine_parts(parts)

    def traverse_section(self, section: etree._Element, context: RenderContext) -> Any:
        """
        Traverse a document section (front, body, or back).

        Args:
            section: Section element to traverse
            context: Current rendering context

        Returns:
            Rendered section content
        """
        children = []

        for child in section:
            # Skip non-element nodes
            if not isinstance(child.tag, str):
                continue

            child_tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')

            # Update context for this child
            child_rend = child.get('rend', '')
            child_context = context.with_parent(child_tag, child_rend)

            # Traverse the child element
            result = self.traverse_element(child, child_context)
            if result:
                children.append(result)

        return self._combine_parts(children)

    def traverse_element(self, elem: etree._Element, context: RenderContext) -> Any:
        """
        Recursively traverse a single element and its children.

        This is the core recursive method that delegates to the renderer
        for each element.

        Args:
            elem: XML element to traverse
            context: Current rendering context

        Returns:
            Rendered element (type depends on renderer)
        """
        # Strip namespace from tag
        tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')

        # Delegate rendering to the renderer
        # The renderer may call back to this method for child elements
        return self.renderer.render_element(elem, tag, context, self)

    def _combine_parts(self, parts: list) -> Any:
        """
        Combine rendered parts into final output.

        Different renderers may return different types (strings, lists, etc.)
        so this method handles combining them appropriately.

        Args:
            parts: List of rendered parts

        Returns:
            Combined output
        """
        # Filter out None and empty values
        parts = [p for p in parts if p]

        if not parts:
            return ''

        # If all parts are strings, join them
        if all(isinstance(p, str) for p in parts):
            return ''.join(parts)

        # If parts are lists, concatenate them
        if all(isinstance(p, list) for p in parts):
            result = []
            for part in parts:
                result.extend(part)
            return result

        # Mixed types - convert to strings and join
        return ''.join(str(p) for p in parts)
