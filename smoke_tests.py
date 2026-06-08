from rag_answer import retrieve


TEST_CASES = [
    {
        "name": "Roster retrieval",
        "query": "What position does Sean Trinder play?",
        "expected_document_type": "roster",
        "required_terms": ["Sean Trinder"],
        "minimum_results": 1,
    },
    {
        "name": "Schedule retrieval",
        "query": "When does Colby football play Bowdoin?",
        "expected_document_type": "schedule",
        "required_terms": ["Bowdoin College"],
        "minimum_results": 1,
    },
    {
        "name": "Statistics retrieval",
        "query": "Who led Colby football in receiving yards?",
        "expected_document_type": "statistics",
        "required_terms": [
            "Individual Receiving Statistics",
            "YDS:",
        ],
        "minimum_results": 2,
    },
]


REQUIRED_METADATA_FIELDS = [
    "title",
    "source_id",
    "source_url",
    "school",
    "sport",
    "season",
    "document_type",
]


def validate_metadata(
    test_name: str,
    retrieved: list[dict],
) -> list[str]:
    errors = []

    for index, item in enumerate(retrieved, start=1):
        metadata = item.get("metadata", {})

        for field in REQUIRED_METADATA_FIELDS:
            value = metadata.get(field)

            if value is None or str(value).strip() == "":
                errors.append(
                    f"{test_name}: result {index} is missing metadata field '{field}'"
                )

    return errors


def validate_test_case(test: dict) -> list[str]:
    errors = []

    name = test["name"]
    query = test["query"]

    print()
    print("=" * 70)
    print(f"TEST: {name}")
    print(f"QUERY: {query}")
    print("=" * 70)

    try:
        retrieved = retrieve(query)
    except Exception as error:
        return [
            f"{name}: retrieval raised an exception: {error}"
        ]

    if not retrieved:
        return [
            f"{name}: retrieval returned no results"
        ]

    minimum_results = test.get("minimum_results", 1)

    if len(retrieved) < minimum_results:
        errors.append(
            f"{name}: expected at least {minimum_results} result(s), "
            f"but received {len(retrieved)}"
        )

    errors.extend(
        validate_metadata(
            test_name=name,
            retrieved=retrieved,
        )
    )

    expected_document_type = test.get(
        "expected_document_type"
    )

    retrieved_types = {
        item.get("metadata", {})
        .get("document_type", "")
        .lower()
        for item in retrieved
    }

    if (
        expected_document_type
        and expected_document_type.lower()
        not in retrieved_types
    ):
        errors.append(
            f"{name}: expected a '{expected_document_type}' result, "
            f"but retrieved document types were {sorted(retrieved_types)}"
        )

    combined_text = "\n".join(
        item.get("text", "")
        for item in retrieved
    ).lower()

    for required_term in test.get(
        "required_terms",
        [],
    ):
        if required_term.lower() not in combined_text:
            errors.append(
                f"{name}: required term not found: '{required_term}'"
            )

    if errors:
        print("FAIL")

        for error in errors:
            print(f"- {error}")
    else:
        print("PASS")
        print(
            f"Retrieved {len(retrieved)} result(s) "
            f"with document types: {sorted(retrieved_types)}"
        )

    return errors


def main() -> None:
    all_errors = []

    for test in TEST_CASES:
        all_errors.extend(
            validate_test_case(test)
        )

    print()
    print("=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)

    if all_errors:
        print(
            f"{len(all_errors)} issue(s) found:"
        )

        for error in all_errors:
            print(f"- {error}")

        raise SystemExit(1)

    print(
        f"All {len(TEST_CASES)} smoke tests passed."
    )


if __name__ == "__main__":
    main()

