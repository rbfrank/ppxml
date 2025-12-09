# ppxml

Bookcove's TEI converter (restricted subset)
converts TEI XML to text, HTML, LaTeX and EPUB3
implemented XML elements documented in `element-set.md`

## features

- Convert TEI XML to multiple formats (HTML, plain text, LaTeX, EPUB3)
- Import HTML files and convert to TEI XML format
- Support for CSS styling in HTML/EPUB output
- Inline CSS utility for self-contained HTML files
- Restricted but practical TEI element set (see `element-set.md`)

## installation

No installation required. Clone or download this repository:

```bash
git clone https://github.com/rbfrank/ppxml.git
cd ppxml
```

Requires Python 3.6 or higher (no external dependencies).

## usage

### file structure

The repository includes these files:

```
example/firebrands.xml    <- source file for all formats
example/mystyles.css      <- CSS specific to firebrands HTML
example/images/*          <- images for the firebrand project

html_to_xml.py         <- (utility) convert HTML files to TEI XML format
inline_css.py          <- (utility) merge external CSS into generated HTML
ppxml.py               <- main Python program
writers/               <- writers directory for text, HTML, etc.
element-set.md         <- description of supported TEI XML elements
HTML_TO_TEI_MAPPING.md <- reference for HTML to TEI conversion
```

### converting TEI XML to other formats

```bash
cd example  # change to the firebrands example directory

# generate the text file firebrands.txt
python3 ../ppxml.py firebrands.xml firebrands.txt

# generate the HTML
python3 ../ppxml.py firebrands.xml firebrands.html --css mystyles.css

# merge the external stylesheet into the HTML file (optional)
python3 ../inline_css.py mystyles.css firebrands.html
```

### converting HTML to TEI XML

Import HTML files and convert them to TEI XML format:

```bash
# basic conversion (title extracted from HTML)
python3 html_to_xml.py input.html output.xml

# with explicit title and author
python3 html_to_xml.py input.html output.xml --title "Book Title" --author "Author Name"

# then use ppxml to convert to other formats
python3 ppxml.py output.xml output.html --css styles.css
```

See `HTML_TO_TEI_MAPPING.md` for details on how HTML elements are mapped to TEI.

**Note**: HTML to TEI conversion is best-effort. Manual review and editing of the output is recommended.

## documentation

- `element-set.md` - Complete list of supported TEI XML elements
- `HTML_TO_TEI_MAPPING.md` - HTML to TEI conversion reference
- https://bookcove.net - Additional documentation and resources

## supported output formats

- **HTML** - Web pages with optional CSS styling
- **Plain Text** - Formatted text with optional line width
- **LaTeX** - For PDF generation (requires pdflatex)
- **EPUB3** - Electronic book format

## license

See `LICENSE` file for details.

