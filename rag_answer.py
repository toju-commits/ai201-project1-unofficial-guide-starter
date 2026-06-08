import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer


ROOT_DIR = Path(__file__).parent
CHROMA_DIR = ROOT_DIR / "chroma_db"

COLLECTION_NAME = "colby_athletics"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

load_dotenv(ROOT_DIR / ".env")


def retrieve(query: str) -> list[dict]:
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

    retrieved = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append(
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return retrieved


def build_context(retrieved: list[dict]) -> str:
    context_blocks = []

    for index, item in enumerate(retrieved, start=1):
        metadata = item["metadata"]

        block = f"""SOURCE {index}
Title: {metadata.get("title", "")}
URL: {metadata.get("source_url", "")}
Sport: {metadata.get("sport", "")}
Season: {metadata.get("season", "")}
Document type: {metadata.get("document_type", "")}

Content:
{item["text"]}
"""

        context_blocks.append(block)

    return "\n\n".join(context_blocks)


def generate_answer(
    query: str,
    retrieved: list[dict],
) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY was not found in .env"
        )

    client = Groq(api_key=api_key)
    context = build_context(retrieved)

    system_prompt = """
You are Mule Intelligence, a citation-first assistant for Colby College athletics.

Answer the user's question using only the retrieved sources provided to you.

Rules:
1. Do not use outside knowledge.
2. Do not guess or invent missing facts.
3. If the sources do not contain enough information, say:
   "I could not find enough information in the available Colby Athletics sources."
4. Prefer the most directly relevant source.
5. Keep the answer concise and clear.
6. Cite factual claims using source numbers such as [Source 1].
7. Do not cite a source that does not support the claim.
"""

    user_prompt = f"""User question:
{query}

Retrieved sources:
{context}

Write a grounded answer with source-number citations.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
        max_tokens=500,
    )

    return response.choices[0].message.content


def print_sources(retrieved: list[dict]) -> None:
    print("\nSources:")

    seen = set()
    printed_any = False

    for index, item in enumerate(retrieved, start=1):
        metadata = item["metadata"]
        distance = item["distance"]

        if distance > 0.42:
            continue

        title = metadata.get("title", "")
        url = metadata.get("source_url", "")
        source_key = (title, url)

        if source_key in seen:
            continue

        seen.add(source_key)
        printed_any = True

        print(f"[Source {index}] {title}")
        print(f"  {url}")

    if not printed_any and retrieved:
        metadata = retrieved[0]["metadata"]
        print(f"[Source 1] {metadata.get('title', '')}")
        print(f"  {metadata.get('source_url', '')}")


def answer_question(query: str) -> None:
    retrieved = retrieve(query)
    answer = generate_answer(query, retrieved)

    print("\nQuestion:")
    print(query)

    print("\nAnswer:")
    print(answer)

    print_sources(retrieved)


if __name__ == "__main__":
    answer_question(
        "When does Colby football play Bowdoin in 2026?"
    )