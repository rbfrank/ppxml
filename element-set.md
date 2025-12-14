# TEI Element Set for bookcove.net
# version 1.0 as of 2025-12-04

## Core Required Elements (TEI Minimal)

### Document Structure
- `<TEI>` - Root element for TEI document
- `<teiHeader>` - Container for metadata
- `<fileDesc>` - File description (bibliographic information)
- `<titleStmt>` - Title statement
- `<title>` - Title of the work
- `<publicationStmt>` - Publication statement
- `<sourceDesc>` - Source description
- `<text>` - Container for the text itself
- `<body>` - Main body of text

### Basic Text Structure
- `<p>` - Paragraph
  - Use `@rend` attribute for styling: `rend="no-indent"`, or any custom CSS class

## Additional Structural Elements

### Document Divisions
- `<div>` - Text division (chapters, sections, parts)
  - Use `@type` attribute: `type="chapter"`, `type="section"`, etc.
  - Use `@xml:id` attribute for linking: `xml:id="ch1"` (creates anchor point for table of contents)
- `<head>` - Heading for divisions
- `<front>` - Front matter (preface, introduction, etc.)
- `<back>` - Back matter (appendices, notes, etc.)

### Poetry/Verse
- `<lg>` - Line group (stanza, verse paragraph)
  - Use `@rend="center"` to center the entire poem
- `<l>` - Line of verse
  - Use `@rend` attribute for indentation: `rend="indent"`, `rend="indent2"`, or `rend="indent3"`
  - Use `@rend="center"` to center a single line

### Lists
- `<list>` - List container
- `<item>` - List item
- `<label>` - Label for list item

### Tables
- `<table>` - Table container
- `<row>` - Table row
- `<cell>` - Table cell
  - Use `@role="label"` for header cells

## Inline Elements

### Emphasis and Highlighting
- `<hi>` - Highlighted text (general purpose)
  - Use `@rend` attribute: `rend="italic"`, `rend="bold"`, `rend="underline"`, `rend="small-caps"`, etc.
- `<emph>` - Semantic emphasis (optional alternative to `<hi>`)

### Quotations and References
- `<quote>` - Quotation (inline or block)
- `<ref>` - Reference or link
  - Use `@target` for URLs: `<ref target="https://example.com">link text</ref>`
  - Use `@target` with `#` for internal links: `<ref target="#ch1">Chapter 1</ref>`
- `<note>` - Note or annotation

### Special Text
- `<foreign>` - Foreign language text (optional)
- `<title>` - Title of a work mentioned in text

### Breaks
- `<lb>` - Line break
- `<pb>` - Page break
  - Use `@n` attribute for page numbers: `<pb n="42"/>`
- `<milestone>` - Section break or thought break
  - Use `@rend="stars"` for asterisk separator: `<milestone rend="stars"/>`
  - Use `@rend="space"` for blank space separator: `<milestone rend="space"/>`

### Figures/Illustrations
- `<figure>` - Container for illustrations
  - Use `@rend` attribute for positioning: `rend="left"`, `rend="right"`, or `rend="center"`
- `<graphic>` - Image reference
  - Use `@url` attribute: `<graphic url="images/picture.jpg"/>`
  - Use `@width` attribute for sizing: `<graphic url="..." width="50%"/>` or `<graphic url="..." width="300px"/>`
- `<figDesc>` - Figure description (for alt text/accessibility)
- `<head>` - Caption for the figure (when used within `<figure>`)

## Total Count
Approximately 33 elements - enough for most literary texts without overwhelming users.

## Common Attributes
- `@type` - Specify types for various elements
- `@rend` - Rendering/display information
- `@n` - Numbering
- `@role` - Role specification (especially for table cells)

## Example Usage

```xml
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Pride and Prejudice</title>
      </titleStmt>
      <publicationStmt>
        <p>Published by bookcove.net</p>
      </publicationStmt>
      <sourceDesc>
        <p>Transcribed from 1813 edition</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <front>
      <div type="preface">
        <head>Preface</head>
        <p>This is the preface...</p>
      </div>
    </front>
    <body>
      <div type="chapter" n="1">
        <head>Chapter I</head>
        <p>It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.</p>
        
        <figure>
          <graphic url="images/estate.jpg"/>
          <head>Netherfield Park</head>
          <figDesc>A grand English estate with manicured gardens</figDesc>
        </figure>
        
        <p>However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the <hi rend="italic">rightful property</hi> of some one or other of their daughters.</p>
        
        <milestone rend="stars"/>
        
        <p>The next morning brought a new development.</p>
      </div>
    </body>
  </text>
</TEI>
```

## Notes
- This set balances simplicity with functionality for typical literary texts
- Can be extended if needed for specific text types
- AI assistance can help users apply these elements correctly
- All elements are valid TEI and will work with TEI processing tools

