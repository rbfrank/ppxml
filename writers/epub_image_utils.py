import os
import shutil
from .common import TEI_NS

def collect_graphic_urls(doc):
    """Return a set of all unique image URLs referenced by <graphic> elements."""
    urls = set()
    for graphic in doc.findall('.//tei:graphic', TEI_NS):
        url = graphic.get('url', '')
        if url:
            urls.add(url)
    return urls

def copy_images_to_epub(urls, input_dir, images_dir):
    """Copy image files from input_dir to images_dir, return a mapping of old->new paths."""
    mapping = {}
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    for url in urls:
        src = os.path.join(input_dir, url)
        filename = os.path.basename(url)
        dst = os.path.join(images_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            mapping[url] = 'images/' + filename
        else:
            mapping[url] = url  # leave as-is if not found
    return mapping
