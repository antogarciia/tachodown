from datetime import date

import pytest

from simulator.card.driver_card import DriverCard
from simulator.card.reader import CardReader
from simulator.device.controller import (
    DeviceController,
    DeviceState,
    InvalidTransition,
)


def create_test_card():
    return DriverCard(
        card_number="TEST-CARD-001",
        driver_id="DRIVER-001",
        issuing_country="ES",
        valid_from=date(2026, 1, 1),
        valid_until=date(2030, 12, 31),
    )


def test_driver_card_is_valid():
    card = create_test_card()

    assert card.is_valid_on(date(2026, 8, 30)) is True


def test_expired_driver_card_is_invalid():
    card = DriverCard(
        card_number="TEST-CARD-002",
        driver_id="DRIVER-002",
        issuing_country="ES",
        valid_from=date(2020, 1, 1),
        valid_until=date(2025, 12, 31),
    )

    assert card.is_valid_on(date(2026, 8, 30)) is False


def test_card_reader_starts_empty():
    reader = CardReader()

    assert reader.is_card_inserted() is False
    assert reader.read_card() is None


def test_card_reader_detects_inserted_card():
    reader = CardReader()
    card = create_test_card()

    reader.insert_card(card)

    assert reader.is_card_inserted() is True
    assert reader.read_card() == card


def test_card_reader_can_remove_card():
    reader = CardReader()
    card = create_test_card()

    reader.insert_card(card)
    reader.remove_card()

    assert reader.is_card_inserted() is False
    assert reader.read_card() is None


def test_device_detects_card():
    reader = CardReader()
    device = DeviceController()
    card = create_test_card()

    reader.insert_card(card)
    device.detect_card(reader.read_card())

    assert device.state == DeviceState.CARD_DETECTED
    assert device.card == card


def test_device_rejects_second_card_detection():
    reader = CardReader()
    device = DeviceController()
    card = create_test_card()

    reader.insert_card(card)
    device.detect_card(reader.read_card())

    with pytest.raises(InvalidTransition):
        device.detect_card(reader.read_card())