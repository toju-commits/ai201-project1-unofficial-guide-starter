import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT_DIR = Path(__file__).parent
DOCUMENTS_DIR = ROOT_DIR / "documents"
MEDIA_DIR = ROOT_DIR / "media"
IMAGE_METADATA_PATH = MEDIA_DIR / "image_metadata.json"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_page_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    for selector in ["nav", "header", "footer"]:
        for tag in soup.select(selector):
            tag.decompose()

    skip_exact = {
        "skip to main content",
        "pause all rotators",
        "history",
        "watch",
        "live stats",
        "scheduled games",
        "box score",
        "recap",
    }

    lines = []

    for raw_line in soup.get_text(separator="\n").splitlines():
        line = clean_text(raw_line)

        if not line or len(line) <= 2:
            continue

        if line.lower() == "score by period":
            break

        if line.lower() in skip_exact:
            continue

        if line.lower().startswith("hide/show additional information for"):
            continue

        # Avoid immediately repeated lines such as duplicate locations.
        if lines and lines[-1] == line:
            continue
                
        lines.append(line)

    return "\n".join(lines)


def extract_images(
    soup: BeautifulSoup,
    page_url: str,
    source: dict,
) -> list[dict]:
    images = []

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")

        if not src:
            continue

        full_url = urljoin(page_url, src)
        alt_text = clean_text(img.get("alt", ""))
        image_type = "logo" if "logo" in alt_text.lower() else "content"

        images.append(
            {
                "source_id": source["id"],
                "source_title": source["title"],
                "source_url": page_url,
                "image_url": full_url,
                "alt_text": alt_text,
                "image_type": image_type,
                "sport": source.get("sport", ""),
                "season": source.get("season", ""),
                "date_collected": datetime.now().strftime("%Y-%m-%d"),
            }
        )

    return images

def extract_roster_text(soup: BeautifulSoup) -> str:
    players = []

    for player in soup.select(".sidearm-roster-player"):
        name = clean_text(
            player.select_one(".sidearm-roster-player-name").get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-name") else ""
        
        name = re.sub(r"^\d+\s+", "", name).strip()

        jersey = clean_text(
            player.select_one(
                ".sidearm-roster-player-jersey-number"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-jersey-number") else ""

        position = clean_text(
            player.select_one(
                ".sidearm-roster-player-position"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-position") else ""
        
        position = re.sub(
            r"\s+\d+'\d+\"(?:\s+\d+\s*lbs)?\s*$",
            "",
            position,
        ).strip()

        height = clean_text(
            player.select_one(
                ".sidearm-roster-player-height"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-height") else ""

        weight = clean_text(
            player.select_one(
                ".sidearm-roster-player-weight"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-weight") else ""

        academic_year = clean_text(
            player.select_one(
                ".sidearm-roster-player-academic-year"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-academic-year") else ""

        hometown = clean_text(
            player.select_one(
                ".sidearm-roster-player-hometown"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-hometown") else ""

        high_school = clean_text(
            player.select_one(
                ".sidearm-roster-player-highschool"
            ).get_text(" ", strip=True)
        ) if player.select_one(".sidearm-roster-player-highschool") else ""

        profile_link_element = player.select_one(
            ".sidearm-roster-player-name a"
        )

        profile_url = ""
        if profile_link_element and profile_link_element.get("href"):
            profile_url = urljoin(
                "https://colbyathletics.com",
                profile_link_element["href"],
            )

        if not name:
            continue

        record = [
            "Record type: athlete",
            f"Player: {name}",
            f"Jersey number: {jersey}",
            f"Position: {position}",
            f"Academic year: {academic_year}",
            f"Height: {height}",
            f"Weight: {weight}",
            f"Hometown: {hometown}",
            f"High school: {high_school}",
            f"Profile URL: {profile_url}",
        ]

        players.append("\n".join(record))

    return "\n\n".join(players)

def extract_statistics_text(
    soup: BeautifulSoup,
    source: dict,
) -> str:
    records = []

    supported_caption_patterns = [
        # Football
        "individual rushing statistics",
        "individual passing statistics",
        "individual receiving statistics",
        "individual defensive statistics",

        # Basketball
        "overall scoring statistics",
        "individual player averages",
        "category leaders",

        # Soccer
        "individual overall offensive statistics",
        "individual overall goalkeeping statistics",
    ]

    ignored_names = {
        "total",
        "team",
        "opponents",
        "opponent",
    }

    for table in soup.find_all("table"):
        caption = table.find("caption")

        if not caption:
            continue

        table_name = clean_text(
            caption.get_text(" ", strip=True)
        )

        if not table_name:
            continue

        table_name_lower = table_name.lower()

        if not any(
            pattern in table_name_lower
            for pattern in supported_caption_patterns
        ):
            continue

        headers = [
            clean_text(header.get_text(" ", strip=True))
            for header in table.select("thead th")
        ]

        if not headers:
            continue

        for row in table.select("tbody tr"):
            cells = row.find_all(["th", "td"])

            if not cells:
                continue

            row_values = [
                clean_text(cell.get_text(" ", strip=True))
                for cell in cells
            ]
            
            if len(row_values) != len(headers):
                continue

            if len(row_values) < 2:
                continue

            row_data = {}

            for index, value in enumerate(row_values):
                if index >= len(headers):
                    break

                header = headers[index]

                if header:
                    row_data[header] = value

            raw_player = (
                row_data.get("Player")
                or row_data.get("Name")
                or ""
            )

            if not raw_player:
                continue

            # Remove duplicate jersey/name text sometimes added by mobile markup.
            raw_player = clean_text(raw_player)

            # Remove duplicated mobile text:
            # "Civello, Dan 6 Civello, Dan" -> "Civello, Dan"
            duplicate_name_match = re.match(
                r"^(.+?,\s*.+?)\s+#?\d+\s+\1$",
                raw_player,
                re.IGNORECASE,
            )

            if duplicate_name_match:
                raw_player = duplicate_name_match.group(1)

            # Remove a jersey number at the beginning:
            # "#6 Civello, Dan" -> "Civello, Dan"
            raw_player = re.sub(
                r"^\s*#?\d+\s+",
                "",
                raw_player,
            ).strip()

            raw_player = clean_text(raw_player)

            if raw_player.lower() in ignored_names:
                continue

            jersey_number = ""

            number_match = re.search(
                r"#?(\d+)",
                row_values[0],
            )

            if number_match:
                jersey_number = number_match.group(1)

            if "," in raw_player:
                last_name, first_name = raw_player.split(",", 1)
                player_name = (
                    f"{first_name.strip()} {last_name.strip()}"
                )
            else:
                player_name = raw_player

            record_lines = [
                f"Record type: {table_name}",
                f"School: {source.get('school', '')}",
                f"Sport: {source.get('sport', '')}",
                f"Season: {source.get('season', '')}",
                f"Player: {player_name}",
            ]

            if jersey_number:
                record_lines.append(
                    f"Jersey number: {jersey_number}"
                )

            for header, value in row_data.items():
                if header in {
                    "#",
                    "Player",
                    "Name",
                    "Bio Link",
                }:
                    continue

                if not value:
                    continue

                record_lines.append(
                    f"{header}: {value}"
                )

            bio_link = row.select_one(
                'a[href*="/roster/"]'
            )

            if bio_link and bio_link.get("href"):
                profile_url = urljoin(
                    source["url"],
                    bio_link["href"],
                )

                record_lines.append(
                    f"Profile URL: {profile_url}"
                )

            records.append(
                "\n".join(record_lines)
            )

    return "\n\n".join(records)


def scrape_source(source: dict) -> tuple[str, list[dict]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; MuleIntelligenceBot/1.0; educational project)"
        )
    }

    response = requests.get(
        source["url"],
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    page_title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""

    document_type = source.get("document_type")

    if document_type == "roster":
        page_text = extract_roster_text(soup)
    elif document_type == "statistics":
        page_text = extract_statistics_text(
            soup,
            source,
        )
    else:
        page_text = extract_page_text(soup)
    
    if not page_text.strip():
        raise ValueError(
            f"No usable content extracted from "
            f"{source['title']} "
            f"({source['url']})"
        )

    images = []
    if source.get("collect_images", False):
        images = extract_images(soup, response.url, source)

    return page_text, images, page_title

def detect_season(page_text: str, fallback: str = "current") -> str:
    season_range = re.search(
        r"\b(20\d{2}-\d{2})\b",
        page_text,
        re.IGNORECASE,
    )

    if season_range:
        return season_range.group(1)

    single_year = re.search(
        r"\b(20\d{2})\b",
        page_text,
        re.IGNORECASE,
    )

    if single_year:
        return single_year.group(1)

    return fallback

def save_document(
        source: dict, 
        page_text: str, 
        page_title: str,
        ) -> Path:
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    output_path = DOCUMENTS_DIR / f"{source['id']}.txt"

    detected_season = detect_season(
    page_title + "\n" + page_text,
    source.get("season", "current"),
    )
    
    metadata = (
        f"title: {page_title or source['title']}\n"
        f"source_id: {source['id']}\n"
        f"source_url: {source['url']}\n"
        f"school: {source.get('school', '')}\n"
        f"sport: {source.get('sport', '')}\n"
        f"season: {detected_season}\n"
        f"document_type: {source.get('document_type', '')}\n"
        f"date_accessed: {datetime.now().strftime('%Y-%m-%d')}\n"
        "\n"
        "CONTENT:\n"
    )

    output_path.write_text(
        metadata + page_text,
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    sources_path = ROOT_DIR / "sources.json"

    sources = json.loads(
        sources_path.read_text(encoding="utf-8")
    )

    all_images = []
    failures = []

    for source in sources:
        print(f"Scraping: {source['title']}")

        try:
            page_text, images, page_title = scrape_source(source)
            output_path = save_document(source, page_text, page_title)

            all_images.extend(images)

            print(f"Saved: {output_path}")
            print(f"Text length: {len(page_text)} characters")
            print(f"Images found: {len(images)}")

        except Exception as error:
            stale_document_path = (
                DOCUMENTS_DIR / f"{source['id']}.txt"
            )

            if stale_document_path.exists():
                stale_document_path.unlink()
                print(
                    f"Removed stale document: "
                    f"{stale_document_path}"
                )

            failures.append(
                f"{source['title']}: {error}"
            )

            print(f"Failed: {error}")

    MEDIA_DIR.mkdir(exist_ok=True)

    IMAGE_METADATA_PATH.write_text(
        json.dumps(all_images, indent=2),
        encoding="utf-8",
    )

    print(f"Saved image metadata: {IMAGE_METADATA_PATH}")

    if failures:
        print()
        print("The following sources failed:")

        for failure in failures:
            print(f"- {failure}")

        raise RuntimeError(
            f"{len(failures)} source(s) failed during scraping."
        )

if __name__ == "__main__":
    main()