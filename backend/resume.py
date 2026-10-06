from pathlib import Path
from pypdf import PdfReader
from docx import Document
def text(path):
    p=Path(path); e=p.suffix.lower()
    if e=='.pdf': return '\n'.join((x.extract_text() or '') for x in PdfReader(str(p)).pages)
    if e=='.docx': return '\n'.join(x.text for x in Document(str(p)).paragraphs)
    return p.read_text(encoding='utf-8',errors='ignore')
