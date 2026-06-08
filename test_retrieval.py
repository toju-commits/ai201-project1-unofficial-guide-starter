from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


ROOT_DIR = Path(__file__).parent
CHROMA_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "colby_athletics"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5


def retrieve(query: str) -> None:
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nQuery: {query}\n")

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1,
    ):
        print("=" * 70)
        print(f"Result {rank}")
        print(f"Distance: {distance:.4f}")
        print(f"Source: {metadata.get('title')}")
        print(f"Sport: {metadata.get('sport')}")
        print(f"Season: {metadata.get('season')}")
        print(f"Document type: {metadata.get('document_type')}")
        print("-" * 70)
        print(document)
        print()


if __name__ == "__main__":
    retrieve("What position does Sean Trinder play?")