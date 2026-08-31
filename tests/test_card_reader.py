from datetime import date

import pytest

from simulator.card.driver_card import DriverCard
from simulator.card.reader import CardReader


def create_card(card_number="CARD-001"):
    return DriverCard(
        card_number=card_number,
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_reader_starts_without_card():
    reader = CardReader()

    assert reader.is_card_inserted() is False
    assert reader.read_card() is None


def test_reader_can_insert_card():
    reader = CardReader()
    card = create_card()

    reader.insert_card(card)

    assert reader.is_card_inserted() is True
    assert reader.read_card() is card


def test_reader_can_remove_card():
    reader = CardReader()
    card = create_card()

    reader.insert_card(card)
    reader.remove_card()

    assert reader.is_card_inserted() is False
    assert reader.read_card() is None


def test_reader_can_insert_card_after_removal():
    reader = CardReader()

    first_card = create_card("CARD-001")
    second_card = create_card("CARD-002")

    reader.insert_card(first_card)
    reader.remove_card()
    reader.insert_card(second_card)

    assert reader.read_card() is second_card


def test_reader_preserves_inserted_card():
    reader = CardReader()
    card = create_card()

    reader.insert_card(card)

    assert reader.read_card() is card
    assert reader.read_card() is card


def test_reader_does_not_allow_replacing_inserted_card():
    reader = CardReader()

    first_card = create_card("CARD-001")
    second_card = create_card("CARD-002")

    reader.insert_card(first_card)

    with pytest.raises(ValueError):
        reader.insert_card(second_card)

    assert reader.read_card() is first_card


def test_reader_remove_is_safe_when_empty():
    reader = CardReader()

    reader.remove_card()

    assert reader.is_card_inserted() is False
    assert reader.read_card() is None