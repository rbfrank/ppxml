import os
import shutil
from .common import TEI_NS

def collect_graphic_urls(doc, input_dir):
    """Return a set of all unique image URLs referenced by <graphic> elements, plus top-level cover images."""
    urls = set()
    
    # Collect URLs from TEI graphic elements
    for graphic in doc.findall('.//tei:graphic', TEI_NS):
        url = graphic.get('url', '')
        if url:
            urls.add(url)
    
    # Check for top-level cover images
    cover_files = ['cover.jpg', 'cover.jpeg', 'cover.png', 'cover.gif']
    for cover_file in cover_files:
        cover_path = os.path.join(input_dir, cover_file)
        if os.path.exists(cover_path):
            urls.add(cover_file)
            break  # Only include the first cover file found
    
    return urls

def copy_images_to_epub(urls, input_dir, images_dir):
    """Copy image files from input_dir to images_dir, return a mapping of old->new paths."""
    mapping = {}
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # Get the parent directory of images_dir (OEBPS directory)
    oebps_dir = os.path.dirname(images_dir)
    
    for url in urls:
        src = os.path.join(input_dir, url)
        filename = os.path.basename(url)
        
        # Special handling for cover images - place them at the top level
        if filename.lower() in ['cover.jpg', 'cover.jpeg', 'cover.png', 'cover.gif']:
            dst = os.path.join(oebps_dir, filename)
            new_path = filename
        else:
            dst = os.path.join(images_dir, filename)
            new_path = 'images/' + filename
            
        if os.path.exists(src):
            shutil.copy2(src, dst)
            mapping[url] = new_path
        else:
            mapping[url] = url  # leave as-is if not found
    return mapping
