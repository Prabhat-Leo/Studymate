import time
import logging
import chromadb
from pypdf import PdfReader
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", providers=["CPUExecutionProvider"])

print("DEBUG - warming up embedder...")
_warmup_start = time.time()
dummy_chunks = ["This is a sample sentence used only to warm up the embedding model."] * 10
list(embedder.embed(dummy_chunks))
print(f"DEBUG - embedder warmup took {time.time() - _warmup_start:.2f}s")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("studymate_docs")

def extract_pdf_text(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def chunk_text(text, chunk_size=250, overlap=20):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i+chunk_size]))
        i += chunk_size - overlap
    return chunks

def index_pdf(path, doc_id):
    start = time.time()
    text = extract_pdf_text(path)
    print(f"DEBUG - extraction took {time.time() - start:.2f}s")

    t2 = time.time()
    chunks = chunk_text(text)
    print(f"DEBUG - created {len(chunks)} chunks in {time.time() - t2:.2f}s")
    if not chunks:
        collection.delete(where={"doc_id": doc_id})
        return 0

    t3 = time.time()
    embeddings = [e.tolist() for e in embedder.embed(chunks)]
    print(f"DEBUG - embedding took {time.time() - t3:.2f}s")

    t4 = time.time()
    chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.upsert(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"doc_id": doc_id} for _ in chunks]
    )
    previous_chunks = collection.get(where={"doc_id": doc_id}, include=[])["ids"]
    stale_ids = [chunk_id for chunk_id in previous_chunks if chunk_id not in chunk_ids]
    if stale_ids:
        collection.delete(ids=stale_ids)
    print(f"DEBUG - chroma add took {time.time() - t4:.2f}s")
    return len(chunks)

def retrieve_context(question, doc_id=None, top_k=3, threshold=1.8):
    if not doc_id:
        return ""

    q_embedding = list(embedder.embed([question]))[0].tolist()
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=top_k,
        where={"doc_id": doc_id}
    )
    logger.debug("Retrieved %d document chunks", len(results["documents"][0]))
    logger.debug("Retrieval distances: %s", results["distances"][0])
    if not results["documents"][0]:
        return ""
    distances = results["distances"][0]
    if min(distances) > threshold:
        logger.debug("Rejected context: min distance %.4f exceeds threshold %.4f", min(distances), threshold)
        return ""
    return "\n\n".join(results["documents"][0])

def retrieve_document_context(doc_id, max_chars=14000):
    result = collection.get(
        where={"doc_id": doc_id},
        include=["documents"]
    )
    chunks = [
        (chunk_id, text)
        for chunk_id, text in zip(result["ids"], result["documents"] or [])
        if text
    ]
    chunks.sort(key=lambda item: int(item[0].rsplit("_", 1)[-1]))
    if not chunks:
        return ""

    total_chars = sum(len(text) for _, text in chunks)
    if total_chars <= max_chars:
        return "\n\n".join(text for _, text in chunks)

    sample_count = max(1, max_chars // 1200)
    if sample_count == 1:
        selected_chunks = [chunks[0][1]]
    else:
        indexes = {
            round(index * (len(chunks) - 1) / (sample_count - 1))
            for index in range(sample_count)
        }
        selected_chunks = [chunks[index][1] for index in sorted(indexes)]
    return "\n\n".join(selected_chunks)[:max_chars]

def clear_collection():
    global collection
    chroma_client.delete_collection("studymate_docs")
    collection = chroma_client.get_or_create_collection("studymate_docs")
