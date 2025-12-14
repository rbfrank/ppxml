# ppxml

Bookcove's TEI converter (restricted subset)
converts TEI XML to text, HTML (EPUB3 and LaTeX in development)
implemented XML elements documented in `element-set.md`

## features

- Convert TEI XML to multiple formats (HTML, plain text)
- Support for CSS styling in HTML/EPUB output
- Restricted but practical TEI element set (see `element-set.md`)

## installation

No installation required. Clone or download this repository:

```bash
git clone https://github.com/rbfrank/ppxml.git
cd ppxml
```

Requires Python 3.6 or higher (with lxml library).

## usage

### file structure

The repository includes these files:

```
ppxml.py                  <- main Python program
writers/                  <- writers directory for text, HTML, etc.
element-set.md            <- description of supported TEI XML elements
```

It also includes an `examples/` directory:


- `firebrand/` a simple starting example with basic markup
- `emmylou/` a much more complicated example demonstrating markup for floated images, title page, a Table of Contents, poetry, and other more advanced constructions.
- `test/` a rudimentary test file containing most of the supported TEI/XML tags in `ppxml`

### converting TEI XML to other formats

```bash
cd example  # change to the firebrands example directory

# generate the text file firebrands.txt
python3 ../ppxml.py firebrands.xml firebrands.txt

# generate the HTML
# if there is an external stylesheet, it will be appended to the internal CSS
python3 ../ppxml.py firebrands.xml firebrands.html

```

## documentation

- `element-set.md` - Complete list of supported TEI XML elements
- https://bookcove.net - Additional documentation and resources

## supported output formats

- **HTML** - Web pages with optional CSS styling
- **Plain Text** - Formatted text with optional line width

## outpput formats in development

- **LaTeX** - For PDF generation (requires pdflatex)
- **EPUB3** - Electronic book format

