# HTML to TEI XML Conversion Reference

This document describes how `html_to_xml.py` maps HTML elements to TEI XML elements.

## Document Structure

| HTML | TEI | Notes |
|------|-----|-------|
| `<html>`, `<body>` | `<TEI>`, `<text>`, `<body>` | Standard TEI structure created |
| `<title>` (in head) | `<title>` (in teiHeader) | Extracted automatically |
| `<h1>`, `<h2>` | `<div type="chapter">` + `<head>` | Major divisions |
| `<h3>`, `<h4>`, `<h5>`, `<h6>` | `<div type="section">` + `<head>` | Subsections |

## Text Structure

| HTML | TEI | Notes |
|------|-----|-------|
| `<p>` | `<p>` | Paragraph |
| `<br>` | `<lb/>` | Line break |
| `<hr>` | `<milestone rend="stars"/>` | Section break |
| `<div>` | `<div type="section">` | Generic division |

## Lists

| HTML | TEI | Notes |
|------|-----|-------|
| `<ul>`, `<ol>` | `<list>` | Both ordered and unordered |
| `<li>` | `<item>` | List item |

## Tables

| HTML | TEI | Notes |
|------|-----|-------|
| `<table>` | `<table>` | Table container |
| `<tr>` | `<row>` | Table row |
| `<td>` | `<cell>` | Table cell |
| `<th>` | `<cell role="label">` | Header cell |

## Inline Formatting

| HTML | TEI | Notes |
|------|-----|-------|
| `<em>`, `<i>` | `<hi rend="italic">` | Italic/emphasis |
| `<strong>`, `<b>` | `<hi rend="bold">` | Bold |
| `<u>` | `<hi rend="underline">` | Underline |
| `<code>` | `<hi rend="monospace">` | Code/monospace |

## Quotations and References

| HTML | TEI | Notes |
|------|-----|-------|
| `<blockquote>` | `<quote rend="block">` | Block quotation |
| `<q>` | `<quote>` | Inline quotation |
| `<a href="...">` | `<ref target="...">` | Link/reference |

## Images and Figures

| HTML | TEI | Notes |
|------|-----|-------|
| `<img src="..." alt="...">` | `<figure>` + `<graphic url="..."/>` + `<figDesc>` | Image with description |
| `<figure>` | `<figure>` | Figure container |
| `<figcaption>` | `<head>` | Figure caption |

## Elements Not Converted

The following HTML elements are ignored or skipped:
- `<script>` - JavaScript code (content skipped)
- `<style>` - CSS styles (content skipped)
- `<nav>`, `<header>`, `<footer>` - Treated as generic divs
- `<span>` - Ignored (only content preserved)
- Form elements (`<form>`, `<input>`, etc.) - Not applicable to TEI

## Limitations and Recommendations

1. **Manual Review Required**: The conversion is best-effort. Always review and edit the output.

2. **Heading Hierarchy**: HTML headings are converted to chapters (h1-h2) and sections (h3+). You may need to adjust the `type` attributes.

3. **CSS Classes**: HTML class attributes are partially used to infer `div` types. Consider reviewing div structures.

4. **Nested Structures**: Complex nested HTML may require manual cleanup.

5. **Semantic Meaning**: HTML's presentational elements are mapped to TEI's semantic elements. Consider if the conversion preserves intended meaning.

## Example Usage

```bash
# Basic conversion
python3 html_to_xml.py book.html book.xml

# With title and author
python3 html_to_xml.py book.html book.xml --title "My Book" --author "Jane Doe"

# Then use with ppxml
python3 ppxml.py book.xml book_output.html --css styles.css
```

## Post-Conversion Checklist

After converting HTML to TEI XML, review:

- [ ] Document title and author are correct
- [ ] Chapter/section divisions make sense
- [ ] Images have correct paths and descriptions
- [ ] Lists and tables are properly structured
- [ ] Emphasis and formatting preserved correctly
- [ ] Links and references are valid
- [ ] Special characters are properly escaped
- [ ] Any custom HTML structures are appropriately represented
