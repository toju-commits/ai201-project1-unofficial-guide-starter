# Mule Intelligence — Project 1

Mule Intelligence is a citation-first retrieval-augmented generation system for Colby College athletics.

The application collects official Colby Athletics schedules, rosters, and cumulative statistics, converts them into structured records, embeds them in a persistent ChromaDB vector store, retrieves relevant evidence, and uses Groq to generate grounded answers with source citations.

The current corpus covers:

* Football
* Men's soccer
* Women's soccer
* Men's basketball
* Women's basketball

The system currently contains **15 source documents** and **793 structure-aware chunks**.

---

## Domain

Mule Intelligence covers Colby College athletics information, including schedules, opponents, locations, season records, player profiles, roster attributes, and individual statistics.

This information is valuable because it is spread across many team-specific pages and formats. A user may need to navigate separate schedule, roster, and statistics pages to answer a single question. Mule Intelligence creates one conversational interface over those official sources while preserving links back to the original pages.

Examples of supported questions include:

* When does Colby football play Bowdoin?
* What position does Sean Trinder play?
* Who led Colby football in receiving yards?
* Who led men's soccer in points?
* Who led men's basketball in scoring?
* What was the men's basketball season record?

The assistant is designed to refuse questions that cannot be supported by the available documents rather than inventing an answer.

---

## Document Sources

The corpus is generated automatically from official Colby Athletics pages.

| #  | Source                                                 | Type       | URL or file path                                                    |
| -- | ------------------------------------------------------ | ---------- | ------------------------------------------------------------------- |
| 1  | Colby Football Schedule                                | Schedule   | `https://colbyathletics.com/sports/football/schedule`               |
| 2  | Colby Football Roster                                  | Roster     | `https://colbyathletics.com/sports/football/roster`                 |
| 3  | 2025 Colby Football Cumulative Statistics              | Statistics | `https://colbyathletics.com/sports/football/stats/2025`             |
| 4  | Colby Men's Soccer Schedule                            | Schedule   | `https://colbyathletics.com/sports/mens-soccer/schedule`            |
| 5  | Colby Men's Soccer Roster                              | Roster     | `https://colbyathletics.com/sports/mens-soccer/roster`              |
| 6  | 2025 Colby Men's Soccer Cumulative Statistics          | Statistics | `https://colbyathletics.com/sports/mens-soccer/stats/2025`          |
| 7  | Colby Women's Soccer Schedule                          | Schedule   | `https://colbyathletics.com/sports/womens-soccer/schedule`          |
| 8  | Colby Women's Soccer Roster                            | Roster     | `https://colbyathletics.com/sports/womens-soccer/roster`            |
| 9  | 2025 Colby Women's Soccer Cumulative Statistics        | Statistics | `https://colbyathletics.com/sports/womens-soccer/stats/2025`        |
| 10 | Colby Men's Basketball Schedule                        | Schedule   | `https://colbyathletics.com/sports/mens-basketball/schedule`        |
| 11 | Colby Men's Basketball Roster                          | Roster     | `https://colbyathletics.com/sports/mens-basketball/roster`          |
| 12 | 2025-26 Colby Men's Basketball Cumulative Statistics   | Statistics | `https://colbyathletics.com/sports/mens-basketball/stats/2025-26`   |
| 13 | Colby Women's Basketball Schedule                      | Schedule   | `https://colbyathletics.com/sports/womens-basketball/schedule`      |
| 14 | Colby Women's Basketball Roster                        | Roster     | `https://colbyathletics.com/sports/womens-basketball/roster`        |
| 15 | 2025-26 Colby Women's Basketball Cumulative Statistics | Statistics | `https://colbyathletics.com/sports/womens-basketball/stats/2025-26` |

The scraper stores generated text documents in `documents/` and collected image metadata in `media/image_metadata.json`.

---

## Chunking Strategy

**Chunk size:** Structure-aware chunks are used for the current schedule, roster, and statistics documents. Fixed-size chunks of approximately 700 characters are available for future prose sources.

**Overlap:** Structured records do not use overlap because each game, athlete, or statistical row remains intact. Future prose documents use approximately 150 characters of overlap.

**Why these choices fit the documents:**

The source corpus contains structured tables and records rather than only continuous prose. Fixed-size splitting could separate a player from their position, a game from its date, or a statistical value from the athlete it describes.

The chunking pipeline therefore uses document-specific behavior:

* Each roster athlete becomes one complete chunk.
* Each schedule page begins with a season-summary chunk.
* Each scheduled game becomes one complete chunk.
* Each supported statistics row becomes one complete chunk.
* Every chunk retains source title, source ID, source URL, school, sport, season, document type, file name, and chunk index.
* Source context is prepended before embedding so individual records remain connected to their school, sport, season, and page.

**Final chunk count:** 793 chunks across 15 documents.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` through Sentence Transformers.

This model was selected because it is free, runs locally, has low latency, and is sufficient for a small English-language athletics corpus. It allows the project to generate embeddings without requiring a paid embedding API.

**Production tradeoff reflection:**

For a production deployment, I would compare local and hosted embedding models based on retrieval accuracy, context length, latency, cost, multilingual support, and performance on names and sports terminology.

A larger hosted model could improve semantic matching but would introduce API cost, network latency, and another external dependency. A larger local model could improve accuracy while preserving privacy, but would increase memory requirements and embedding time.

The current model is appropriate for this prototype because the corpus is relatively small and the system also uses metadata filtering and intent-based routing to improve retrieval precision.

---

## Grounded Generation

**System prompt grounding instruction:**

The model is instructed to answer using only the retrieved Colby Athletics sources. It may not use outside knowledge or guess missing information.

The core grounding rules include:

```text
Answer the user's question using only the retrieved sources provided to you.

Do not use outside knowledge.
Do not guess or invent missing facts.
If the sources do not contain enough information, say:
"I could not find enough information in the available Colby Athletics sources."
Cite factual claims using source numbers such as [Source 1].
Do not cite a source that does not support the claim.
```

The generator uses Groq with a low temperature to reduce unnecessary variation.

**Structural grounding choices:**

* Retrieval results include the source title, URL, sport, season, and document type.
* Queries are routed by intent to schedules, rosters, or statistics.
* Category-wide statistical questions retrieve all relevant player records rather than only the semantic top five.
* Statistics are filtered by requested sport and season.
* Unsupported questions produce a refusal rather than an unsupported prediction.
* Duplicate records from one webpage share one displayed source number.

**How source attribution is surfaced:**

Answers contain citations such as `[Source 1]`. The interface displays the matching official Colby Athletics page title, sport, season, and URL beneath the answer.

---

## Retrieval Architecture

```text
sources.json
    |
    v
scrape_sources.py
    |
    +--> documents/*.txt
    +--> media/image_metadata.json
    |
    v
chunk_documents.py
    |
    v
Sentence Transformers
all-MiniLM-L6-v2
    |
    v
ChromaDB persistent vector store
    |
    v
Intent and statistics-category routing
    |
    v
Groq grounded generation
    |
    v
Colby-styled Gradio interface
```

The entire data refresh process is coordinated through `refresh_pipeline.py`.

---

## Automated Refresh Pipeline

Run:

```powershell
python refresh_pipeline.py
```

The command performs the following steps:

1. Scrapes and cleans every source registered in `sources.json`.
2. Removes stale generated documents when a source fails.
3. Rejects sources that produce empty content.
4. Validates and chunks all generated documents.
5. Rebuilds the persistent ChromaDB vector store.
6. Runs retrieval smoke tests.
7. Stops immediately if any stage fails.

This prevents the documents, chunks, and vector database from silently becoming inconsistent.

---

## Evaluation Report

| # | Question                                                 | Expected answer                                      | System response, summarized                                                          | Retrieval quality | Response accuracy |
| - | -------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------- | ----------------- |
| 1 | What position does Sean Trinder play?                    | Wide receiver                                        | Identified Sean Trinder as a WR and cited the football roster.                       | Relevant          | Accurate          |
| 2 | When does Colby football play Bowdoin in 2026?           | November 14, 2026 at 1:00 PM in Brunswick, Maine     | Returned the correct date, time, and location with a schedule citation.              | Relevant          | Accurate          |
| 3 | Who led the 2025 Colby football team in receiving yards? | Jack Nye with 369 yards                              | Compared the receiving-statistics records and identified Jack Nye with 369 yards.    | Relevant          | Accurate          |
| 4 | Who led Colby men's basketball in scoring in 2025-26?    | Dan Civello with 457 points and 18.3 points per game | Identified Dan Civello and returned both his total and per-game average.             | Relevant          | Accurate          |
| 5 | Who led Colby men's soccer in points in 2025?            | Jude Gussen with 11 points                           | Compared the offensive-statistics records and identified Jude Gussen with 11 points. | Relevant          | Accurate          |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

Additional unsupported-question test:

```text
Question: Who will be Colby's best football player next season?

Response:
I could not find enough information in the available Colby Athletics sources.
```

This confirmed that the assistant refused a prediction that was not supported by the corpus.

---
### Informal User Testing

I conducted an informal user test with family members using questions that were not part of the original evaluation set.

One successful test involved a student-athlete who appears on both the football and basketball rosters. When asked for his jersey number, Mule Intelligence correctly returned both numbers and distinguished them by sport. This demonstrated that the system can retrieve and combine multiple records for the same person across different teams.

The test also exposed limitations in reverse-lookup questions. For example:

```text
Who is number 95 on Colby football?
```

The relevant football roster record was present in the corpus, but the system did not reliably identify Joshua Iyonsi from the jersey number alone. This suggests that the current semantic retrieval and keyword-based routing perform better when a query includes a player name than when the system must search by a short numeric attribute.

A future improvement would add structured metadata fields for jersey numbers and support exact-match or hybrid retrieval. The system could first filter by sport and document type, then search structured fields such as jersey number before falling back to semantic similarity.

## Failure Case Analysis

**Question that failed:**

```text
Who led the 2025 Colby football team in receiving yards?
```

**Initial system behavior:**

The first version of the corpus contained only schedules and rosters, so it did not include receiving statistics. The system correctly refused to answer rather than guessing.

After adding football statistics, the question initially failed again because semantic top-five retrieval returned defensive records instead of the full receiving table.

**Root cause:**

The first failure occurred during document coverage: the required information was absent from the corpus.

The second failure occurred during retrieval: a “who led” question requires comparison across all records in a statistical category, but ordinary semantic top-k retrieval returned only a small subset.

**Fix:**

* Added the official football cumulative statistics page.
* Built a statistics-table normalizer.
* Preserved one athlete-stat row per chunk.
* Added intent-based document filtering.
* Added sport-aware statistics-category routing.
* Retrieved the full matching statistics category for leader and aggregation questions.
* Added smoke tests so corpus expansion does not silently break schedule or roster retrieval.

A second retrieval failure occurred with the question:

```text
When does Colby football play Bowdoin in 2026?
```

The first schedule chunks did not repeat the school, sport, or season inside every game record. The general season-summary chunk ranked above the actual Bowdoin game.

This was fixed by prepending source context to each chunk before embedding.

---

## Spec Reflection

**One way the spec helped during implementation:**

The planning document established the five-stage RAG pipeline before implementation: ingestion, chunking, embeddings, retrieval, and generation. That made it easier to work incrementally and test each stage independently instead of attempting to build the entire application at once.

The requirement to define chunking behavior also led to structure-aware records. Roster players, schedule games, and statistics rows remain intact rather than being split arbitrarily.

**One way the implementation diverged from the spec, and why:**

The initial plan focused primarily on schedules, rosters, news, awards, and future image support. During user testing, a question about the receiving-yard leader revealed that statistics were a major missing feature.

The implementation therefore expanded earlier than planned to include cumulative statistics and sport-aware aggregation routing. The system also gained an automated refresh pipeline and regression smoke tests because manual rebuilding became too easy to forget as the corpus grew.

---

## AI Usage

### Instance 1

* **What I gave the AI:** The planned roster fields, the HTML class names discovered from the Colby Athletics roster page, and examples of noisy raw output.
* **What it produced:** A roster-specific extraction function using Sidearm roster classes.
* **What I changed or overrode:** I tested the output and corrected season detection, duplicate jersey numbers in player names, and position fields that incorrectly included height and weight. I preserved one athlete per record after confirming the structure manually.

### Instance 2

* **What I gave the AI:** Examples of football and basketball statistics tables, including captions, headers, first rows, and corrupted extraction output.
* **What it produced:** A generalized statistics normalizer and suggestions for supported table patterns.
* **What I changed or overrode:** I rejected ambiguous grouped-header and multi-player game-high tables rather than embedding unreliable values. I selected flat, one-player-per-row tables and added row-width validation, stale-file removal, empty-content validation, intent routing, and smoke tests.

### Instance 3

* **What I gave the AI:** Retrieval results showing that the Bowdoin schedule summary ranked above the actual game and that leader questions compared incomplete records.
* **What it produced:** Contextual embeddings and category-wide statistics retrieval.
* **What I changed or verified:** I rebuilt ChromaDB, reran the same questions, inspected ranking changes, and added automated retrieval tests for roster, schedule, football statistics, basketball statistics, and soccer statistics.

---

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Add a Groq API key to `.env`:

```text
GROQ_API_KEY=your_key_here
```

Never commit `.env`.

---

## Running the Project

Refresh all data and rebuild the vector store:

```powershell
python refresh_pipeline.py
```

Launch the interface:

```powershell
python app.py
```

Open the local Gradio URL printed in the terminal, usually:

```text
http://127.0.0.1:7860
```

Run retrieval smoke tests independently:

```powershell
python smoke_tests.py
```

Run command-line generation:

```powershell
python rag_answer.py
```

---

## Main Files

```text
app.py                  Gradio user interface
rag_answer.py           Retrieval routing and grounded generation
scrape_sources.py       Source ingestion and structured extraction
chunk_documents.py      Metadata parsing and structure-aware chunking
build_vector_store.py   Embedding generation and ChromaDB persistence
refresh_pipeline.py     End-to-end refresh orchestration
smoke_tests.py          Retrieval regression tests
sources.json            Registered source configuration
planning.md             Project specification and architecture
documents/              Generated text documents
media/                  Image metadata
```

---

## Current Limitations

* The current corpus covers five Colby sports rather than every varsity program.
* Statistics support depends on trustworthy, flat HTML tables.
* Ambiguous grouped-header and multi-player rows are intentionally skipped.
* The system does not yet ingest news stories, awards pages, or game recaps.
* Image metadata is collected, but image-to-answer matching remains limited.
* The application currently runs locally and has not yet been deployed.
* The embedding model may struggle with highly ambiguous or underspecified questions.
* Intent routing currently uses keyword-based rules and can be expanded.
* Reverse lookups from short numeric attributes, such as jersey numbers, are not always reliable with semantic retrieval alone.
* A person appearing across multiple sports may produce several valid records that require entity-aware grouping.
* Some natural-language questions require query normalization or exact structured filtering rather than vector similarity.

---

## Future Work

Planned improvements include:

* Add the remaining Colby varsity sports.
* Ingest news stories, game recaps, awards, and historical archives.
* Associate player headshots and event images with retrieved answers.
* Add conversational memory and user preferences.
* Replace hard-coded intent keywords with a lightweight query classifier.
* Detect changed sources and rebuild only affected documents.
* Schedule automatic refreshes.
* Add unit tests for table normalization.
* Deploy the application publicly.
* Expand the architecture from Colby Athletics to the full NESCAC.

---

## Project Status

The current prototype successfully provides grounded, cited answers from official Colby Athletics schedules, rosters, and cumulative statistics.

The system has been tested across multiple sports and document formats, includes failure handling and regression tests, and can refresh its entire corpus through one command.
