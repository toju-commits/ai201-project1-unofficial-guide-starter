import os
import warnings
from pathlib import Path
import re

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*asyncio\.iscoroutinefunction.*",
)
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r".*unclosed event loop.*",
)

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

def detect_statistics_category(query: str) -> str | None:
    query_lower = query.lower()

    if "football" in query_lower:
        football_categories = {
            "receiving": "individual receiving statistics",
            "rushing": "individual rushing statistics",
            "passing": "individual passing statistics",
            "defensive": "individual defensive statistics",
            "defense": "individual defensive statistics",
        }

        for keyword, category in football_categories.items():
            if keyword in query_lower:
                return category

    if "soccer" in query_lower:
        soccer_categories = {
            "points": "individual overall offensive statistics",
            "goals": "individual overall offensive statistics",
            "assists": "individual overall offensive statistics",
            "shots": "individual overall offensive statistics",
            "saves": "individual overall goalkeeping statistics",
            "goalkeeper": "individual overall goalkeeping statistics",
            "goalkeeping": "individual overall goalkeeping statistics",
        }

        for keyword, category in soccer_categories.items():
            if keyword in query_lower:
                return category

    if "basketball" in query_lower:
        basketball_categories = {
            "scoring": "overall scoring statistics",
            "points": "overall scoring statistics",
            "rebounds": "category leaders - rebounds",
            "assists": "category leaders - assists",
            "steals": "category leaders - steals",
            "blocks": "category leaders - blocked shots",
        }

        for keyword, category in basketball_categories.items():
            if keyword in query_lower:
                return category

    return None


def retrieve_statistics_records(
    collection,
    query: str,
    category: str,
) -> list[dict]:
    results = collection.get(
        where={"document_type": "statistics"},
        include=["documents", "metadatas"],
    )

    query_lower = query.lower()

    season_match = re.search(r"\b20\d{2}(?:-\d{2})?\b", query)
    requested_season = season_match.group(0) if season_match else None

    requested_sport = None

    sport_names = [
        "football",
        "men's soccer",
        "women's soccer",
        "men's basketball",
        "women's basketball",
    ]

    for sport_name in sport_names:
        if sport_name in query_lower:
            requested_sport = sport_name
            break

    retrieved = []

    for document, metadata in zip(
        results["documents"],
        results["metadatas"],
    ):
        if category not in document.lower():
            continue

        metadata_sport = metadata.get("sport", "").lower()
        metadata_season = metadata.get("season", "")

        if requested_sport and metadata_sport != requested_sport:
            continue

        if requested_season and metadata_season != requested_season:
            continue

        retrieved.append(
            {
                "text": document,
                "metadata": metadata,
                "distance": 0.0,
            }
        )

    retrieved.sort(
        key=lambda item: item["metadata"].get(
            "chunk_index",
            0,
        )
    )

    return retrieved


def detect_document_type(query: str) -> str | None:
    query_lower = query.lower()

    statistics_terms = [
        "stat",
        "statistics",
        "receiving",
        "rushing",
        "passing",
        "defensive",
        "defense",
        "yards",
        "touchdowns",
        "tackles",
        "sacks",
        "interceptions",
    ]

    schedule_terms = [
        "schedule",
        "when",
        "what time",
        "what date",
        "where do",
        "where does",
        "play bowdoin",
        "play against",
        "next game",
        "opponent",
        "record",
    ]

    roster_terms = [
        "roster",
        "position",
        "jersey",
        "number",
        "height",
        "weight",
        "hometown",
        "class year",
        "freshman",
        "sophomore",
        "junior",
        "senior",
    ]

    if any(term in query_lower for term in statistics_terms):
        return "statistics"

    if any(term in query_lower for term in schedule_terms):
        return "schedule"

    if any(term in query_lower for term in roster_terms):
        return "roster"

    return None

def retrieve(query: str) -> list[dict]:
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    statistics_category = detect_statistics_category(query)

    if statistics_category:
        statistics_records = retrieve_statistics_records(
            collection,
            query,
            statistics_category,
        )

        if statistics_records:
            return statistics_records

    document_type = detect_document_type(query)
    query_embedding = model.encode(query).tolist()

    query_arguments = {
        "query_embeddings": [query_embedding],
        "n_results": TOP_K,
        "include": [
            "documents",
            "metadatas",
            "distances",
        ],
    }

    if document_type:
        query_arguments["where"] = {
            "document_type": document_type,
        }

    results = collection.query(**query_arguments)

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

def build_source_number_map(
    retrieved: list[dict],
) -> dict[tuple[str, str], int]:
    source_numbers = {}
    next_number = 1

    for item in retrieved:
        metadata = item["metadata"]

        source_key = (
            metadata.get("title", ""),
            metadata.get("source_url", ""),
        )

        if source_key not in source_numbers:
            source_numbers[source_key] = next_number
            next_number += 1

    return source_numbers

def build_context(retrieved: list[dict]) -> str:
    context_blocks = []
    source_numbers = build_source_number_map(retrieved)

    for record_index, item in enumerate(
        retrieved,
        start=1,
    ):
        metadata = item["metadata"]

        source_key = (
            metadata.get("title", ""),
            metadata.get("source_url", ""),
        )

        source_number = source_numbers[source_key]

        block = f"""SOURCE {source_number}
        Internal record index: {record_index}
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
        8. Citations must use exactly this format: [Source 1]. Never include internal record numbers in citations.
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

    source_numbers = build_source_number_map(retrieved)
    seen = set()

    for item in retrieved:
        metadata = item["metadata"]

        title = metadata.get("title", "")
        url = metadata.get("source_url", "")
        source_key = (title, url)

        if source_key in seen:
            continue

        seen.add(source_key)
        source_number = source_numbers[source_key]

        print(f"[Source {source_number}] {title}")
        print(f"  {url}")


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
        "Who led Colby men's soccer in points in 2025?"
    )