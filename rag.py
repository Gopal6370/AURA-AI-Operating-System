import json
from typing import List, Tuple
from sqlalchemy.orm import Session
from pypdf import PdfReader
from .models import DocumentChunk
from .ai import embed_texts, cosine_scores

def split_text(text: str, size: int = 1200, overlap: int = 200) -> List[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def index_pdf(db: Session, user_id: int, filepath: str, filename: str):
    reader = PdfReader(filepath)
    texts = []
    metadata = []
    for page_no, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        for chunk in split_text(raw):
            texts.append(chunk)
            metadata.append(page_no)

    if not texts:
        raise ValueError("No extractable text found in this PDF.")

    vectors = embed_texts(texts)
    for text, page_no, vector in zip(texts, metadata, vectors):
        db.add(DocumentChunk(
            user_id=user_id,
            filename=filename,
            page=page_no,
            text=text,
            embedding=json.dumps(vector),
        ))
    db.commit()
    return len(texts)

def retrieve(db: Session, user_id: int, query: str, top_k: int = 5) -> List[Tuple[str, int, str, float]]:
    rows = db.query(DocumentChunk).filter(DocumentChunk.user_id == user_id).all()
    if not rows:
        return []

    qvec = embed_texts([query])[0]
    matrix = [json.loads(row.embedding) for row in rows]
    scores = cosine_scores(qvec, matrix)
    indices = np.argsort(scores)[::-1][:top_k] if len(scores) else []

    return [(rows[i].filename, rows[i].page, rows[i].text, float(scores[i])) for i in indices]

import numpy as np
