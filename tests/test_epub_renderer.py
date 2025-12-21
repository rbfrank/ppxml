"""
Unit tests for EPUBRenderer.

Tests EPUB3-compliant XHTML rendering with cross-file references.
"""

import pytest
from lxml import etree

from writers.core.context import RenderContext
from writers.core.traverser import TEITraverser
from writers.renderers.epub_renderer import EPUBRenderer


class TestEPUBRenderer:
    """Test EPUBRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = EPUBRenderer()
        self.traverser = TEITraverser(self.renderer)

    def test_xhtml_mode_enabled(self):
        """Test that XHTML mode is enabled by default."""
        assert self.renderer.xhtml is True

    def test_line_break_xhtml(self):
        """Test line break renders as XHTML <br />."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Line 1<lb/>Line 2</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<br />' in result
        assert '<br>' not in result  # Should not use non-XHTML form

    def test_milestone_stars_xhtml(self):
        """Test milestone with stars uses XHTML self-closing div."""
        xml = '''<milestone xmlns="http://www.tei-c.org/ns/1.0" rend="stars"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_milestone(elem, context, self.traverser)

        assert '<div class="milestone stars"></div>' in result

    def test_milestone_space_xhtml(self):
        """Test milestone with space uses XHTML self-closing div."""
        xml = '''<milestone xmlns="http://www.tei-c.org/ns/1.0" rend="space"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_milestone(elem, context, self.traverser)

        assert '<div class="milestone space"></div>' in result

    def test_graphic_xhtml(self):
        """Test graphic renders as XHTML <img /> tag."""
        xml = '''<graphic xmlns="http://www.tei-c.org/ns/1.0" url="image.jpg"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='figure', xhtml=True)

        result = self.renderer.render_graphic(elem, context, self.traverser)

        assert '<img src="image.jpg" alt="" />' in result

    def test_ref_without_target(self):
        """Test ref without target renders as plain text."""
        xml = '''<ref xmlns="http://www.tei-c.org/ns/1.0">Chapter 1</ref>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='p', xhtml=True)

        result = self.renderer.render_ref(elem, context, self.traverser)

        assert result == 'Chapter 1'
        assert '<a' not in result

    def test_ref_with_hash_target(self):
        """Test ref with # target renders as same-file link."""
        xml = '''<ref xmlns="http://www.tei-c.org/ns/1.0" target="#ch1">Chapter 1</ref>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='p', xhtml=True)

        result = self.renderer.render_ref(elem, context, self.traverser)

        assert '<a href="#ch1">Chapter 1</a>' in result

    def test_ref_with_external_url(self):
        """Test ref with external URL renders as external link."""
        xml = '''<ref xmlns="http://www.tei-c.org/ns/1.0" target="https://example.com">Example</ref>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='p', xhtml=True)

        result = self.renderer.render_ref(elem, context, self.traverser)

        assert '<a href="https://example.com">Example</a>' in result

    def test_ref_with_id_map(self):
        """Test ref with id_map creates cross-file reference."""
        xml = '''<ref xmlns="http://www.tei-c.org/ns/1.0" target="ch1">Chapter 1</ref>'''
        elem = etree.fromstring(xml)
        id_map = {'ch1': 'chapter1.xhtml'}
        context = RenderContext(parent_tag='p', xhtml=True, id_map=id_map)

        result = self.renderer.render_ref(elem, context, self.traverser)

        assert '<a href="chapter1.xhtml#ch1">Chapter 1</a>' in result

    def test_ref_with_id_not_in_map(self):
        """Test ref with id not in map falls back to same-file reference."""
        xml = '''<ref xmlns="http://www.tei-c.org/ns/1.0" target="unknown">Unknown</ref>'''
        elem = etree.fromstring(xml)
        id_map = {'ch1': 'chapter1.xhtml'}
        context = RenderContext(parent_tag='p', xhtml=True, id_map=id_map)

        result = self.renderer.render_ref(elem, context, self.traverser)

        assert '<a href="#unknown">Unknown</a>' in result

    def test_render_chapter_basic(self):
        """Test rendering a basic chapter."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Chapter Title</head>
            <p>Chapter content.</p>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check XHTML structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert '<!DOCTYPE html>' in result
        assert '<html xmlns="http://www.w3.org/1999/xhtml"' in result
        assert 'xmlns:epub="http://www.idpf.org/2007/ops"' in result

        # Check title
        assert '<title>Chapter Title</title>' in result

        # Check heading
        assert '<h2>Chapter Title</h2>' in result

        # Check content
        assert 'Chapter content.' in result

        # Check closing tags
        assert '</body>' in result
        assert '</html>' in result

    def test_render_chapter_with_id(self):
        """Test rendering chapter with xml:id on div."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0" xml:id="ch1">
            <head>Chapter One</head>
            <p>Content.</p>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check heading has ID
        assert '<h2 id="ch1">Chapter One</h2>' in result

    def test_render_chapter_without_head(self):
        """Test rendering chapter without head element uses book title."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <p>Content without heading.</p>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check title fallback
        assert '<title>Book Title</title>' in result

        # Should not have h2 (no head element)
        assert '<h2>' not in result

    def test_render_chapter_with_nested_quotes(self):
        """Test chapter with nested blockquotes."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Test</head>
            <quote>
                <p>Outer quote</p>
                <quote>
                    <p>Inner quote</p>
                </quote>
            </quote>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check nested blockquotes
        assert '<blockquote>' in result
        assert 'Outer quote' in result
        assert 'Inner quote' in result

    def test_render_chapter_with_poetry(self):
        """Test chapter with poetry."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Poem Chapter</head>
            <lg>
                <head>Poem Title</head>
                <l>First line</l>
                <l>Second line</l>
            </lg>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check poetry structure
        assert '<div class="poem">' in result
        assert '<div class="poem-title">Poem Title</div>' in result
        assert 'First line' in result
        assert 'Second line' in result

    def test_render_chapter_with_cross_references(self):
        """Test chapter with cross-file references."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Chapter 2</head>
            <p>See <ref target="ch1">Chapter 1</ref> for details.</p>
        </div>'''
        elem = etree.fromstring(xml)
        id_map = {'ch1': 'chapter1.xhtml'}

        result = self.renderer.render_chapter(elem, 'Book Title', id_map=id_map)

        # Check cross-file reference
        assert '<a href="chapter1.xhtml#ch1">Chapter 1</a>' in result

    def test_html_escaping(self):
        """Test that special characters are properly escaped in XHTML."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text with &lt;special&gt; &amp; "characters".</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # lxml already handles entity escaping in the input XML
        # Our output should preserve proper escaping
        assert '&lt;' in result or '<special>' not in result
        assert '&amp;' in result or '& ' not in result

    def test_render_chapter_with_list(self):
        """Test chapter with list."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>List Chapter</head>
            <list>
                <item>First item</item>
                <item>Second item</item>
            </list>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check list structure
        assert '<ul>' in result
        assert '<li>First item</li>' in result
        assert '<li>Second item</li>' in result

    def test_render_chapter_with_table(self):
        """Test chapter with table."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Table Chapter</head>
            <table>
                <row>
                    <cell>A</cell>
                    <cell>B</cell>
                </row>
            </table>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check table structure
        assert '<table>' in result
        assert '<tr>' in result
        assert '<td>A</td>' in result
        assert '<td>B</td>' in result

    def test_render_chapter_with_figure(self):
        """Test chapter with figure."""
        xml = '''<div xmlns="http://www.tei-c.org/ns/1.0">
            <head>Figure Chapter</head>
            <figure>
                <graphic url="test.jpg"/>
                <head>Caption</head>
            </figure>
        </div>'''
        elem = etree.fromstring(xml)

        result = self.renderer.render_chapter(elem, 'Book Title')

        # Check figure structure
        assert '<figure>' in result
        assert '<img src="test.jpg" alt="" />' in result
        assert '<figcaption>Caption</figcaption>' in result

    def test_emphasis_in_paragraph(self):
        """Test emphasis rendering in XHTML."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text with <hi rend="italic">emphasis</hi>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '<span class="italic">emphasis</span>' in result

    def test_inline_quote_smart_quotes(self):
        """Test inline quotes use smart quotes in XHTML."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">He said <quote>hello</quote>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div', xhtml=True)

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Should use Unicode smart quotes
        assert '\u201c' in result  # Opening double quote
        assert '\u201d' in result  # Closing double quote
        assert 'hello' in result
