import json
from pathlib import Path

import gradio as gr

from rag_answer import generate_answer, retrieve

CUSTOM_CSS = """
:root {
    --colby-blue: #002878;
    --colby-blue-dark: #001a52;
    --colby-light: #f4f7fb;
    --colby-border: #d8e0ee;
    --text-dark: #172033;
}

/* Page background */
.gradio-container {
    background: var(--colby-light) !important;
    color: var(--text-dark) !important;
}

/* Hero banner */
#hero {
    background: linear-gradient(135deg, var(--colby-blue-dark), var(--colby-blue));
    padding: 32px 20px;
    text-align: center;
    border-radius: 18px;
    margin-bottom: 18px;
}

#hero,
#hero * {
    color: white !important;
}

/* Main panels */
.panel {
    background: white !important;
    border: 1px solid var(--colby-border) !important;
    border-radius: 16px !important;
    padding: 18px !important;
    box-shadow: 0 8px 24px rgba(0, 40, 120, 0.08) !important;
}

/* Force readable text everywhere outside hero */
body,
.gradio-container,
.gradio-container label,
.gradio-container p,
.gradio-container span,
.gradio-container div,
.gradio-container textarea,
.gradio-container input,
.gradio-container button,
.gradio-container .markdown,
.gradio-container .prose,
.gradio-container .prose *,
.gradio-container [data-testid="markdown"],
.gradio-container [data-testid="markdown"] * {
    color: var(--text-dark) !important;
}

/* Re-apply white only inside hero and primary button */
#hero,
#hero *,
.primary-button,
.primary-button * {
    color: white !important;
}

/* Inputs */
textarea,
input {
    background: white !important;
    color: var(--text-dark) !important;
    border: 1px solid var(--colby-border) !important;
}

textarea::placeholder,
input::placeholder {
    color: #6b7280 !important;
}

/* Buttons */
.primary-button {
    background: var(--colby-blue) !important;
    border-color: var(--colby-blue) !important;
}

.primary-button:hover {
    background: var(--colby-blue-dark) !important;
    border-color: var(--colby-blue-dark) !important;
}

/* Clear button */
button {
    background: white !important;
    color: var(--text-dark) !important;
    border: 1px solid var(--colby-border) !important;
}

.primary-button {
    background: var(--colby-blue) !important;
    color: white !important;
}

/* Links */
a {
    color: var(--colby-blue) !important;
}

/* Hide footer */
footer {
    display: none !important;
}
"""

ROOT_DIR = Path(__file__).parent
IMAGE_METADATA_PATH = ROOT_DIR / "media" / "image_metadata.json"


def load_image_metadata() -> list[dict]:
    if not IMAGE_METADATA_PATH.exists():
        return []

    return json.loads(
        IMAGE_METADATA_PATH.read_text(encoding="utf-8")
    )


IMAGE_METADATA = load_image_metadata()


def get_relevant_image(retrieved: list[dict]) -> str | None:
    if not retrieved:
        return None

    best_source_id = retrieved[0]["metadata"].get("source_id", "")

    for image in IMAGE_METADATA:
        if image.get("source_id") != best_source_id:
            continue

        if image.get("image_type") == "logo":
            continue

        image_url = image.get("image_url")

        if image_url:
            return image_url

    return None


def format_sources(retrieved: list[dict]) -> str:
    lines = []
    seen = set()

    for index, item in enumerate(retrieved, start=1):
        metadata = item["metadata"]
        distance = item["distance"]

        if distance > 0.42:
            continue

        title = metadata.get("title", "")
        url = metadata.get("source_url", "")
        season = metadata.get("season", "")
        sport = metadata.get("sport", "")

        source_key = (title, url)

        if source_key in seen:
            continue

        seen.add(source_key)

        lines.append(
            f"**[Source {index}] {title}**  \n"
            f"Sport: {sport}  \n"
            f"Season: {season}  \n"
            f"{url}"
        )

    if not lines and retrieved:
        metadata = retrieved[0]["metadata"]

        lines.append(
            f"**[Source 1] {metadata.get('title', '')}**  \n"
            f"Sport: {metadata.get('sport', '')}  \n"
            f"Season: {metadata.get('season', '')}  \n"
            f"{metadata.get('source_url', '')}"
        )

    return "\n\n---\n\n".join(lines)


def answer_for_interface(
    question: str,
) -> tuple[str, str, str | None]:
    question = question.strip()

    if not question:
        return (
            "Enter a Colby Athletics question.",
            "",
            None,
        )

    retrieved = retrieve(question)
    answer = generate_answer(question, retrieved)
    sources = format_sources(retrieved)
    image_url = get_relevant_image(retrieved)

    return answer, sources, image_url


with gr.Blocks(
    title="Mule Intelligence",
) as demo:
    gr.Markdown(
        """
# Mule Intelligence

**Live, citation-first answers for Colby Athletics**

Explore schedules, rosters, results, players, and season information
from official Colby sources.
""",
        elem_id="hero",
    )

    with gr.Column(elem_classes="panel"):
        question_input = gr.Textbox(
            label="Ask Mule Intelligence",
            placeholder="When does Colby football play Bowdoin in 2026?",
            lines=2,
        )

        with gr.Row():
            submit_button = gr.Button(
                "Ask Mule Intelligence",
                variant="primary",
                elem_classes="primary-button",
            )

            clear_button = gr.Button("Clear")

    with gr.Row():
        with gr.Column(scale=2):
            with gr.Column(elem_classes="panel"):
                answer_output = gr.Markdown(
                    label="Answer"
                )

            with gr.Column(elem_classes="panel"):
                sources_output = gr.Markdown(
                    label="Sources"
                )

        with gr.Column(scale=1):
            with gr.Column(elem_classes="panel"):
                image_output = gr.Image(
                    label="Relevant official image",
                    type="filepath",
                )

    gr.Examples(
        examples=[
            ["When does Colby football play Bowdoin in 2026?"],
            ["What position does Sean Trinder play?"],
            ["What was the men's basketball overall record in 2025-26?"],
            ["Who will be Colby's best football player next season?"],
        ],
        inputs=question_input,
    )

    submit_button.click(
        fn=answer_for_interface,
        inputs=question_input,
        outputs=[
            answer_output,
            sources_output,
            image_output,
        ],
    )

    question_input.submit(
        fn=answer_for_interface,
        inputs=question_input,
        outputs=[
            answer_output,
            sources_output,
            image_output,
        ],
    )

    clear_button.click(
        fn=lambda: ("", "", "", None),
        inputs=[],
        outputs=[
            question_input,
            answer_output,
            sources_output,
            image_output,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
        )