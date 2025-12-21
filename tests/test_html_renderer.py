"""
Unit tests for HTMLRenderer.

Tests HTML rendering with proper context management and recursion.
"""

import pytest
from lxml import etree

from writers.core.context import RenderContext
from writers.core.traverser import TEITraverser
from writers.renderers.html_renderer import HTMLRenderer
from writers.common import parse_tei


class TestHTMLRenderer:
    """Test HTMLRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = HTMLRenderer()
        self.traverser = TEITraverser(self.renderer)

    def test_simple_document(self):
        """Test rendering a simple document."""
        doc = parse_tei('tests/fixtures/simple.xml')
        result = self.traverser.traverse_document(doc)

        assert '<!DOCTYPE html>' in result
        assert '<title>Simple Test Document</title>' in result
        assert '<h1>Simple Test Document</h1>' in result
        assert '<h2>Test Chapter</h2>' in result
        assert '<p>This is a simple paragraph.</p>' in result
        assert '<i>italic text</i>' in result

    def test_paragraph_rendering(self):
        """Test basic paragraph rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Simple text</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert result == '<p>Simple text</p>'

    def test_paragraph_with_rend(self):
        """Test paragraph with rend attribute."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0" rend="no-indent">Text</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert result == '<p class="no-indent">Text</p>'

    def test_inline_quote(self):
        """Test inline quote uses smart quotes."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">He said <quote>hello</quote>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Should use double quotes (U+201C and U+201D)
        assert '\u201c' in result  # Opening quote
        assert '\u201d' in result  # Closing quote
        assert 'hello' in result

    def test_nested_inline_quotes(self):
        """Test nested inline quotes alternate quote marks."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">A <quote>B <quote>C</quote> D</quote> E</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Outer quote: double quotes (depth 0 = even)
        # Inner quote: single quotes (depth 1 = odd)
        assert result.count('\u201c') == 1  # One opening double quote
        assert result.count('\u201d') == 1  # One closing double quote
        assert result.count('\u2018') == 1  # One opening single quote
        assert result.count('\u2019') == 1  # One closing single quote

    def test_block_quote_simple(self):
        """Test block quote with single paragraph."""
        xml = '''<quote xmlns="http://www.tei-c.org/ns/1.0">
            <p>Quoted text</p>
        </quote>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_quote(elem, context, self.traverser)

        assert '<blockquote>' in result
        assert '<p>Quoted text</p>' in result
        assert '</blockquote>' in result

    def test_block_quote_multiple_paragraphs(self):
        """Test block quote with multiple paragraphs."""
        xml = '''<quote xmlns="http://www.tei-c.org/ns/1.0">
            <p>First paragraph</p>
            <p>Second paragraph</p>
        </quote>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_quote(elem, context, self.traverser)

        assert result.count('<p>') == 2
        assert 'First paragraph' in result
        assert 'Second paragraph' in result

    def test_block_quote_with_inline_quote(self):
        """Test block quote containing inline quote."""
        doc = parse_tei('tests/fixtures/nested_quotes.xml')
        result = self.traverser.traverse_document(doc)

        # Block quote should contain paragraph with inline quote
        assert '<blockquote>' in result
        # Inline quote inside should use proper quote marks
        assert '\u201c' in result or '\u2018' in result

    def test_triple_nested_quotes(self):
        """Test deeply nested quotes maintain proper depth."""
        doc = parse_tei('tests/fixtures/nested_quotes.xml')
        result = self.traverser.traverse_document(doc)

        # Should contain both types of quotes due to nesting
        assert '\u201c' in result  # Double quotes
        assert '\u2018' in result  # Single quotes

    def test_list_rendering(self):
        """Test list rendering."""
        xml = '''<list xmlns="http://www.tei-c.org/ns/1.0">
            <item>First item</item>
            <item>Second item</item>
        </list>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_list(elem, context, self.traverser)

        assert '<ul>' in result
        assert '<li>First item</li>' in result
        assert '<li>Second item</li>' in result
        assert '</ul>' in result

    def test_table_rendering(self):
        """Test table rendering."""
        xml = '''<table xmlns="http://www.tei-c.org/ns/1.0">
            <row>
                <cell role="label">Header</cell>
                <cell role="label">Header 2</cell>
            </row>
            <row>
                <cell>Data 1</cell>
                <cell>Data 2</cell>
            </row>
        </table>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_table(elem, context, self.traverser)

        assert '<table>' in result
        assert '<th>Header</th>' in result
        assert '<th>Header 2</th>' in result
        assert '<td>Data 1</td>' in result
        assert '<td>Data 2</td>' in result

    def test_poetry_rendering(self):
        """Test poetry (lg) rendering."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0">
            <head>Poem Title</head>
            <l>First line</l>
            <l rend="indent">Indented line</l>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        assert '<div class="poem">' in result
        assert 'Poem Title' in result
        assert 'poem-title' in result
        assert '<div class="line">First line</div>' in result
        assert '<div class="line indent">Indented line</div>' in result

    def test_poetry_with_stanzas(self):
        """Test poetry with nested stanzas."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0" rend="center">
            <lg>
                <l>Stanza 1, line 1</l>
                <l>Stanza 1, line 2</l>
            </lg>
            <lg>
                <l>Stanza 2, line 1</l>
            </lg>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        assert '<div class="poem center">' in result
        assert result.count('<div class="stanza">') == 2
        assert 'Stanza 1, line 1' in result
        assert 'Stanza 2, line 1' in result

    def test_poetry_in_blockquote(self):
        """Test poetry inside blockquote (key recursion test)."""
        doc = parse_tei('tests/fixtures/poetry.xml')
        result = self.traverser.traverse_document(doc)

        # Should contain both blockquote and poem structures
        assert '<blockquote>' in result
        assert '<div class="poem">' in result
        assert 'Poetry inside a blockquote' in result

    def test_figure_rendering(self):
        """Test figure with image rendering."""
        xml = '''<figure xmlns="http://www.tei-c.org/ns/1.0" rend="center">
            <graphic url="images/test.jpg" width="50%"/>
            <head>Image Caption</head>
            <figDesc>Alt text description</figDesc>
        </figure>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_figure(elem, context, self.traverser)

        assert '<figure class="center" style="width: 50%;">' in result
        assert '<img src="images/test.jpg" alt="Alt text description">' in result
        assert '<figcaption>Image Caption</figcaption>' in result

    def test_milestone_rendering(self):
        """Test milestone (section break) rendering."""
        xml = '''<milestone xmlns="http://www.tei-c.org/ns/1.0" rend="stars"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_milestone(elem, context, self.traverser)

        assert '<div class="milestone stars"></div>' == result

    def test_inline_hi_italic(self):
        """Test inline <hi> with italic rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text with <hi rend="italic">italic</hi> word.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<i>italic</i>' in result

    def test_inline_hi_bold(self):
        """Test inline <hi> with bold rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text with <hi rend="bold">bold</hi> word.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<b>bold</b>' in result

    def test_inline_ref(self):
        """Test inline <ref> (link) rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">See <ref target="https://example.com">example</ref>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<a href="https://example.com">example</a>' in result

    def test_inline_ref_internal(self):
        """Test inline <ref> with internal link."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">See <ref target="ch1">Chapter 1</ref>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Should add # prefix for internal links
        assert '<a href="#ch1">Chapter 1</a>' in result

    def test_inline_note(self):
        """Test inline <note> rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text<note>footnote</note> continues.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<sup>[footnote]</sup>' in result

    def test_line_break(self):
        """Test line break rendering."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Line 1<lb/>Line 2</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<br>' in result
        assert 'Line 1' in result
        assert 'Line 2' in result

    def test_xhtml_mode(self):
        """Test XHTML mode uses self-closing tags."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Line<lb/>break</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<br/>' in result  # Self-closing tag in XHTML mode

    def test_context_preservation(self):
        """Test that context is properly preserved through recursion."""
        xml = '''<quote xmlns="http://www.tei-c.org/ns/1.0">
            <p>Outer <quote>inner</quote> text</p>
        </quote>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', quote_depth=0)

        result = self.renderer.render_quote(elem, context, self.traverser)

        # Block quote should contain paragraph
        assert '<blockquote>' in result
        assert '<p>' in result
        # Inline quote inside should use proper marks
        assert '\u201c' in result
        assert '\u201d' in result

    def test_smart_quotes_helper(self):
        """Test get_smart_quotes helper method."""
        # Even depth: double quotes
        open_q, close_q = self.renderer.get_smart_quotes(0)
        assert open_q == '\u201c'
        assert close_q == '\u201d'

        # Odd depth: single quotes
        open_q, close_q = self.renderer.get_smart_quotes(1)
        assert open_q == '\u2018'
        assert close_q == '\u2019'

        # Back to double quotes
        open_q, close_q = self.renderer.get_smart_quotes(2)
        assert open_q == '\u201c'
        assert close_q == '\u201d'
