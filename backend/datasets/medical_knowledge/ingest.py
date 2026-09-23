"""
Ingestion script for Dataset 2: Authoritative Medical Knowledge Dataset.
Validates, chunks, embeds, and indexes medical guidelines into FAISS IndexFlatIP.
"""

import os
import sys
import json
import re
import hashlib
import numpy as np

# Set up paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
BASE_DIR = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STORAGE_DIR = os.path.join(BACKEND_DIR, "ai", "rag_storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

INDEX_FILE = os.path.join(STORAGE_DIR, "faiss_index.bin")
CHUNKS_FILE = os.path.join(STORAGE_DIR, "chunks.json")
HASH_FILE = os.path.join(STORAGE_DIR, "corpus_hash.txt")
DATASET_PATH = os.path.join(CURRENT_DIR, "medical_knowledge_dataset.json")


def load_knowledge_dataset(filepath: str = DATASET_PATH):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Medical knowledge dataset not found at: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        docs = json.load(f)
    print(f"Loaded {len(docs)} documents from {filepath}")
    return docs


def validate_document(doc: dict, index: int):
    required_fields = ["id", "title", "specialty", "organization", "content", "source_reference", "reference_url"]
    for field in required_fields:
        if field not in doc or not str(doc[field]).strip():
            raise ValueError(f"Document at index {index} (ID: {doc.get('id')}) missing required field: {field}")
    return True


def chunk_document(doc: dict) -> list:
    """
    Chunks a medical document into focused clinical segments while preserving
    complete citation and reference provenance.
    """
    content = doc["content"].strip()
    doc_id = doc["id"]
    title = doc["title"]
    specialty = doc["specialty"]
    organization = doc["organization"]
    source_reference = doc["source_reference"]
    reference_url = doc["reference_url"]
    condition_covered = doc.get("condition_covered", "")
    evidence_level = doc.get("clinical_evidence_level", "")

    # Clean text
    clean_text = re.sub(r'\s+', ' ', content).strip()
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]

    chunks = []
    if len(sentences) <= 3:
        chunks.append({
            "chunk_id": f"doc_{doc_id}_c0",
            "doc_id": doc_id,
            "title": title,
            "category": specialty,
            "specialty": specialty,
            "condition_covered": condition_covered,
            "organization": organization,
            "source_reference": source_reference,
            "reference_url": reference_url,
            "clinical_evidence_level": evidence_level,
            "content": clean_text
        })
    else:
        step = 2
        window = 3
        c_idx = 0
        for i in range(0, len(sentences), step):
            chunk_sentences = sentences[i:i + window]
            chunk_text = " ".join(chunk_sentences)
            if len(chunk_text) > 40:
                chunks.append({
                    "chunk_id": f"doc_{doc_id}_c{c_idx}",
                    "doc_id": doc_id,
                    "title": title,
                    "category": specialty,
                    "specialty": specialty,
                    "condition_covered": condition_covered,
                    "organization": organization,
                    "source_reference": source_reference,
                    "reference_url": reference_url,
                    "clinical_evidence_level": evidence_level,
                    "content": chunk_text
                })
                c_idx += 1

    return chunks


def compute_dataset_hash(docs: list) -> str:
    serialized = json.dumps([{
        "id": d["id"],
        "title": d["title"],
        "content": d["content"],
        "specialty": d.get("specialty", d.get("category", "")),
        "source_reference": d.get("source_reference", "")
    } for d in docs], sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def ingest_dataset_to_faiss(docs: list = None, force_rebuild: bool = False):
    import faiss
    from sentence_transformers import SentenceTransformer

    if docs is None:
        docs = load_knowledge_dataset()

    for idx, doc in enumerate(docs):
        validate_document(doc, idx)

    current_hash = compute_dataset_hash(docs)

    if not force_rebuild and os.path.exists(INDEX_FILE) and os.path.exists(CHUNKS_FILE) and os.path.exists(HASH_FILE):
        try:
            with open(HASH_FILE, "r") as f:
                saved_hash = f.read().strip()
            if saved_hash == current_hash:
                print("Index is already up to date with corpus hash. Loading from disk.")
                index = faiss.read_index(INDEX_FILE)
                with open(CHUNKS_FILE, "r") as f:
                    chunks = json.load(f)
                return index, chunks, current_hash
        except Exception as e:
            print(f"Error checking existing index: {e}. Rebuilding...")

    print("Building fresh FAISS vector index from medical guidelines...")
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))

    print(f"Generated {len(all_chunks)} chunks from {len(docs)} documents.")

    texts_to_embed = [
        f"{c['title']} | Specialty: {c['category']} | {c['content']}"
        for c in all_chunks
    ]

    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2' on CPU...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)
    embeddings_np = np.array(embeddings, dtype=np.float32)

    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_np)
    print(f"Added {index.ntotal} vectors of dimension {dim} to FAISS IndexFlatIP.")

    # Save to disk
    faiss.write_index(index, INDEX_FILE)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(current_hash)

    print(f"Successfully persisted index to {INDEX_FILE} and metadata to {CHUNKS_FILE}")
    return index, all_chunks, current_hash


if __name__ == "__main__":
    ingest_dataset_to_faiss(force_rebuild=True)
