import pymupdf4llm as pdf
import pymupdf
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

DOC_PATH = os.getenv('DOC_PATH')
EX_DOC_PATH = os.getenv('EX_DOC_PATH')

doc_dir = Path(DOC_PATH).glob('*')
ex_dir = Path(EX_DOC_PATH); ex_dir.mkdir(exist_ok=True)

for doc_path in doc_dir:
    doc = pymupdf.open(doc_path)

    for i in range(len(doc)):
        doc_md = pdf.to_markdown(doc,pages=[i])
        out = ex_dir.joinpath(Path(f'{doc_path.stem}')); out.mkdir(parents=True,exist_ok=True)

        (out / f"{i+1:03}.md").write_text(doc_md, encoding="utf-8")

