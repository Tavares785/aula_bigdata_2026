import os
import sys
from datetime import datetime

import pytest
from pyspark.sql import SparkSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from stream_aggregation import windowed_event_counts, windowed_revenue_sum


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]").appName("aula03-tests").getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def events_df(spark):
    # Todos os eventos caem dentro de duas janelas de 10 segundos:
    # 10:00:00-10:00:10 e 10:00:10-10:00:20
    rows = [
        (datetime(2026, 1, 1, 10, 0, 1), "compra", 100.0),
        (datetime(2026, 1, 1, 10, 0, 5), "compra", 50.0),
        (datetime(2026, 1, 1, 10, 0, 8), "devolucao", 20.0),
        (datetime(2026, 1, 1, 10, 0, 12), "compra", 200.0),
    ]
    return spark.createDataFrame(rows, ["event_time", "category", "amount"])


def test_windowed_event_counts_columns(events_df):
    result = windowed_event_counts(events_df)
    assert set(result.columns) == {"window_start", "window_end", "category", "count"}


def test_windowed_event_counts_values(events_df):
    result = windowed_event_counts(events_df).collect()
    counts = {(row["category"], row["count"]) for row in result}
    assert ("compra", 2) in counts  # janela 10:00:00-10:00:10
    assert ("devolucao", 1) in counts
    assert ("compra", 1) in counts  # janela 10:00:10-10:00:20


def test_windowed_revenue_sum_total(events_df):
    result = windowed_revenue_sum(events_df).collect()
    total = sum(row["total_amount"] for row in result)
    assert total == 370.0


def test_windowed_revenue_sum_two_windows(events_df):
    result = windowed_revenue_sum(events_df).collect()
    assert len(result) == 2
    amounts = sorted(row["total_amount"] for row in result)
    assert amounts == [170.0, 200.0]
