"""
to_latex.py - Convert TEI to LaTeX and optionally compile to PDF
"""

import subprocess
import os
import shutil
from .common import TEI_NS, parse_tei, get_metadata

def convert(tei_file, output_file, compile_pdf=True):
    """
    Convert TEI XML to LaTeX, and optionally compile to PDF.
    
    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to output file (.tex or .pdf)
        compile_pdf: Whether to compile LaTeX to PDF (default True)
    """
    doc = parse_tei(tei_file)
    metadata = get_metadata(doc)
    
    # Generate LaTeX content
    latex_parts = []
    
    # Document preamble
    latex_parts.append(get_preamble(metadata))
    
    # Begin document
    latex_parts.append(r'\begin{document}')
    latex_parts.append('')
    
    # Title page
    latex_parts.append(r'\maketitle')
    latex_parts.append(r'\cleardoublepage')
    latex_parts.append('')
    
    # Process front matter
    front = doc.find('.//tei:front', TEI_NS)
    if front is not None:
        for div in front.findall('.//tei:div', TEI_NS):
            latex_parts.append(process_div(div))
            latex_parts.append('')
    
    # Process body
    body = doc.find('.//tei:body', TEI_NS)
    if body is not None:
        for div in body.findall('.//tei:div', TEI_NS):
            latex_parts.append(process_div(div))
            latex_parts.append('')
    
    # Process back matter
    back = doc.find('.//tei:back', TEI_NS)
    if back is not None:
        for div in back.findall('.//tei:div', TEI_NS):
            latex_parts.append(process_div(div))
            latex_parts.append('')
    
    latex_parts.append(r'\end{document}')
    
    # Determine output paths
    if output_file.endswith('.pdf'):
        tex_file = output_file.replace('.pdf', '.tex')
        pdf_requested = True
    else:
        tex_file = output_file
        pdf_requested = False
    
    # Write LaTeX file
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_parts))
    
    print(f"LaTeX file created: {tex_file}")
    
    # Compile to PDF if requested
    if compile_pdf and pdf_requested:
        compile_latex_to_pdf(tex_file, output_file)

def get_preamble(metadata):
    """Generate LaTeX preamble."""
    title = latex_escape(metadata['title'])
    
    return f'''\\documentclass[12pt,letterpaper]{{book}}

% Packages
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{caption}}
\\usepackage{{longtable}}
\\usepackage{{hyperref}}

% Setup
\\title{{{title}}}
\\author{{}}
\\date{{}}

% Custom commands for poetry
\\newcommand{{\\poemtitle}}[1]{{\\textbf{{#1}}}}
\\newenvironment{{poem}}{{\\begin{{flushleft}}\\obeylines}}{{\\end{{flushleft}}}}
\\setlength{{\\parindent}}{{1.5em}}
\\setlength{{\\parskip}}{{0pt}}
'''

def process_div(div):
    """Process a TEI div element."""
    parts = []
    
    # Get heading
    head = div.find('tei:head', TEI_NS)
    if head is not None:
        title = latex_escape(''.join(head.itertext()).strip())
        if title:
            parts.append(f'\\chapter{{{title}}}')
            parts.append('')
    
    # Process all child elements
    for elem in div:
        if not isinstance(elem.tag, str):
            continue
        elem_tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        if elem_tag != 'head':  # Skip head, already processed
            parts.append(process_element(elem))
    
    return '\n'.join(parts)

def process_element(elem):
    """Process a TEI element and return LaTeX string."""
    tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
    
    if tag == 'p':
        text = process_text_content(elem)
        return f'{text}\n'
    
    elif tag == 'quote':
        # Check if it's a block quote
        parent_tag = elem.getparent().tag.replace(f"{{{TEI_NS['tei']}}}", '')
        text = process_text_content(elem)
        if parent_tag == 'p':
            # Inline quote
            return f'``{text}\'\''
        else:
            # Block quote
            return f'\\begin{{quote}}\n{text}\n\\end{{quote}}\n'
    
    elif tag == 'list':
        items = []
        for item in elem.findall('tei:item', TEI_NS):
            items.append(f'  \\item {process_text_content(item)}')
        return '\\begin{itemize}\n' + '\n'.join(items) + '\n\\end{itemize}\n'
    
    elif tag == 'table':
        return process_table(elem)
    
    elif tag == 'figure':
        return process_figure(elem)
    
    elif tag == 'lg':
        return process_poem(elem)
    
    elif tag == 'div':
        # Nested div
        parts = []
        for child in elem:
            parts.append(process_element(child))
        return '\n'.join(parts)
    
    elif tag == 'milestone':
        # Section/thought break
        rend = elem.get('rend', 'space')
        if rend == 'stars':
            return '\\begin{center}\n*\\hspace{2em}*\\hspace{2em}*\\hspace{2em}*\\hspace{2em}*\n\\end{center}\n'
        else:
            return '\\vspace{2em}\n'
    
    else:
        return ''

def process_table(elem):
    """Process a table element."""
    rows = elem.findall('tei:row', TEI_NS)
    if not rows:
        return ''
    
    # Determine number of columns from first row
    first_row = rows[0]
    num_cols = len(first_row.findall('tei:cell', TEI_NS))
    col_spec = '|' + 'l|' * num_cols
    
    parts = [f'\\begin{{longtable}}{{{col_spec}}}']
    parts.append('\\hline')
    
    for row in rows:
        cells = []
        for cell in row.findall('tei:cell', TEI_NS):
            cells.append(process_text_content(cell))
        parts.append(' & '.join(cells) + r' \\')
        parts.append('\\hline')
    
    parts.append('\\end{longtable}')
    return '\n'.join(parts) + '\n'

def process_figure(elem):
    """Process a figure element."""
    parts = []
    parts.append('\\begin{figure}[htbp]')
    parts.append('\\centering')
    
    graphic = elem.find('tei:graphic', TEI_NS)
    if graphic is not None:
        url = graphic.get('url', '')
        if url:
            # Remove 'images/' prefix if present for LaTeX
            img_path = url.replace('\\', '/')
            parts.append(f'\\includegraphics[max width=\\textwidth]{{{img_path}}}')
    
    head = elem.find('tei:head', TEI_NS)
    if head is not None:
        caption = process_text_content(head)
        parts.append(f'\\caption{{{caption}}}')
    
    parts.append('\\end{figure}')
    return '\n'.join(parts) + '\n'

def process_poem(elem):
    """Process a poem (lg) element."""
    parts = []
    
    # Poem title
    head = elem.find('tei:head', TEI_NS)
    if head is not None:
        title = process_text_content(head)
        parts.append(f'\\poemtitle{{{title}}}\n')
    
    parts.append('\\begin{poem}')
    
    # Check for nested stanzas
    nested_lg = elem.findall('tei:lg', TEI_NS)
    if nested_lg:
        for i, stanza in enumerate(nested_lg):
            if i > 0:
                parts.append('')  # Blank line between stanzas
            for line in stanza.findall('tei:l', TEI_NS):
                line_text = process_text_content(line)
                rend = line.get('rend', '')
                if rend == 'indent':
                    parts.append(f'\\hspace{{2em}}{line_text}')
                elif rend == 'indent2':
                    parts.append(f'\\hspace{{4em}}{line_text}')
                elif rend == 'indent3':
                    parts.append(f'\\hspace{{6em}}{line_text}')
                else:
                    parts.append(line_text)
    else:
        # Single stanza
        for line in elem.findall('tei:l', TEI_NS):
            line_text = process_text_content(line)
            rend = line.get('rend', '')
            if rend == 'indent':
                parts.append(f'\\hspace{{2em}}{line_text}')
            elif rend == 'indent2':
                parts.append(f'\\hspace{{4em}}{line_text}')
            elif rend == 'indent3':
                parts.append(f'\\hspace{{6em}}{line_text}')
            else:
                parts.append(line_text)
    
    parts.append('\\end{poem}')
    return '\n'.join(parts) + '\n'

def process_text_content(elem):
    """Extract text content from element, processing inline markup."""
    result = ''
    
    if elem.text:
        result = latex_escape(elem.text)
    
    for child in elem:
        tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        child_text = latex_escape(''.join(child.itertext()))
        
        if tag == 'hi':
            rend = child.get('rend', 'italic')
            if rend == 'italic':
                result += f'\\textit{{{child_text}}}'
            elif rend == 'bold':
                result += f'\\textbf{{{child_text}}}'
            else:
                result += f'\\textit{{{child_text}}}'
        
        elif tag == 'emph':
            result += f'\\emph{{{child_text}}}'
        
        elif tag == 'ref':
            target = child.get('target', '')
            if target:
                result += f'\\href{{{target}}}{{{child_text}}}'
            else:
                result += child_text
        
        elif tag == 'note':
            result += f'\\footnote{{{child_text}}}'
        
        elif tag == 'foreign' or tag == 'title':
            result += f'\\textit{{{child_text}}}'
        
        else:
            result += child_text
        
        if child.tail:
            result += latex_escape(child.tail)
    
    return result

def latex_escape(text):
    """Escape special LaTeX characters."""
    if not text:
        return ''
    
    # Order matters for some of these
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('$', r'\$'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    
    # Handle backslash first, specially
    text = text.replace('\\', r'\textbackslash{}')
    
    # Then handle the rest
    for char, replacement in replacements[1:]:
        text = text.replace(char, replacement)
    
    return text

def compile_latex_to_pdf(tex_file, pdf_file):
    """Compile LaTeX file to PDF using pdflatex."""
    
    # Check if pdflatex is available
    if not shutil.which('pdflatex'):
        print("Error: pdflatex not found. Please install LaTeX (texlive or miktex).")
        print(f"LaTeX file saved as: {tex_file}")
        print("You can compile it manually with: pdflatex {tex_file}")
        return False
    
    # Get directory and base name
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    tex_base = os.path.basename(tex_file)
    
    print(f"Compiling LaTeX to PDF...")
    
    try:
        # Run pdflatex twice (for references and TOC)
        for run in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_base],
                cwd=tex_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"LaTeX compilation failed on run {run+1}")
                print("Error output:")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                return False
        
        # Move generated PDF to requested location if different
        generated_pdf = tex_file.replace('.tex', '.pdf')
        if os.path.abspath(generated_pdf) != os.path.abspath(pdf_file):
            shutil.move(generated_pdf, pdf_file)
        
        # Clean up auxiliary files
        aux_extensions = ['.aux', '.log', '.out', '.toc']
        base_name = tex_file.replace('.tex', '')
        for ext in aux_extensions:
            aux_file = base_name + ext
            if os.path.exists(aux_file):
                os.remove(aux_file)
        
        print(f"PDF created successfully: {pdf_file}")
        return True
        
    except subprocess.TimeoutExpired:
        print("Error: LaTeX compilation timed out")
        return False
    except Exception as e:
        print(f"Error during LaTeX compilation: {e}")
        return False

