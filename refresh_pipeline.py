import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent


def run_step(name: str, script_name: str) -> None:
    print()
    print("=" * 70)
    print(f"STEP: {name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, script_name],
        cwd=ROOT_DIR,
        check=False,
    )

    if result.returncode != 0:
        print()
        print(f"PIPELINE FAILED DURING: {name}")
        raise SystemExit(result.returncode)

    print()
    print(f"COMPLETED: {name}")


def main() -> None:
    run_step(
        "Scrape and clean registered sources",
        "scrape_sources.py",
    )

    run_step(
        "Validate and chunk documents",
        "chunk_documents.py",
    )

    run_step(
        "Rebuild the Chroma vector store",
        "build_vector_store.py",
    )

    run_step(
        "Run retrieval smoke tests",
        "smoke_tests.py",
    )

    print()
    print("=" * 70)
    print("PIPELINE REFRESH COMPLETE")
    print("=" * 70)
    print("Sources, documents, chunks, and ChromaDB are synchronized.")
    print("Restart app.py if it was already running.")


if __name__ == "__main__":
    main()