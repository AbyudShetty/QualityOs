"""Render the delivered PDF for visual review and check its document structure."""
import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader

here=Path(__file__).resolve().parent
root=here.parents[2]
out=root/'qualityos/var/visual-guide/previews'
out.mkdir(parents=True,exist_ok=True)
source=root/'QUALITYOS_VISUAL_USER_GUIDE.pdf'
reader=PdfReader(str(source))
doc=pdfium.PdfDocument(str(source))
thumbs=[]
for i in range(len(doc)):
    image=doc[i].render(scale=1.0).to_pil().convert('RGB')
    image.save(out/f'page-{i+1:02d}.png')
    image.thumbnail((490,348))
    tile=Image.new('RGB',(506,374),'#e6e8e0')
    tile.paste(image,((506-image.width)//2,8))
    ImageDraw.Draw(tile).text((12,356),f'PAGE {i+1:02d}',fill='#173b2f')
    thumbs.append(tile)
for begin in range(0,len(thumbs),9):
    sheet=Image.new('RGB',(506*3,374*3),'#d5dfd3')
    for j,tile in enumerate(thumbs[begin:begin+9]):sheet.paste(tile,((j%3)*506,(j//3)*374))
    sheet.save(out/f'overview-{begin//9+1}.png')

captures=json.loads((here/'captures.json').read_text(encoding='utf-8'))
report=json.loads((here/'validation.json').read_text(encoding='utf-8'))
assert hashlib.sha256((root/'QUALITYOS_USER_MANUAL.md').read_bytes()).hexdigest()==captures['markdown_manual_sha256']
assert len(reader.pages)==39 and len(reader.outline)==39
assert all(len(p.extract_text())>200 for p in reader.pages)
assert len(reader.pages[1].get('/Annots',[]))>=8
assert all(float(p.mediabox.width)>float(p.mediabox.height) for p in reader.pages)
assert '/JavaScript' not in reader.trailer['/Root'].get('/Names',{})
report['document_checks']={'all_pages_rendered':len(doc),'nonempty_selectable_text_pages':len(reader.pages),
    'bookmarks':len(reader.outline),'clickable_contents_entries':len(reader.pages[1].get('/Annots',[])),
    'landscape_pages':len(reader.pages),'markdown_unchanged':True,
    'scope':'Document structure and developer visual review; no claim of independent novice comprehension'}
(here/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'Rendered all {len(doc)} PDF pages; text, bookmarks, clickable contents and original Markdown checks passed.')
