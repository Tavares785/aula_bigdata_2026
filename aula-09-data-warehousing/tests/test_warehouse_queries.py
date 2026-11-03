import os
import sys

import pytest
from pyspark.sql import SparkSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from warehouse_queries import (
    register_sales_table,
    total_revenue_by_region,
    top_n_products,
    regions_above_threshold,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("aula09-tests")
        .enableHiveSupport()
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture(autouse=True)
def sales_table(spark):
    rows = [
        ("sul", "notebook", 5000.0),
        ("sul", "mouse", 100.0),
        ("sudeste", "notebook", 8000.0),
        ("sudeste", "teclado", 300.0),
        ("nordeste", "mouse", 150.0),
    ]
    register_sales_table(spark, rows)


def test_total_revenue_by_region(spark):
    result = total_revenue_by_region(spark)
    assert result == {"sudeste": 8300.0, "sul": 5100.0, "nordeste": 150.0}


def test_top_n_products(spark):
    result = top_n_products(spark, 2)
    assert result == ["notebook", "teclado"]


def test_top_n_products_n_equals_1(spark):
    result = top_n_products(spark, 1)
    assert result == ["notebook"]


def test_regions_above_threshold(spark):
    result = regions_above_threshold(spark, 200.0)
    assert result == ["sudeste", "sul"]


def test_regions_above_threshold_none_qualify(spark):
    result = regions_above_threshold(spark, 100000.0)
    assert result == []
