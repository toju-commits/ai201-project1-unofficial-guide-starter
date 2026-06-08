# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

I chose **Mule Intelligence**, a retrieval-augmented assistant for Colby College athletics. The system is designed to answer questions about Colby teams, schedules, results, rosters, awards, athletics resources, and official sports news using Colby Athletics and NESCAC source documents.

This knowledge is valuable because athletics information is spread across many different pages: team schedules, rosters, news articles, awards pages, conference pages, facility pages, and student-athlete resource pages. A student, athlete, family member, fan, or journalist may need to search multiple pages to answer one question. For example, asking about a team's season may require the schedule page, roster page, recap articles, and conference awards pages.

The prototype will focus on Colby Athletics because that keeps the project specific and testable. However, the system will be designed with metadata fields like `school`, `sport`, `season`, `document_type`, `source_url`, and `date_accessed`, so it can scale later to other NESCAC schools without rewriting the full pipeline.

The long-term product vision is a live, citation-first NESCAC sports assistant, but the Project 1 version will launch with Colby as the validated first school.

---

## Documents

| #  | Source                            | Description                                                                                                           | URL or location                                                           |
| -- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 1  | Colby Athletics Official Website  | Main athletics hub and navigation source for Colby teams, schedules, rosters, news, awards, facilities, and resources | https://colbyathletics.com/                                               |
| 2  | Colby Football Schedule           | 2025 football schedule, results, opponents, locations, and season record                                              | https://colbyathletics.com/sports/football/schedule                       |
| 3  | Colby Football Roster             | 2025 football roster with player names, positions, years, and hometowns                                               | https://colbyathletics.com/sports/football/roster                         |
| 4  | Colby Football News               | Football news and recap source for game context beyond scores                                                         | https://colbyathletics.com/sports/football/news                           |
| 5  | Colby Men's Soccer Schedule       | Men's soccer schedule and results source                                                                              | https://colbyathletics.com/sports/mens-soccer/schedule                    |
| 6  | Colby Men's Soccer Roster         | Men's soccer roster source                                                                                            | https://colbyathletics.com/sports/mens-soccer/roster                      |
| 7  | Colby Women's Soccer Schedule     | Women's soccer schedule and results source                                                                            | https://colbyathletics.com/sports/womens-soccer/schedule                  |
| 8  | Colby Women's Soccer Roster       | Women's soccer roster source                                                                                          | https://colbyathletics.com/sports/womens-soccer/roster                    |
| 9  | Colby Men's Basketball Schedule   | Men's basketball schedule and results source                                                                          | https://colbyathletics.com/sports/mens-basketball/schedule                |
| 10 | Colby Women's Basketball Schedule | Women's basketball schedule and results source                                                                        | https://colbyathletics.com/sports/womens-basketball/schedule              |
| 11 | Colby All-NESCAC Awards           | Colby awards page for conference recognition across sports                                                            | https://colbyathletics.com/sports/2020/6/9/awards-all-nescac-awards.aspx  |
| 12 | Colby Student-Athlete Wellbeing   | Athletics resource page for student-athlete support and performance context                                           | https://colbyathletics.com/sports/2020/6/9/student-athlete-wellbeing.aspx |

I will save cleaned text versions of these sources in the `documents/` folder. Each document will include a metadata header with the source title, URL, school, sport, season, document type, and date accessed.

Example metadata header:

```text
title: Colby Football Schedule
source_url: https://colbyathletics.com/sports/football/schedule
school: Colby College
sport: Football
season: 2025
document_type: schedule/results
date_accessed: 2026-06-08
```

---

## Chunking Strategy

**Chunk size:** Approximately 700 characters per chunk.

**Overlap:** Approximately 150 characters.

**Reasoning:**

The documents in this project will be a mix of team schedules, rosters, awards pages, news and recap pages, and athletics resource pages. These documents are usually not long textbook-style documents. They are short factual pages with tables, headings, names, dates, scores, and links.

A 700-character chunk is large enough to keep related information together, such as a single schedule entry with opponent, date, location, and score, or a roster section with several players. It is also small enough for retrieval to find specific answers without returning too much unrelated text.

The 150-character overlap helps prevent key information from being split across chunk boundaries. This matters because sports pages often place important facts close together, such as a player name and position, or a date and score. If a chunk boundary splits those details, the answer could become incomplete.

Before chunking, I will clean each document by removing repeated navigation menus, footer text, ad-blocker messages, duplicate links, image labels, and unrelated website boilerplate. For table-heavy pages like schedules and rosters, I will convert important rows into structured natural-language statements before chunking.

Example cleaned schedule row:

```text
Sport: Football. Team: Colby. Season: 2025. Date: September 13, 2025. Opponent: Trinity College. Location: Waterville, ME. Result: Win. Score: 13-6.
```

This makes the text easier for the embedding model to retrieve accurately.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` through the `sentence-transformers` library.

**Top-k:** Retrieve the top 5 chunks for each query.

**Production tradeoff reflection:**

I chose `all-MiniLM-L6-v2` because it is lightweight, free to run locally, and commonly used for beginner RAG prototypes. It should be fast enough for this project while still giving useful semantic search results over short athletics documents.

If I were deploying this system for real users and cost was not a constraint, I would compare stronger embedding models based on accuracy, latency, cost, and how well they handle sports-specific text. Important tradeoffs would include whether the model handles names, abbreviations, mascots, team nicknames, scores, and table-derived text well.

For example, the system should understand that “Mules” refers to Colby and that “football schedule” and “football results” are closely related. I would also consider adding structured filters for `sport`, `season`, and `document_type` so the retrieval step does not confuse football results with basketball results or men's soccer with women's soccer.

For a more advanced version, I would combine vector search with metadata filtering. For example, if the user asks, “What was Colby football's record in 2025?” the system should prioritize chunks where `sport = Football` and `season = 2025`.

### Planned Memory Extension

The core Project 1 system will use RAG over official Colby Athletics and NESCAC documents. A future version will add memory as a separate layer from the official knowledge base.

The memory layer would store user preferences and session context, such as favorite sports, preferred teams, preferred seasons, and whether the user wants short answers or detailed source-heavy answers. This memory would not be treated as factual sports knowledge. Official athletics facts would still come from retrieved source documents.

Memory would improve personalization by helping the assistant interpret follow-up questions and choose better retrieval filters. For example, if a user says they mainly care about Colby football, later questions like “What was their record?” could prioritize football schedule and roster documents.

The planned memory architecture is:

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

## Evaluation Plan

| # | Question                                                                                               | Expected answer                                                                                                                                                                                 |
| - | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | What was Colby football's overall record in 2025?                                                      | The system should answer that Colby football finished 6-3 overall, based on the 2025 football schedule source.                                                                                  |
| 2 | What was the result of Colby football's game against Bowdoin in 2025?                                  | The system should answer that Colby defeated Bowdoin 16-6 in Waterville, Maine, on November 8, 2025, based on the football schedule source.                                                     |
| 3 | Which source should the system use to answer a question about Colby football player positions?         | The system should use the Colby Football Roster source because roster information contains player names and positions.                                                                          |
| 4 | If a user asks, “Who will be Colby's best football player next season?” how should the system respond? | The system should say the provided documents do not contain enough information to support that prediction. It should not invent a future ranking.                                               |
| 5 | Why is source attribution important for Mule Intelligence?                                             | The system should explain that sports information changes over time and is spread across schedules, rosters, news, and awards pages, so answers should cite the retrieved source title and URL. |

I will revise or expand these questions after collecting the final cleaned documents. At least three final evaluation questions will ask about specific facts from the collected sources, such as records, scores, roster information, or awards.

---

## Anticipated Challenges

1. Colby Athletics pages include repeated navigation menus, image labels, footer text, ad-blocker messages, and many duplicate links. If I ingest the raw pages without cleaning, retrieval may return irrelevant chunks from the website navigation instead of the actual schedule, roster, or awards content. To reduce this risk, I will manually inspect the cleaned text and remove repeated website boilerplate before chunking.

2. Sports pages often contain table-like information such as schedules, records, rosters, and scores. If the table text is copied or scraped poorly, important relationships may become unclear. For example, a date, opponent, location, and score might be separated from each other. To reduce this risk, I will rewrite important table rows into structured sentences before embedding them.

3. Because the project includes multiple sports, retrieval could confuse similar terms across documents. For example, a question about basketball schedules could accidentally retrieve football schedule chunks if both contain opponent names and dates. To reduce this risk, I will include metadata such as sport, season, school, and document type in each document and chunk.

4. The project is intended to scale and stay current, but Project 1 will not be a fully automated live production system. To avoid overclaiming, the prototype will include source URLs and `date_accessed` metadata. The future version would rerun ingestion from official URLs to refresh the vector store.

5. A future personalized version may include memory, but memory creates a risk of mixing user preferences with factual source information. For example, if a user says they like football, the system should use that preference to prioritize football documents, not to invent football facts. To reduce this risk, I will treat memory as a routing and personalization layer only. All factual claims about teams, schedules, scores, rosters, and awards must still come from retrieved documents with citations.


---

## Architecture

```text
Official Colby Athletics and NESCAC source pages
        |
        v
Document Ingestion
- Manually collect and clean source text for Project 1
- Save cleaned .txt files in documents/
- Add metadata:
  title
  URL
  school
  sport
  season
  document_type
  date_accessed
        |
        v
Chunking
- Python function reads each document
- Split into approximately 700-character chunks
- Use approximately 150-character overlap
- Preserve metadata for every chunk
        |
        v
Embedding and Vector Store
- Use sentence-transformers model: all-MiniLM-L6-v2
- Store chunk embeddings in ChromaDB
- Persist local vector store so it can be reused
        |
        v
Retrieval
- User asks a Colby athletics question
- Query is embedded using the same embedding model
- Retrieve top 5 most relevant chunks
- Return chunk text plus metadata
        |
        v
Grounded Generation
- LLM receives the retrieved chunks as context
- System prompt instructs the model to answer only from retrieved sources
- If context is insufficient, the model must say so
- Answer includes source titles and URLs
        |
        v
Interface
- Gradio app
- User enters a question
- App displays answer, sources used, and retrieved context preview
```

Future live-refresh extension:

```text
Source URL registry
        |
        v
Refresh script
- Re-download or re-copy current source text
- Update date_accessed and last_updated
- Rebuild cleaned documents
- Rebuild vector store
        |
        v
Fresh RAG answers with source timestamps
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**

I plan to use ChatGPT, Claude, or GitHub Copilot to help implement document loading and chunking. I will give the AI my Domain, Documents, and Chunking Strategy sections from this planning document. I will ask it to write Python functions that read `.txt` files from the `documents/` folder, parse the metadata header, and split the body text into 700-character chunks with 150-character overlap.

I expect the AI to produce readable Python code for loading documents and chunking text. I will verify the output by printing the number of documents loaded, the number of chunks created, and several sample chunks. I will manually check whether important facts like scores, player names, source URLs, and sports metadata stay attached to the correct chunks.

**Milestone 4 — Embedding and retrieval:**

I plan to use ChatGPT, Claude, or GitHub Copilot to help connect `sentence-transformers` with ChromaDB. I will give the AI my Retrieval Approach section and ask it to implement functions for building a local vector store and retrieving the top 5 chunks for a user query.

I expect the AI to produce code that embeds each chunk, stores it with metadata, and retrieves relevant chunks for test questions. I will verify the retrieval manually by running questions like “What was Colby football's 2025 record?” and checking whether the returned chunks come from the football schedule document. I will also test an off-topic or unsupported question to see whether retrieval is weak or irrelevant.

**Milestone 5 — Generation and interface:**

I plan to use ChatGPT, Claude, or GitHub Copilot to help build the grounded answer generation function and a simple Gradio interface. I will give the AI my Architecture, Retrieval Approach, and Evaluation Plan sections. I will ask it to create a system prompt that tells the model to answer only from retrieved context and cite the source title and URL for each answer.

I expect the AI to produce a simple app where the user can type a Colby athletics question and receive a grounded answer with sources. I will verify the output by running my five evaluation questions and checking whether the answer is accurate, whether the correct sources are shown, and whether the system refuses to answer unsupported prediction questions.
