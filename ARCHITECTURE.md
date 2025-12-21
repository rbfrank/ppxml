# ppxml Architecture Documentation

## Overview

ppxml is a TEI (Text Encoding Initiative) to HTML/Text/EPUB converter built with a clean visitor pattern architecture. This document describes the design decisions, architecture, and implementation details of the rewritten system (December 2024).

## Design Philosophy

The core principle is **separation of concerns through the visitor pattern with immutable context**. This enables true recursion where nested elements properly inherit and modify context from their parents, solving the original problem where markup rendered differently at different nesting levels.

### Key Architectural Decisions

1. **Immutable Context Objects** - Replace parameter explosion with single context parameter
2. **Visitor Pattern** - Separate tree traversal from rendering logic
3. **Format-Agnostic Core** - Core traversal works for any output format
4. **Thin Wrappers** - Preserve backward-compatible API while using new implementation

## Architecture Layers

### Layer 1: Core Infrastructure (`writers/core/`)

The core layer provides format-agnostic tree traversal and context management.

#### `context.py` - RenderContext

Immutable dataclass that holds all rendering state:

```python
@dataclass(frozen=True)
class RenderContext:
    parent_tag: str = ''           # Parent element type
    quote_depth: int = 0           # Nesting level for quote marks
    block_depth: int = 0           # Block element nesting
    indent_level: int = 0          # Indentation level (text output)
    indent_string: str = '    '    # Indent unit (4 spaces)
    line_width: int = 72           # Text wrapping width
    xhtml: bool = False            # XHTML compliance mode
    id_map: Optional[Dict] = None  # Cross-file reference mapping
```

**Key Features:**
- Immutable (`frozen=True`) - prevents accidental state mutation
- Helper methods return new contexts: `with_parent()`, `with_deeper_quote()`, `with_indent()`
- Computed properties: `current_indent`, `is_inline_parent`

**Why This Matters:**
Before the rewrite, functions passed 5-7 individual parameters. Now they receive one context object. When recursing, create a modified copy:

```python
# Old way - parameter explosion
render_element(elem, parent='div', depth=2, indent=8, xhtml=True, id_map={...})

# New way - single context
child_context = context.with_deeper_quote()
render_element(elem, child_context, traverser)
```

#### `traverser.py` - TEITraverser

Generic tree walker that delegates rendering to format-specific renderers:

```python
class TEITraverser:
    def __init__(self, renderer: BaseRenderer):
        self.renderer = renderer

    def traverse_document(self, doc: etree._ElementTree) -> str:
        """Traverse complete TEI document."""
        # Get document structure (front, body, back)
        # Call renderer for each section
        # Assemble final output

    def traverse_element(self, elem: etree._Element,
                        context: RenderContext):
        """Traverse single element with context."""
        tag = strip_namespace(elem.tag)
        return self.renderer.render_element(elem, tag, context, self)
```

**Key Insight:**
The traverser knows *structure* (front/body/back, parent/child relationships) but not *formatting* (HTML tags vs plain text). It passes the traverser itself to renderers for recursive calls.

#### `base_renderer.py` - BaseRenderer

Abstract base class defining the renderer interface:

```python
class BaseRenderer(ABC):
    @abstractmethod
    def render_document_start(self, doc) -> Union[str, List[str]]:
        """Called before rendering body content."""

    @abstractmethod
    def render_document_end(self) -> Union[str, List[str]]:
        """Called after rendering body content."""

    @abstractmethod
    def render_element(self, elem, tag, context, traverser):
        """Render a single element - dispatch to specific handlers."""

    # Shared utilities
    def get_smart_quotes(self, depth: int) -> Tuple[str, str]:
        """Return opening/closing quotes based on nesting depth."""
        # depth 0 (even) = double quotes, depth 1 (odd) = single quotes

    def extract_plain_text(self, elem) -> str:
        """Extract all text content, ignoring markup."""

    def render_children(self, elem, context, traverser):
        """Recursively render all child elements."""
```

**Shared Utilities:**
- `get_smart_quotes()` - Alternating quote marks based on `context.quote_depth`
- `extract_plain_text()` - Text extraction without markup
- `render_children()` - Generic child traversal
- `strip_namespace()` - Remove TEI namespace from tags

### Layer 2: Format Renderers (`writers/renderers/`)

Each renderer extends `BaseRenderer` and implements format-specific output.

#### `html_renderer.py` - HTMLRenderer

Renders TEI to HTML with CSS classes. Supports both HTML5 and XHTML modes.

**Key Methods:**

```python
def render_element(self, elem, tag, context, traverser):
    """Dispatch to specific element handler."""
    if tag == 'div':
        return self.render_div(elem, context, traverser)
    elif tag == 'p':
        return self.render_paragraph(elem, context, traverser)
    # ... 33 element types total

def render_paragraph(self, elem, context, traverser):
    """Render paragraph with inline markup."""
    text = self.render_text_content(elem, context)
    elem_id = elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
    if elem_id:
        return f'<p id="{elem_id}">{text}</p>'
    return f'<p>{text}</p>'

def render_quote(self, elem, context, traverser):
    """Render quote - inline or block based on parent context."""
    if context.is_inline_parent:
        # Inline quote - handled in render_text_content
        return ''
    else:
        # Block quote
        child_context = context.with_deeper_block()
        children = self.render_children(elem, child_context, traverser)
        return '<blockquote>\n' + children + '\n</blockquote>'
```

**XHTML Mode:**
When `context.xhtml=True`:
- Self-closing tags: `<br/>` instead of `<br>`
- Escaped attributes: `html.escape()` on all attribute values
- Entity escaping: `html.escape()` on all text content

**Cross-File References:**
When `context.id_map` is provided (EPUB mode):
```python
if target in context.id_map:
    filename = context.id_map[target]
    href = f'{filename}#{target}'
```

#### `text_renderer.py` - TextRenderer

Renders TEI to plain text with wrapping and indentation.

**Key Innovation: True Narrowing**

Nested blockquotes reduce both left and right margins:

```python
def render_paragraph(self, elem, context, traverser):
    text = self._extract_text_with_emphasis(elem, context).strip()
    normalized = ' '.join(text.split())

    # Key: reduce total width based on indent level
    effective_width = self.line_width - (context.indent_level * 4)

    wrapped = textwrap.fill(
        normalized,
        width=effective_width,           # Reduced width
        initial_indent=context.current_indent,
        subsequent_indent=context.current_indent,
        break_long_words=False,
        break_on_hyphens=False
    )

    return wrapped.split('\n') + ['']
```

**Result:**
- Level 0: 72 chars total (0 indent, 72 text)
- Level 1: 72 chars total (4 indent, 68 text)
- Level 2: 72 chars total (8 indent, 64 text)

Both margins move inward, creating true narrowing effect.

**Text-Specific Features:**
- Emphasis marked with underscores: `_emphasized_`
- Smart quotes for inline quotes
- Poetry formatting with centered/indented lines
- Section breaks with centered asterisks

#### `epub_renderer.py` - EPUBRenderer

Extends `HTMLRenderer` for EPUB3-compliant XHTML.

```python
class EPUBRenderer(HTMLRenderer):
    def __init__(self, css_file=None):
        super().__init__(css_file=css_file)
        self.xhtml = True  # Force XHTML mode

    def render_chapter(self, div, book_title, id_map=None):
        """Render complete XHTML chapter document."""
        # Get chapter title from <head>
        head = div.find('tei:head', TEI_NS)
        chapter_title = self.extract_plain_text(head).strip()

        # Create context with id_map for cross-references
        context = RenderContext(
            parent_tag='body',
            xhtml=True,
            id_map=id_map or {}
        )

        # Generate XHTML document structure
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml" '
                  'xmlns:epub="http://www.idpf.org/2007/ops">',
            # ... render children ...
            '</html>'
        ]

        return '\n'.join(parts)
```

**Key Features:**
- Inherits all HTML rendering from parent
- XHTML mode enabled by default
- Provides `render_chapter()` for complete documents
- Supports cross-file references via `id_map`

### Layer 3: Compatibility Wrappers (`writers/`)

Thin wrappers that preserve the original API while using new renderers.

#### `to_html.py` (52 lines, was 457)

```python
def convert(tei_file, output_file, css_file=None):
    """Convert TEI XML to HTML."""
    doc = parse_tei(tei_file)
    renderer = HTMLRenderer(css_file=css_file)
    traverser = TEITraverser(renderer)
    html = traverser.traverse_document(doc)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
```

#### `to_text.py` (57 lines, was 352)

```python
def convert(tei_file, output_file, line_width=72):
    """Convert TEI XML to plain text with wrapping."""
    doc = parse_tei(tei_file)
    renderer = TextRenderer(line_width=line_width)
    traverser = TEITraverser(renderer)
    result = traverser.traverse_document(doc)
    # ... flatten and write ...
```

#### `to_epub.py` (360 lines, was 442)

```python
def convert(tei_file, output_file):
    """Convert TEI XML to EPUB3 format."""
    doc = parse_tei(tei_file)

    # Build ID mapping for cross-references
    id_map = build_id_mapping(doc)

    # Create renderer
    renderer = EPUBRenderer()

    # Process each chapter
    for div in body.findall('tei:div', TEI_NS):
        chapter_html = renderer.render_chapter(div, title, id_map)
        # ... write chapter file ...

    # ... package EPUB (mimetype, container.xml, content.opf, nav.xhtml) ...
```

## How Recursion Works

### Example: Nested Quotes with Alternating Marks

**Input XML:**
```xml
<quote>
  <p>Outer: <quote>Middle: <quote>Inner</quote></quote></p>
</quote>
```

**Execution Flow:**

1. **Outer blockquote** receives `context(quote_depth=0, parent_tag='div')`
   - Detects block context (parent is div)
   - Creates `child_context = context.with_deeper_block()`
   - Recursively renders `<p>` child with new context

2. **Paragraph** receives `context(quote_depth=0, parent_tag='quote')`
   - Processes inline content
   - When encountering first inline `<quote>`:
     - Creates `quote_context = context.with_deeper_quote()` → `quote_depth=1`
     - Calls `render_text_content(child, quote_context)`

3. **First inline quote** processes with `context(quote_depth=1)`
   - Calls `get_smart_quotes(1)` → returns `('\u2018', '\u2019')` (single quotes)
   - Renders: `'Middle: ...`
   - For nested `<quote>`, creates `quote_context.with_deeper_quote()` → `quote_depth=2`

4. **Second inline quote** processes with `context(quote_depth=2)`
   - Calls `get_smart_quotes(2)` → returns `('\u201c', '\u201d')` (double quotes)
   - Renders: `"Inner"`

**Result:**
```html
<blockquote>
  <p>Outer: 'Middle: "Inner"'</p>
</blockquote>
```

**Key Insight:** Each level receives the correct quote depth automatically through context propagation. No special cases needed!

## Testing Strategy

### Test Coverage by Layer

**Core Tests** (`tests/test_context.py`):
- Context immutability
- Helper methods (`with_parent`, `with_indent`, etc.)
- Computed properties

**Renderer Tests:**
- `test_html_renderer.py` - 25 tests, all element types
- `test_text_renderer.py` - 30+ tests, wrapping/indentation
- `test_epub_renderer.py` - 22 tests, XHTML compliance

**Integration Tests:**
- Complete document rendering
- Example book conversions
- Nested element combinations

### Test Design Principles

1. **Test Behavior, Not Implementation**
   - Test final output, not internal method calls
   - Accept variations (e.g., `<br/>` vs `<br />`)

2. **Test Recursion**
   - Nested quotes, blockquotes, lists
   - Quote depth alternation
   - Indentation levels

3. **Test Edge Cases**
   - Empty elements
   - Missing attributes
   - Deeply nested structures

## Key Design Patterns

### 1. Immutable State

**Problem:** Passing mutable state through recursion leads to bugs.

**Solution:** Frozen dataclass with helper methods returning new instances.

```python
# Wrong - mutates shared state
def render(elem, state):
    state.depth += 1
    for child in elem:
        render(child, state)  # All siblings see incremented depth!
    state.depth -= 1

# Right - creates new state
def render(elem, context):
    child_context = context.with_deeper_quote()
    for child in elem:
        render(child, child_context)  # Each child gets own context
```

### 2. Visitor Pattern

**Problem:** Tree traversal logic mixed with format-specific rendering.

**Solution:** Separate traverser (knows structure) from renderer (knows formatting).

```python
# Traverser knows structure
class TEITraverser:
    def traverse_element(self, elem, context):
        tag = strip_namespace(elem.tag)
        return self.renderer.render_element(elem, tag, context, self)

# Renderer knows formatting
class HTMLRenderer:
    def render_element(self, elem, tag, context, traverser):
        if tag == 'p':
            return self.render_paragraph(elem, context, traverser)
```

### 3. Context Propagation

**Problem:** Children need to know about parents (for nesting-dependent rendering).

**Solution:** Pass context down, modify for children, never look up.

```python
# Parent creates appropriate child context
def render_quote(elem, context, traverser):
    if context.is_inline_parent:
        # Parent is <p>, <item>, etc - inline rendering
        return ''
    else:
        # Parent is <div>, <quote>, etc - block rendering
        child_context = context.with_deeper_block()
        return render_children(elem, child_context, traverser)
```

## Performance Considerations

### Context Creation

Creating new context objects on every recursive call is fast because:
1. Dataclasses are lightweight
2. Most fields are simple types (int, str, bool)
3. Only `id_map` dict is shared (not copied)

### Text Wrapping

Using `textwrap.fill()` with both indent parameters AND reduced width:
- Efficient: single pass through text
- Correct: both margins handled properly
- Readable: parameters clearly express intent

## File Organization

```
ppxml/
├── writers/
│   ├── core/                    # Core infrastructure
│   │   ├── __init__.py
│   │   ├── context.py          # RenderContext dataclass
│   │   ├── traverser.py        # TEITraverser
│   │   └── base_renderer.py   # BaseRenderer abstract class
│   │
│   ├── renderers/              # Format-specific renderers
│   │   ├── __init__.py
│   │   ├── html_renderer.py   # HTML output
│   │   ├── text_renderer.py   # Plain text output
│   │   └── epub_renderer.py   # EPUB3 XHTML output
│   │
│   ├── to_html.py             # Backward-compatible wrapper (52 lines)
│   ├── to_text.py             # Backward-compatible wrapper (57 lines)
│   ├── to_epub.py             # Backward-compatible wrapper (360 lines)
│   ├── common.py              # Shared utilities (parse_tei, get_title)
│   └── epub_image_utils.py    # EPUB image handling
│
├── tests/
│   ├── test_context.py
│   ├── test_html_renderer.py
│   ├── test_text_renderer.py
│   ├── test_epub_renderer.py
│   └── fixtures/
│       ├── simple.xml
│       ├── nested_quotes.xml
│       └── poetry.xml
│
├── ppxml.py                   # CLI entry point (unchanged)
├── element-set.md            # TEI element documentation
└── ARCHITECTURE.md           # This file
```

## Code Metrics

### Before Rewrite
- `to_html.py`: 457 lines
- `to_text.py`: 352 lines
- `to_epub.py`: 442 lines
- **Total**: ~1,250 lines
- **Tests**: 0 unit tests
- **Recursion**: Broken (markup rendered differently at different nesting levels)

### After Rewrite
- Core layer: ~400 lines (context.py, traverser.py, base_renderer.py)
- Renderers: ~900 lines (html_renderer.py, text_renderer.py, epub_renderer.py)
- Wrappers: ~470 lines (to_html.py, to_text.py, to_epub.py)
- **Total**: ~1,770 lines
- **Tests**: 77 unit tests, all passing
- **Recursion**: Correct (context properly propagates through all nesting levels)

**Line count increased by ~40%, but:**
- Properly tested (0 → 77 tests)
- Properly architected (visitor pattern, immutable state)
- Properly recursive (context propagation)
- More maintainable (separation of concerns)

## Future Considerations

### Adding New Output Formats

To add a new format (e.g., Markdown):

1. Create `writers/renderers/markdown_renderer.py`
2. Extend `BaseRenderer`
3. Implement required methods
4. Create thin wrapper `writers/to_markdown.py`
5. Add tests `tests/test_markdown_renderer.py`

**Core layer unchanged!** Traversal logic is format-agnostic.

### Adding New TEI Elements

To support new TEI element type:

1. Add `render_<element>()` method to each renderer
2. Add dispatch case in `render_element()`
3. Add tests for new element
4. Document in `element-set.md`

### Performance Optimization

If needed:
- Cache `extract_plain_text()` results
- Profile `textwrap.fill()` calls
- Consider streaming output for large documents

Current performance is adequate for typical book-length documents (~300KB TEI → ~1s conversion).

## Common Pitfalls and Solutions

### Pitfall 1: Forgetting to Pass Traverser

**Wrong:**
```python
def render_quote(self, elem, context, traverser):
    for child in elem:
        result = self.render_element(child, ...)  # No way to recurse!
```

**Right:**
```python
def render_quote(self, elem, context, traverser):
    for child in elem:
        result = traverser.traverse_element(child, child_context)
```

### Pitfall 2: Setting Parent Tag Incorrectly

**Wrong:**
```python
def render_children(self, elem, context, traverser):
    for child in elem:
        child_tag = strip_namespace(child.tag)
        child_context = context.with_parent(child_tag)  # Sets child as parent!
        result = traverser.traverse_element(child, child_context)
```

**Right:**
```python
def render_children(self, elem, context, traverser):
    for child in elem:
        # Pass context unchanged - child will see current element as parent
        result = traverser.traverse_element(child, context)
```

### Pitfall 3: Lowercase vs Uppercase in XML Namespace

**Wrong:**
```python
elem.get('{http://www.w3.org/xml/1998/namespace}id', '')  # lowercase 'xml'
```

**Right:**
```python
elem.get('{http://www.w3.org/XML/1998/namespace}id', '')  # uppercase 'XML'
```

The official XML namespace uses uppercase.

## Conclusion

The ppxml rewrite demonstrates that **good architecture pays off**:

- **Before**: Broken recursion, no tests, 1,250 lines of tangled code
- **After**: Correct recursion, 77 tests, 1,770 lines of clean architecture

The visitor pattern with immutable context enables true recursion where nested elements properly inherit and modify context from parents. This solves the original problem and creates a maintainable foundation for future development.

**Core Principle:** Separate what changes (rendering logic) from what stays the same (traversal logic), and make all state explicit through immutable context objects.
