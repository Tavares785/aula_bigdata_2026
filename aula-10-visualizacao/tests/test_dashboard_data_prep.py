import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dashboard_data_prep import (
    aggregate_daily_totals,
    top_categories,
    compute_moving_average,
)

RECORDS = [
    {"date": "2026-01-01", "category": "eletronicos", "value": 100.0},
    {"date": "2026-01-01", "category": "livros", "value": 20.0},
    {"date": "2026-01-02", "category": "eletronicos", "value": 300.0},
    {"date": "2026-01-02", "category": "moveis", "value": 150.0},
    {"date": "2026-01-03", "category": "livros", "value": 40.0},
]


def test_aggregate_daily_totals():
    result = aggregate_daily_totals(RECORDS)
    assert result == {
        "2026-01-01": 120.0,
        "2026-01-02": 450.0,
        "2026-01-03": 40.0,
    }


def test_aggregate_daily_totals_is_sorted_by_date():
    result = aggregate_daily_totals(RECORDS)
    assert list(result.keys()) == ["2026-01-01", "2026-01-02", "2026-01-03"]


def test_aggregate_daily_totals_empty():
    assert aggregate_daily_totals([]) == {}


def test_top_categories():
    result = top_categories(RECORDS, 2)
    assert result == [("eletronicos", 400.0), ("moveis", 150.0)]


def test_top_categories_n_greater_than_available():
    result = top_categories(RECORDS, 10)
    assert len(result) == 3
    assert result[0] == ("eletronicos", 400.0)


def test_compute_moving_average_window_1():
    result = compute_moving_average([1, 2, 3, 4], window=1)
    assert result == [1.0, 2.0, 3.0, 4.0]


def test_compute_moving_average_window_3():
    result = compute_moving_average([1, 2, 3, 4, 5], window=3)
    assert result == [1.0, 1.5, 2.0, 3.0, 4.0]


def test_compute_moving_average_window_larger_than_list():
    result = compute_moving_average([2, 4], window=5)
    assert result == [2.0, 3.0]
