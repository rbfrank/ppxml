# ppxml

Bookcove's TEI converter (restricted subset)
converts TEI XML to text, HTML, and EPUB3.

## features

- Convert TEI XML to multiple formats (HTML, plain text, EPUB3)
- Support for CSS styling in HTML/EPUB output
- Restricted but practical TEI element set (see `element-set.md`)

## installation

Clone or download this repository:

```bash
git clone https://github.com/rbfrank/ppxml.git
cd ppxml
```

### setup virtual environment (recommended)

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Requires Python 3.6 or higher.

## usage

### file structure

The repository includes these files:

```
ppxml.py       <- main Python program
writers/       <- writers directory for text, HTML, etc.
element-set.md <- supported TEI XML elements
```

It also includes an `examples/` directory:

- `firebrand/` a simple starting example with basic markup
- `emmylou/` a much more complicated example demonstrating markup for floated images, title page, a Table of Contents, poetry, and other more advanced constructions.
- `test/` a rudimentary test file containing most of the supported TEI/XML tags in `ppxml`

### converting TEI XML to other formats

After setting up the virtual environment, here is a sample sequence to generate the text and HTML for the book "Emmy Lou, Her Book and Heart":

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Generate outputs
cd examples/emmylou
python ../../ppxml.py emmylou.xml emmylou.txt
python ../../ppxml.py emmylou.xml emmylou.html
python ../../ppxml.py emmylou.xml emmylou.epub
```

That will generate `emmylou.txt`, `emmylou.html`, and `emmylou.epub` in the `examples/emmylou/` directory.

Note: Python must include the lxml libraries to run `ppxml.py`.

Note: If you don't have `git` installed, visit `https://github.com/rbfrank/ppxml`, click on
the white down arrow in the gree "Code" button, and download the zip file. Unzip that instead
of cloning the repository.

## documentation

- `element-set.md` - Complete list of supported TEI XML elements
- https://bookcove.net - Additional documentation and resources

## CSS styling

ppxml supports custom CSS for both HTML and EPUB outputs using a directory-based structure.

### format-specific CSS directories

Create separate CSS files for HTML and EPUB formats in your project directory:

```
project/
├── book.xml
└── css/
    ├── html/
    │   └── custom.css    # HTML-specific styles
    └── epub/
        └── custom.css    # EPUB-specific styles
```

### multiple CSS files

You can use multiple CSS files in each directory. They will be concatenated in **alphabetical order**:

```
project/
└── css/
    ├── html/
    │   ├── 01-base.css
    │   ├── 02-layout.css
    │   └── 03-theme.css
    └── epub/
        └── styles.css
```

### CSS behavior

- **HTML**: Custom CSS is appended to default styles and embedded in the HTML output
- **EPUB**: Custom CSS is appended to default styles in the EPUB's `styles.css` file
- **Discovery**: CSS files must be in `css/html/` or `css/epub/` directories relative to your XML file
- **Cascading**: Custom CSS rules override default styles due to CSS cascade order

### examples

Both example projects (`emmylou/` and `firebrand/`) include CSS files in the new directory structure that demonstrate custom styling.

## supported output formats

- **HTML** - Web pages with optional CSS styling
- **Plain Text** - Formatted text with optional line width
- **EPUB3** - Electronic book format with XHTML chapters

