import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kafka_event_parser import parse_kafka_message, is_valid_event, filter_valid_events

VALID_JSON = (
    '{"event_id": "e1", "event_time": "2026-01-01T10:00:00", '
    '"category": "compra", "amount": 50.0}'
)


def test_parse_kafka_message_valid():
    result = parse_kafka_message(VALID_JSON)
    assert result["event_id"] == "e1"
    assert result["amount"] == 50.0


def test_parse_kafka_message_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_kafka_message("isto nao e json {{{")


def test_parse_kafka_message_missing_fields_raises():
    with pytest.raises(ValueError):
        parse_kafka_message('{"event_id": "e1"}')


def test_parse_kafka_message_non_object_raises():
    with pytest.raises(ValueError):
        parse_kafka_message("[1, 2, 3]")


def test_is_valid_event_true():
    event = {
        "event_id": "e1",
        "event_time": "2026-01-01T10:00:00",
        "category": "compra",
        "amount": 10.0,
    }
    assert is_valid_event(event) is True


def test_is_valid_event_missing_field():
    event = {"event_id": "e1", "event_time": "x", "category": "compra"}
    assert is_valid_event(event) is False


def test_is_valid_event_negative_amount():
    event = {
        "event_id": "e1",
        "event_time": "x",
        "category": "compra",
        "amount": -5.0,
    }
    assert is_valid_event(event) is False


def test_is_valid_event_non_numeric_amount():
    event = {
        "event_id": "e1",
        "event_time": "x",
        "category": "compra",
        "amount": "cinquenta",
    }
    assert is_valid_event(event) is False


def test_filter_valid_events():
    events = [
        {"event_id": "e1", "event_time": "x", "category": "a", "amount": 10.0},
        {"event_id": "e2", "event_time": "x", "category": "b", "amount": -1.0},
        {"event_id": "e3", "event_time": "x", "category": "c"},
    ]
    result = filter_valid_events(events)
    assert len(result) == 1
    assert result[0]["event_id"] == "e1"
