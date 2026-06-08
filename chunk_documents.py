from pathlib import Path
import re

ROOT_DIR = Path(__file__).parent
DOCUMENTS_DIR = ROOT_DIR / "documents"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 150


def parse_document(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")

    if "\nCONTENT:\n" not in text:
        raise ValueError(f"Missing CONTENT marker in {path.name}")

    header_text, content = text.split("\nCONTENT:\n", 1)

    metadata = {}

    for line in header_text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    metadata["file_name"] = path.name

    return metadata, content.strip()


def chunk_prose(
    content: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    chunks = []
    start = 0

    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk = content[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(content):
            break

        start = end - overlap

    return chunks


def chunk_structured_records(content: str) -> list[str]:
    records = [
        record.strip()
        for record in content.split("\n\n")
        if record.strip()
    ]

    return records

def chunk_schedule_records(content: str) -> list[str]:
    """
    Keep the season summary together, then create one chunk per game.
    A game begins with a line like: Sep 19 (Sat)
    """
    lines = content.splitlines()

    date_pattern = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"\s+\d{1,2}\s+\([A-Za-z]{3}\)$"
    )

    chunks = []
    current_lines = []
    found_first_game = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if date_pattern.match(line):
            if current_lines:
                chunks.append("\n".join(current_lines))

            current_lines = [line]
            found_first_game = True
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks

def chunk_document(metadata: dict, content: str) -> list[dict]:
    document_type = metadata.get("document_type", "").lower()

    if document_type in {"roster", "statistics"}:
        text_chunks = chunk_structured_records(content)
    elif document_type == "schedule":
        text_chunks = chunk_schedule_records(content)
    else:
        text_chunks = chunk_prose(content)

    chunks = []

    for index, text in enumerate(text_chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_index"] = index

        chunks.append(
            {
                "text": text,
                "metadata": chunk_metadata,
            }
        )

    return chunks


def load_and_chunk_documents() -> list[dict]:
    all_chunks = []

    document_paths = sorted(DOCUMENTS_DIR.glob("*.txt"))

    for path in document_paths:
        metadata, content = parse_document(path)
        chunks = chunk_document(metadata, content)

        print(
            f"{path.name}: "
            f"{len(content)} characters -> {len(chunks)} chunks"
        )

        all_chunks.extend(chunks)

    return all_chunks


def main() -> None:
    chunks = load_and_chunk_documents()

    print()
    print(f"Total chunks: {len(chunks)}")

    print()
    print("First 3 chunks:")

    for index, chunk in enumerate(chunks[:3], start=1):
        metadata = chunk["metadata"]

        print()
        print("=" * 70)
        print(f"Chunk {index}")
        print(f"Source: {metadata.get('title')}")
        print(f"Sport: {metadata.get('sport')}")
        print(f"Season: {metadata.get('season')}")
        print(f"Document type: {metadata.get('document_type')}")
        print(f"Chunk index: {metadata.get('chunk_index')}")
        print("-" * 70)
        print(chunk["text"])


if __name__ == "__main__":
    main()