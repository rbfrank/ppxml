"""
Unit tests for TextRenderer.

Tests plain text rendering with wrapping, indentation, and emphasis.
"""

import pytest
from lxml import etree

from writers.core.context import RenderContext
from writers.core.traverser import TEITraverser
from writers.renderers.text_renderer import TextRenderer
from writers.common import parse_tei


class TestTextRenderer:
    """Test TextRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = TextRenderer(line_width=72)
        self.traverser = TEITraverser(self.renderer)

    def test_simple_paragraph(self):
        """Test rendering a simple paragraph."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Simple text paragraph.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert isinstance(result, list)
        assert len(result) == 2  # Text + blank line
        assert result[0] == 'Simple text paragraph.'
        assert result[1] == ''

    def test_paragraph_wrapping(self):
        """Test that long paragraphs wrap correctly."""
        long_text = ' '.join(['word'] * 30)  # Very long paragraph
        xml = f'''<p xmlns="http://www.tei-c.org/ns/1.0">{long_text}</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Should be wrapped into multiple lines
        assert len(result) > 2
        # Each line should be <= 72 chars
        for line in result[:-1]:  # Exclude blank line
            assert len(line) <= 72

    def test_paragraph_with_emphasis(self):
        """Test paragraph with emphasis markup."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text with <hi rend="italic">emphasis</hi> here.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert 'Text with _emphasis_ here.' in result[0]

    def test_inline_quote(self):
        """Test inline quote uses smart quotes."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">He said <quote>hello</quote>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        # Should use double quotes (U+201C and U+201D)
        assert '\u201c' in result[0]
        assert '\u201d' in result[0]
        assert 'hello' in result[0]

    def test_nested_inline_quotes(self):
        """Test nested inline quotes alternate quote marks."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">A <quote>B <quote>C</quote> D</quote> E</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        text = result[0]
        # Should have both double and single quotes
        assert '\u201c' in text  # Opening double quote
        assert '\u201d' in text  # Closing double quote
        assert '\u2018' in text  # Opening single quote
        assert '\u2019' in text  # Closing single quote

    def test_block_quote_indentation(self):
        """Test block quote is indented."""
        xml = '''<quote xmlns="http://www.tei-c.org/ns/1.0">
            <p>Quoted paragraph.</p>
        </quote>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_quote(elem, context, self.traverser)

        # Should be indented (4 spaces)
        assert result[0].startswith('    ')
        assert 'Quoted paragraph.' in result[0]

    def test_nested_block_quotes(self):
        """Test nested block quotes have deeper indentation."""
        xml = '''<quote xmlns="http://www.tei-c.org/ns/1.0">
            <quote>
                <p>Nested quote.</p>
            </quote>
        </quote>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_quote(elem, context, self.traverser)

        # Should be double-indented (8 spaces)
        has_double_indent = any(line.startswith('        ') for line in result if line.strip())
        assert has_double_indent

    def test_list_rendering(self):
        """Test list with bullet points."""
        xml = '''<list xmlns="http://www.tei-c.org/ns/1.0">
            <item>First item</item>
            <item>Second item</item>
        </list>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_list(elem, context, self.traverser)

        assert len(result) >= 3  # 2 items + blank
        assert '•' in result[0]
        assert 'First item' in result[0]
        assert '•' in result[1]
        assert 'Second item' in result[1]

    def test_table_rendering(self):
        """Test table rendering."""
        xml = '''<table xmlns="http://www.tei-c.org/ns/1.0">
            <row>
                <cell>A</cell>
                <cell>B</cell>
            </row>
            <row>
                <cell>C</cell>
                <cell>D</cell>
            </row>
        </table>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_table(elem, context, self.traverser)

        # Should have 2 rows + blank
        assert len(result) == 3
        assert 'A' in result[0]
        assert 'B' in result[0]
        assert 'C' in result[1]
        assert 'D' in result[1]

    def test_simple_poem(self):
        """Test simple poetry rendering."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0">
            <l>First line</l>
            <l>Second line</l>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        # Lines should be indented (4 spaces base indent)
        assert any('First line' in line for line in result)
        assert any('Second line' in line for line in result)
        # Should have indentation
        has_indent = any(line.startswith('    ') and line.strip() for line in result)
        assert has_indent

    def test_poem_with_title(self):
        """Test poem with title."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0">
            <head>Poem Title</head>
            <l>First line</l>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        # Title should be uppercase
        assert any('POEM TITLE' in line for line in result)

    def test_centered_poem(self):
        """Test centered poem rendering."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0" rend="center">
            <head>Title</head>
            <l>Short</l>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        # Title should be centered
        title_line = [l for l in result if 'TITLE' in l][0]
        assert title_line.startswith(' ')  # Has leading spaces for centering

    def test_indented_verse_line(self):
        """Test verse line with indent attribute."""
        xml = '''<lg xmlns="http://www.tei-c.org/ns/1.0">
            <l>Normal line</l>
            <l rend="indent">Indented line</l>
        </lg>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_line_group(elem, context, self.traverser)

        # Find the lines
        normal_line = [l for l in result if 'Normal line' in l][0]
        indented_line = [l for l in result if 'Indented line' in l][0]

        # Indented line should have more leading spaces
        normal_spaces = len(normal_line) - len(normal_line.lstrip())
        indented_spaces = len(indented_line) - len(indented_line.lstrip())
        assert indented_spaces > normal_spaces

    def test_figure_rendering(self):
        """Test figure rendering as caption text."""
        xml = '''<figure xmlns="http://www.tei-c.org/ns/1.0">
            <graphic url="image.jpg"/>
            <head>Image Caption</head>
        </figure>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_figure(elem, context, self.traverser)

        assert len(result) == 2  # Caption + blank
        assert '[Illustration: Image Caption]' in result[0]

    def test_milestone_stars(self):
        """Test milestone with stars rendering."""
        xml = '''<milestone xmlns="http://www.tei-c.org/ns/1.0" rend="stars"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_milestone(elem, context, self.traverser)

        assert len(result) == 2  # Stars + blank
        assert '*' in result[0]

    def test_milestone_space(self):
        """Test milestone with space rendering."""
        xml = '''<milestone xmlns="http://www.tei-c.org/ns/1.0" rend="space"/>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_milestone(elem, context, self.traverser)

        # Should be blank lines
        assert all(line == '' for line in result)

    def test_line_break(self):
        """Test line break in text."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Line 1<lb/>Line 2</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        text = result[0]
        assert 'Line 1' in text
        assert 'Line 2' in text

    def test_note_formatting(self):
        """Test note rendering in brackets."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">Text<note>footnote</note> continues.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '[footnote]' in result[0]

    def test_reference_text(self):
        """Test ref renders as plain text."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">See <ref target="ch1">Chapter 1</ref>.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert 'See Chapter 1.' in result[0]
        # Should not include target URL

    def test_foreign_text(self):
        """Test foreign text marked with underscores."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">The word <foreign>et cetera</foreign> is Latin.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '_et cetera_' in result[0]

    def test_title_markup(self):
        """Test title marked with underscores."""
        xml = '''<p xmlns="http://www.tei-c.org/ns/1.0">I read <title>Moby Dick</title> yesterday.</p>'''
        elem = etree.fromstring(xml)
        context = RenderContext(parent_tag='div')

        result = self.renderer.render_paragraph(elem, context, self.traverser)

        assert '_Moby Dick_' in result[0]

    def test_visual_length_helper(self):
        """Test visual length calculation excludes emphasis markers."""
        text_with_markers = 'Hello _world_ test'
        visual_len = self.renderer._visual_length(text_with_markers)

        # Should count: "Hello world test" = 16 chars
        assert visual_len == 16

    def test_complete_document(self):
        """Test rendering complete document from fixture."""
        doc = parse_tei('tests/fixtures/simple.xml')
        result = self.traverser.traverse_document(doc)

        # Result should be a list of lines or a string
        if isinstance(result, str):
            lines = result.split('\n')
        else:
            lines = result

        # Should contain chapter heading (uppercase)
        has_heading = any('TEST CHAPTER' in str(line) for line in lines)
        assert has_heading

        # Should contain paragraph text
        has_paragraph = any('simple paragraph' in str(line).lower() for line in lines)
        assert has_paragraph

    def test_poetry_in_blockquote(self):
        """Test poetry inside blockquote (recursion test)."""
        doc = parse_tei('tests/fixtures/poetry.xml')
        result = self.traverser.traverse_document(doc)

        if isinstance(result, str):
            lines = result.split('\n')
        else:
            lines = result

        # Should contain the poetry text with proper indentation
        has_poetry = any('Poetry inside a blockquote' in str(line) for line in lines)
        assert has_poetry

        # Check that it's indented (blockquote indent)
        poetry_lines = [str(l) for l in lines if 'Poetry inside a blockquote' in str(l)]
        if poetry_lines:
            # Should have leading whitespace from blockquote indentation
            assert poetry_lines[0].startswith(' ')

    def test_context_indentation(self):
        """Test that context properly tracks indentation."""
        ctx = RenderContext(indent_level=0)
        assert ctx.current_indent == ''

        ctx = ctx.with_indent(1)
        assert ctx.current_indent == '    '  # 4 spaces

        ctx = ctx.with_indent(1)
        assert ctx.current_indent == '        '  # 8 spaces
