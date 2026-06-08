from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunk_documents import load_and_chunk_documents


ROOT_DIR = Path(__file__).parent
CHROMA_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "colby_athletics"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build_vector_store() -> None:
    print("Loading and chunking documents...")
    chunks = load_and_chunk_documents()

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Creating embeddings...")
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
    ).tolist()

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    # Rebuild the collection so refreshed source data replaces old data.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        metadata = chunk["metadata"]

        chunk_id = (
            f"{metadata.get('source_id', 'unknown')}"
            f"-chunk-{metadata.get('chunk_index', index)}"
        )

        ids.append(chunk_id)

        metadatas.append(
            {
                "title": metadata.get("title", ""),
                "source_id": metadata.get("source_id", ""),
                "source_url": metadata.get("source_url", ""),
                "school": metadata.get("school", ""),
                "sport": metadata.get("sport", ""),
                "season": metadata.get("season", ""),
                "document_type": metadata.get("document_type", ""),
                "file_name": metadata.get("file_name", ""),
                "chunk_index": int(metadata.get("chunk_index", 0)),
            }
        )

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print()
    print(f"Stored {collection.count()} chunks in ChromaDB.")
    print(f"Database location: {CHROMA_DIR}")


if __name__ == "__main__":
    build_vector_store()