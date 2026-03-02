import json
import os
import re

import pytest

QA_DATA_PATH = "data/qa_data.json"


@pytest.fixture
def qa_data():
    """Loads the Q&A data from the JSON file."""
    assert os.path.exists(QA_DATA_PATH), f"File {QA_DATA_PATH} not found"
    with open(QA_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_qa_data_is_list(qa_data):
    """Verifies that the data is a list of items."""
    assert isinstance(qa_data, list)
    assert len(qa_data) > 0


def test_qa_data_count(qa_data):
    """Verifies that the total count matches the expected 206 items."""
    # Note: The website reported 206 hits.
    assert len(qa_data) == 206


def test_entry_schema(qa_data):
    """Verifies the schema of each Q&A entry."""
    required_keys = {"id", "date", "question", "answer", "related_cards"}
    for entry in qa_data:
        assert set(entry.keys()) == required_keys, f"Entry {entry.get('id')} has incorrect keys"
        assert entry["id"].startswith("Q"), f"Entry {entry.get('id')} ID should start with 'Q'"
        assert re.match(r"\d{4}\.\d{2}\.\d{2}", entry["date"]), f"Entry {entry.get('id')} has invalid date format"
        assert isinstance(entry["question"], str) and len(entry["question"]) > 0
        assert isinstance(entry["answer"], str) and len(entry["answer"]) > 0
        assert isinstance(entry["related_cards"], list)


def test_related_cards_well_formed(qa_data):
    """Verifies that related cards have the correct structure."""
    for entry in qa_data:
        for card in entry["related_cards"]:
            assert "card_no" in card
            assert "name" in card
            assert isinstance(card["card_no"], str)
            assert isinstance(card["name"], str)


def test_icon_formatting(qa_data):
    """Verifies that icons are formatted as {{filename|alt}} or {{filename}}."""
    icon_pattern = r"\{\{.*?\.png\|?.*?\}\}"
    found_any_icon = False

    for entry in qa_data:
        # Check both question and answer for icons
        match_q = re.search(icon_pattern, entry["question"])
        match_a = re.search(icon_pattern, entry["answer"])

        if match_q or match_a:
            found_any_icon = True

        # If icons exist, verify they follow the project's standard
        for text in [entry["question"], entry["answer"]]:
            icons = re.findall(r"\{\{(.*?)\}\}", text)
            for icon in icons:
                # Should be filename.png or filename.png|alt
                assert ".png" in icon, f"Possible malformed icon in {entry['id']}: {icon}"

    assert found_any_icon, "No icons were found in the entire dataset (unexpected for 206 entries)"


def test_general_questions_have_no_related_cards(qa_data):
    """Verifies that general orientation/rule questions have empty related_cards."""
    # We know Q1 is about where to buy cards (general)
    q1 = next((item for item in qa_data if item["id"] == "Q1"), None)
    assert q1 is not None
    assert len(q1["related_cards"]) == 0

    # We know Q206 matches Emma Verde (card-specific)
    q206 = next((item for item in qa_data if item["id"] == "Q206"), None)
    assert q206 is not None
    assert len(q206["related_cards"]) > 0
