# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

I chose **Mule Intelligence**, a retrieval-augmented assistant for Colby College athletics. The system is designed to answer questions about Colby teams, schedules, results, rosters, awards, athletics resources, official sports news, and related media using official Colby Athletics and NESCAC-connected source documents.

This knowledge is valuable because Colby athletics information is spread across many separate official pages: team schedules, rosters, story archives, awards pages, photo galleries, department resources, and student-athlete support pages. A student, athlete, family member, fan, alum, journalist, or recruit may need to search multiple pages to answer one question. For example, asking about a team’s season may require the schedule page, roster page, recap articles, and award pages.

The prototype will focus on Colby Athletics because that keeps the project specific, testable, and useful. However, the architecture will be designed to scale later to the rest of the NESCAC. Each source and chunk will carry metadata such as `school`, `sport`, `season`, `document_type`, `source_url`, `source_id`, and `date_accessed`, so adding another NESCAC school later should mostly mean adding new source registry entries rather than rewriting the full RAG pipeline.

The long-term product vision is a live, citation-first NESCAC sports intelligence assistant. The Project 1 version will launch with Colby as the validated first school and will include a refresh-friendly scraping plan so the system does not become outdated after one season.

---

## Documents

The initial corpus will use verified official Colby Athletics pages. A source registry will store each URL and its metadata so the scraper can refresh the documents without changing the ingestion code.

| #  | Source                            | Description                                                                                                                | URL or location                                                            |
| -- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1  | Colby Athletics Official Website  | Main athletics hub with team navigation, athletics resources, stories, scoreboard, galleries, and official links           | https://colbyathletics.com/                                                |
| 2  | Colby Football Schedule           | Current football schedule page with season selector, record, opponents, locations, results, box scores, and recaps         | https://colbyathletics.com/sports/football/schedule                        |
| 3  | Colby Football Roster             | Current football roster with player names, numbers, positions, class years, hometowns, heights, weights, and profile links | https://colbyathletics.com/sports/football/roster                          |
| 4  | Colby Football Story Archives     | Football news and game recap archive                                                                                       | https://colbyathletics.com/sports/football/archives                        |
| 5  | Colby Men's Soccer Schedule       | Current men's soccer schedule and results page                                                                             | https://colbyathletics.com/sports/mens-soccer/schedule                     |
| 6  | Colby Men's Soccer Roster         | Current men's soccer roster and player profile source                                                                      | https://colbyathletics.com/sports/mens-soccer/roster                       |
| 7  | Colby Women's Soccer Schedule     | Current women's soccer schedule and results page                                                                           | https://colbyathletics.com/sports/womens-soccer/schedule                   |
| 8  | Colby Women's Soccer Roster       | Current women's soccer roster and player profile source                                                                    | https://colbyathletics.com/sports/womens-soccer/roster                     |
| 9  | Colby Men's Basketball Schedule   | Current men's basketball schedule, record, opponents, and results                                                          | https://colbyathletics.com/sports/mens-basketball/schedule                 |
| 10 | Colby Women's Basketball Schedule | Current women's basketball schedule, record, opponents, and results                                                        | https://colbyathletics.com/sports/womens-basketball/schedule               |
| 11 | Colby All-NESCAC Awards           | Historical conference award information for Colby athletes across sports                                                   | https://colbyathletics.com/sports/2022/7/27/all-nescac.aspx                |
| 12 | Colby Student Athlete Wellbeing   | Official athletics support and wellbeing information                                                                       | https://colbyathletics.com/sports/2022/8/22/student-athlete-wellbeing.aspx |
| 13 | Colby Athletics Galleries         | Official athletics photo gallery index                                                                                     | https://colbyathletics.com/galleries/                                      |

The collection process will be automated through a source registry and scraper rather than relying entirely on manual copy-and-paste. Each source entry will specify:

* source id
* source name
* source URL
* school
* sport
* season, when applicable
* document type
* whether images should be collected
* refresh frequency
* last successful retrieval time

The scraper will save cleaned textual content for RAG ingestion and a separate structured metadata record for source attribution, freshness, and image presentation.

Example source registry entry:

```json
{
  "id": "colby-football-schedule",
  "title": "Colby Football Schedule",
  "url": "https://colbyathletics.com/sports/football/schedule",
  "school": "Colby College",
  "sport": "Football",
  "season": "current",
  "document_type": "schedule",
  "collect_images": true,
  "refresh_frequency": "daily"
}
```

---

## Multimedia and Image Plan

Mule Intelligence will be designed as a multimedia RAG assistant. Its factual answers will continue to come from retrieved text documents, but relevant official images may be displayed beside an answer when the retrieved source includes useful visual content.

For each meaningful image, the scraper will attempt to collect:

* image URL
* alt text
* caption
* photographer or image credit, when available
* source page URL
* associated school
* associated sport
* associated team, athlete, game, or article
* date collected

The scraper will ignore likely decorative assets such as site logos repeated on every page, social-media icons, navigation images, advertisements, tracking images, and very small thumbnails.

Images will be linked to their parent source document through metadata. The initial retrieval system will remain text-based. When a text document or chunk is retrieved, the interface may display an image associated with that source.

```text
User question
        |
        v
Text retrieval finds relevant document chunks
        |
        v
Retrieved chunk metadata identifies its source
        |
        v
Image metadata store finds images associated with that source
        |
        v
Answer is displayed with citations and an optional relevant image
```

The system will preserve the original source page and image URL instead of presenting an image as independently owned content. Image credits will be shown when the source provides them.

A future multimodal version could use an image-text embedding model such as CLIP to search images by visual meaning. That feature is outside the required Project 1 text-RAG pipeline and will only be attempted after ingestion, retrieval, generation, citations, and evaluation are working correctly.

---

## Chunking Strategy

**Chunk size:** Approximately 700 characters per chunk, with structure-aware exceptions for schedules, rosters, awards, and article sections.

**Overlap:** Approximately 150 characters for prose documents. Structured rows such as a single schedule event, roster player, or award entry will remain intact and will not rely on character overlap.

**Reasoning:**

The source corpus includes schedules, rosters, awards pages, news archives, articles, galleries, and athletics resource pages. These formats should not all be processed identically.

For prose such as recaps and resource pages, the scraper will preserve headings and divide content into approximately 700-character chunks with 150-character overlap.

For structured pages:

* each schedule game will become its own structured text record
* each roster player will become an individual structured record
* award entries will be grouped by sport, season, or award section
* article titles, dates, summaries, and source links will remain together
* gallery entries will preserve image title, caption, source page, and sport when available

Example schedule record:

```text
Record type: game
School: Colby College
Sport: Football
Season: 2025
Date: September 13, 2025
Opponent: Trinity College
Location: Waterville, Maine
Site: Home
Result: Win
Score: 13-6
Source: Colby Football Schedule
```

Example player record:

```text
Record type: athlete
School: Colby College
Sport: Football
Season: 2025
Player: Example Player
Number: 0
Position: Wide Receiver
Class year: Sophomore
Height: 6 feet 1 inch
Weight: 200 pounds
Hometown: Fair Haven, New Jersey
Source: Colby Football Roster
```

Before chunking, the ingestion process will remove repeated navigation menus, footer content, cookie or ad-blocker notices, duplicate links, social media links, and unrelated site-wide text.

Image metadata will not be embedded directly into prose chunks. Instead, each chunk will contain an identifier such as `source_id`, and image records will use the same identifier so the interface can associate retrieved facts with relevant images.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` through the `sentence-transformers` library.

**Top-k:** Retrieve the top 5 chunks for each query.

**Production tradeoff reflection:**

I chose `all-MiniLM-L6-v2` because it is lightweight, free to run locally, and commonly used for beginner RAG prototypes. It should be fast enough for this project while still giving useful semantic search results over short athletics documents.

If I were deploying this system for real users and cost was not a constraint, I would compare stronger embedding models based on accuracy, latency, cost, and how well they handle sports-specific text. Important tradeoffs would include whether the model handles names, abbreviations, mascots, team nicknames, scores, table-derived text, and short factual queries well.

For example, the system should understand that “Mules” refers to Colby and that “football schedule” and “football results” are closely related. I would also consider adding structured filters for `sport`, `season`, `document_type`, and `school` so the retrieval step does not confuse football results with basketball results or men's soccer with women's soccer.

For a more advanced version, I would combine vector search with metadata filtering. For example, if the user asks, “What was Colby football's record in 2025?” the system should prioritize chunks where `sport = Football` and `season = 2025`.

---

## Evaluation Plan

| # | Question                                                                                               | Expected answer                                                                                                                                   |
| - | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | What was Colby football's overall record on the current football schedule page?                        | The system should retrieve the Colby Football Schedule source and answer using the season record shown in that document.                          |
| 2 | Which source should the system use to answer a question about Colby football player positions?         | The system should use the Colby Football Roster source because roster information contains player names and positions.                            |
| 3 | What kind of information does the Colby All-NESCAC Awards page provide?                                | The system should answer that it provides historical conference award information for Colby athletes across sports.                               |
| 4 | If a user asks, “Who will be Colby's best football player next season?” how should the system respond? | The system should say the provided documents do not contain enough information to support that prediction. It should not invent a future ranking. |
| 5 | If the system displays an image with an answer, what should the image be based on?                     | The image should come from official source metadata connected to the retrieved document, not from a hallucinated or unrelated image search.       |

I will revise or expand these questions after collecting the final cleaned documents. At least three final evaluation questions will ask about specific facts from the collected sources, such as records, scores, roster information, awards, or student-athlete resources.

---

## Anticipated Challenges

1. Colby Athletics is powered by a sports-content website structure that contains repeated navigation, menus, accessibility text, logos, footer content, ad-blocker notices, and many duplicate links. A generic scraper may collect more boilerplate than useful sports information. The cleaning system will therefore target meaningful page sections and the output will be manually inspected during development.

2. Schedule and roster pages are visually structured but may become disorganized when converted to plain text. A score could be separated from its opponent, or a player's name could be separated from the player's position. The scraper will use page-type-specific extraction rules and convert each row or profile into a self-contained structured record.

3. Current schedule pages may automatically point to a new season when the school updates the site. The source registry will distinguish between `current` pages and explicitly archived seasons. Each generated document will store both the season detected on the page and the retrieval timestamp.

4. Images may include decorative assets, school logos, opponent logos, athlete headshots, gallery photos, and article images. Saving all of them would create noise and unnecessary storage. Image filtering will use alt text, HTML context, dimensions when available, file patterns, and source location to keep only likely content images.

5. Some images may have missing alt text, captions, or credits. The system must not invent an identity or description. Images with insufficient metadata may be preserved as source-linked assets but should not be presented as factual evidence about a specific athlete or event.

6. Source URLs can change over time. The scraper will log failed requests, HTTP status codes, redirect destinations, and the last successful retrieval time. A failed source will not silently overwrite a previously valid document with an empty file.

7. Adding conversation or user memory creates a risk of mixing personal preferences with official sports facts. Memory may help select a sport, season, or preferred answer style, but all claims about scores, schedules, athletes, rosters, and awards must remain grounded in retrieved official documents.

---

## Architecture

```text
Verified source registry
- URL
- school
- sport
- season
- document type
- image collection setting
- refresh frequency
        |
        v
Automated source collector
- Requests + Beautiful Soup for standard HTML
- Optional browser-based fallback for JavaScript-rendered pages
- Follow redirects
- Record failures and retrieval timestamps
        |
        +---------------------------+
        |                           |
        v                           v
Text extraction                Image extraction
- schedules                    - image URL
- rosters                      - alt text
- articles                     - caption
- awards                       - credit
- resource pages               - parent source
        |                           |
        v                           v
Cleaned documents             Image metadata store
- structured records           - JSON metadata
- prose sections               - source associations
- source metadata              - optional cached files
        |                           |
        v                           |
Chunking                        |
- structure-aware chunks        |
- prose: ~700 chars             |
- overlap: ~150 chars           |
- preserve source_id            |
        |                        |
        v                        |
Embedding + vector store        |
- all-MiniLM-L6-v2              |
- ChromaDB                      |
- chunk metadata                |
        |                        |
        v                        |
Retrieval                       |
- top 5 chunks                  |
- optional metadata filters     |
        |                        |
        +------------+-----------+
                     |
                     v
Grounded generation
- answer only from retrieved context
- refuse unsupported claims
- cite title and source URL
                     |
                     v
Gradio interface
- answer
- citations
- source freshness
- optional relevant source image
```

### Planned Live-Update Process

```text
Scheduled or manual refresh
        |
        v
Check each registered source
        |
        v
Download current content
        |
        v
Detect whether meaningful content changed
        |
        +---- no change ----> keep existing document and embeddings
        |
        +---- changed ------> regenerate document and image metadata
                              |
                              v
                        replace affected vector entries
                              |
                              v
                        record refreshed timestamp
```

The Project 1 implementation may initially use a manual command such as:

```text
python scrape_sources.py
```

The architecture will allow the same command to be scheduled later without rewriting the main RAG application.

---

## Planned Memory Extension

The core Project 1 system will use RAG over official Colby Athletics and NESCAC-connected documents. A future version will add memory as a separate layer from the official knowledge base.

The memory layer would store user preferences and session context, such as favorite sports, preferred teams, preferred seasons, and whether the user wants short answers or detailed source-heavy answers. This memory would not be treated as factual sports knowledge. Official athletics facts would still come from retrieved source documents.

Memory would improve personalization by helping the assistant interpret follow-up questions and choose better retrieval filters. For example, if a user says they mainly care about Colby football, later questions like “What was their record?” could prioritize football schedule and roster documents.

```text
User question
        |
        v
Session / preference memory
- favorite sports
- preferred school
- preferred season
- answer style
        |
        v
Query rewriting and metadata filtering
        |
        v
RAG retrieval from official source documents
        |
        v
Grounded answer generation with citations
```

This keeps factual accuracy grounded in official documents while allowing the assistant to become more personalized over time.

---

## AI Tool Plan

**Milestone 3 — Automated ingestion, image collection, and chunking:**

I will give an AI tool my Documents, Multimedia and Image Plan, Chunking Strategy, and Architecture sections. I will ask it to help design a beginner-readable scraper that reads verified URLs from a source registry, checks HTTP responses, follows redirects, extracts useful page content, and saves cleaned documents and image metadata.

The first implementation will target one known page type, such as the Colby football schedule. I will verify the code by comparing the generated records against the visible official page. I will check that opponents, dates, locations, results, scores, source URLs, and season metadata are correct.

After the first page works, I will ask the AI to help refactor the code into reusable extraction functions for schedules, rosters, archives, articles, awards pages, and general resource pages. I will not accept a generalized scraper until I test each page type manually.

For image extraction, I will verify that retained images come from meaningful page content and that decorative logos, icons, and tracking assets are excluded. I will not allow the AI to invent captions, athlete identities, or image credits.

**Milestone 4 — Embedding and retrieval:**

I will give the AI my Retrieval Approach and the exact cleaned document format produced by the scraper. I will ask it to implement embedding and ChromaDB storage while preserving `source_id`, sport, season, document type, source URL, and retrieval timestamp.

I will verify retrieval using direct factual questions and inspect the raw returned chunks before adding answer generation. I will also confirm that a retrieved chunk can be matched to its associated image metadata through `source_id`.

**Milestone 5 — Generation and multimedia interface:**

I will give the AI the Architecture, Evaluation Plan, grounding requirements, and image metadata structure. I will ask it to implement a Gradio interface that displays a grounded answer, source citations, freshness information, and an optional image associated with the retrieved source.

I will test whether the answer remains correct when no relevant image exists. Image display will be optional and must never replace textual evidence or citations.
