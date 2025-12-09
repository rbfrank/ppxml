# ppxml

Bookcove’s TEI converter (restricted subset)
converts TEI to text, HTML, LaTeX and EPUB3
implemented XML in `element-set.md`

## usage

```
prepare a directory for an example project.
These are already loaded if you download the zip from this repository:
  https://github.com/rbfrank/ppxml.git

example/firebrands.xml    <- source file for all formats
example/mystyles.css      <- CSS specific to firebrands HTML
example/images/*          <- images for the firebrand project

html_to_xml.py    <- (utility) convert HTML files to TEI XML format
inline_css.py     <- (utility) merge external CSS into generated HTML
ppxml.py          <- main Python program
writers/          <- writers directory for text, HTML, etc.
element-set.md    <- (optional) description of XML markup

manual build:

cd example  # change to the firebrands example directory

# generate the text file firebrands.txt
python3 ../ppxml.py firebrands.xml firebrands.txt

# generate the HTML
python3 ../ppxml.py firebrands.xml firebrands.html --css mystyles.css

# merge the external stylesheet into the HTML file (optional)
python3 ../inline_css.py mystyles.css firebrands.html

# convert an HTML file to TEI XML format (utility)
python3 ../html_to_xml.py source.html output.xml --title "Book Title"
```

## further documentation

For further documentation, visit https://bookcove.net

