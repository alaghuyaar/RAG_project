import re
from pathlib import Path
import ollama, chromadb
import os
from dotenv import load_dotenv

load_dotenv()
INFOSYS_PATH = os.getenv('INFOSYS_PATH')
DATABASE_PATH = os.getenv('DATABASE_PATH')

def chunk_page(text, page, max_chars=2000):
    # split into blocks at blank lines; a table stays one block
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks, cur = [], ""
    for b in blocks:
        if cur and len(cur) + len(b) > max_chars:
            chunks.append("search_document: " + cur); cur = b
        else:
            cur = f"{cur}\n\n{b}" if cur else b
    if cur: chunks.append("search_document: " + cur)
    return [{"text": c, "page": page} for c in chunks]

all_chunks = []
for f in sorted(Path(INFOSYS_PATH).glob("*.md")):
    all_chunks += chunk_page(f.read_text(encoding="utf-8"), int(f.stem))



def embedding(all_chunks):
    db_path = Path(DATABASE_PATH)
    db_path.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    collection  = client.get_or_create_collection(name='my_docs')

    ids = []
    embeddings = []
    metadatas = []
    org_doc = []
    for i,chunk in enumerate(all_chunks,start=1):
        response = ollama.embeddings(model='nomic-embed-text',prompt=f"""{chunk['text']}""")

        embeddings.append(response.embedding)
        ids.append(f'chunk_{i}')
        metadatas.append({'page':chunk['page']})
        org_doc.append(chunk['text'])


    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=org_doc,
        metadatas=metadatas
    )


    return collection


collection = embedding(all_chunks)

#sanity check : length of all_chunks = length of collection

print('Size of all chunks : ',len(all_chunks))
print('Size of Collection(embedding) : ',collection.count())