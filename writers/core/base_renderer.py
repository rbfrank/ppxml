"""
Abstract base renderer for TEI conversion.

This module defines the interface that all format-specific renderers must implement.
It also provides common utility methods that all renderers can use.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Set, Tuple, TYPE_CHECKING
from lxml import etree

if TYPE_CHECKING:
    from .traverser import TEITraverser
    from .context import RenderContext

# TEI namespace
TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

# Special token for em-dash (converted from -- in markup)
# Using a Unicode private use character that won't appear in normal text
EMDASH_TOKEN = '\uE000'


class BaseRenderer(ABC):
    """
    Abstract base class for all format renderers.

    Subclasses must implement all abstract methods to handle document-level
    and element-level rendering for their specific output format.
    """

    @abstractmethod
    def render_document_start(self, doc: etree._ElementTree) -> Any:
        """
        Render document header/preamble.

        Args:
            doc: Parsed TEI document

        Returns:
            Header content (type depends on format)
        """
        pass

    @abstractmethod
    def render_document_end(self) -> Any:
        """
        Render document footer/closing.

        Returns:
            Footer content (type depends on format)
        """
        pass

    @abstractmethod
    def render_element(self, elem: etree._Element, tag: str,
                      context: 'RenderContext', traverser: 'TEITraverser') -> Any:
        """
        Render a single element with given context.

        This is the main dispatch method that routes each element to its
        appropriate handler based on the tag name.

        Args:
            elem: The XML element to render
            tag: Tag name (without namespace)
            context: Current rendering context
            traverser: Traverser instance for recursive calls

        Returns:
            Rendered content (type depends on format)
        """
        pass

    # Common utility methods (concrete implementations)

    def get_smart_quotes(self, depth: int) -> Tuple[str, str]:
        """
        Get opening/closing quote characters for given nesting depth.

        Alternates between double and single quotes based on depth.

        Args:
            depth: Quote nesting depth (0 = outer, 1 = inner, etc.)

        Returns:
            Tuple of (opening_quote, closing_quote) Unicode characters
        """
        if depth % 2 == 0:
            # Even depth (0, 2, 4...): use double quotes
            return ('\u201c', '\u201d')  # " and "
        else:
            # Odd depth (1, 3, 5...): use single quotes
            return ('\u2018', '\u2019')  # ' and '

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text to convert em-dashes to token.

        Converts both -- and — (U+2014) to EMDASH_TOKEN for consistent handling.

        Args:
            text: Raw text from XML

        Returns:
            Text with em-dashes converted to EMDASH_TOKEN
        """
        if text:
            # Normalize both -- and Unicode em-dash to token
            text = text.replace('--', EMDASH_TOKEN)
            text = text.replace('\u2014', EMDASH_TOKEN)
        return text

    def extract_plain_text(self, elem: etree._Element) -> str:
        """
        Extract all text content from element, ignoring markup.

        Args:
            elem: The XML element

        Returns:
            Plain text content as a single string
        """
        return ''.join(elem.itertext()).strip()

    def get_rend_class(self, elem: etree._Element, default: str = '') -> str:
        """
        Get the rend attribute value from an element.

        The rend attribute is used for styling/rendering hints in TEI.

        Args:
            elem: The XML element
            default: Default value if rend attribute is missing

        Returns:
            Value of rend attribute or default
        """
        return elem.get('rend', default)

    def get_format_rend(self, elem: etree._Element, format_name: str,
                       default: Optional[str] = None) -> Optional[str]:
        """
        Get format-specific rend attribute.

        Checks for @rend-{format} attribute (e.g., @rend-epub, @rend-html).
        If found, returns its value. Otherwise returns default.

        This allows conditional rendering based on output format. For example:
        <milestone rend="space" rend-epub="none"/> will render spacing in
        HTML/text but be suppressed in EPUB.

        Args:
            elem: The XML element
            format_name: Format identifier ('epub', 'html', 'text')
            default: Value to return if format-specific attribute not found

        Returns:
            Format-specific rend value or default
        """
        format_attr = f'rend-{format_name}'
        return elem.get(format_attr, default)

    def strip_namespace(self, tag: str) -> str:
        """
        Remove TEI namespace from tag name.

        Args:
            tag: Tag name, possibly with namespace

        Returns:
            Tag name without namespace
        """
        return tag.replace(f"{{{TEI_NS['tei']}}}", '')

    def render_children(self, elem: etree._Element, context: 'RenderContext',
                       traverser: 'TEITraverser',
                       skip_tags: Set[str] = None) -> List[Any]:
        """
        Helper to recursively render all child elements.

        This method iterates through an element's children and renders each one
        using the traverser, passing along updated context.

        Args:
            elem: Parent element whose children should be rendered
            context: Current rendering context
            traverser: Traverser instance for recursive calls
            skip_tags: Set of tag names to skip (optional)

        Returns:
            List of rendered child elements
        """
        results = []
        skip_tags = skip_tags or set()

        for child in elem:
            # Skip non-element nodes (comments, etc.)
            if not isinstance(child.tag, str):
                continue

            child_tag = self.strip_namespace(child.tag)

            if child_tag not in skip_tags:
                # Recursively render the child with current context
                # (The child's renderer will update context as needed for its own children)
                result = traverser.traverse_element(child, context)
                if result:  # Only append non-empty results
                    results.append(result)

        return results
