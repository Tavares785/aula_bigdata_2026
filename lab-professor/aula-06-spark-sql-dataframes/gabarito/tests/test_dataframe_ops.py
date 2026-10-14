import os
import sys

import pytest
from pyspark.sql import SparkSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dataframe_ops import (
    filter_high_value_sales,
    total_revenue_by_category,
    join_orders_with_customers,
    top_n_customers_by_spend,
)


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]").appName("aula06-tests").getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def sales_df(spark):
    data = [
        ("eletronicos", 1500.0),
        ("eletronicos", 200.0),
        ("livros", 80.0),
        ("livros", 40.0),
        ("moveis", 900.0),
    ]
    return spark.createDataFrame(data, ["category", "value"])


@pytest.fixture
def orders_df(spark):
    data = [
        (1, 101, 250.0),
        (2, 102, 100.0),
        (3, 101, 300.0),
        (4, 103, 50.0),
    ]
    return spark.createDataFrame(data, ["order_id", "customer_id", "value"])


@pytest.fixture
def customers_df(spark):
    data = [
        (101, "Ana"),
        (102, "Bruno"),
        (103, "Carla"),
    ]
    return spark.createDataFrame(data, ["customer_id", "customer_name"])


def test_filter_high_value_sales(sales_df):
    result = filter_high_value_sales(sales_df, 500.0).collect()
    values = sorted([row["value"] for row in result])
    assert values == [900.0, 1500.0]


def test_filter_high_value_sales_no_matches(sales_df):
    result = filter_high_value_sales(sales_df, 5000.0).collect()
    assert result == []


def test_total_revenue_by_category(sales_df):
    result = {row["category"]: row["total_revenue"] for row in total_revenue_by_category(sales_df).collect()}
    assert result == {"eletronicos": 1700.0, "livros": 120.0, "moveis": 900.0}


def test_total_revenue_by_category_ordered_desc(sales_df):
    rows = total_revenue_by_category(sales_df).collect()
    revenues = [row["total_revenue"] for row in rows]
    assert revenues == sorted(revenues, reverse=True)


def test_join_orders_with_customers(orders_df, customers_df):
    result = join_orders_with_customers(orders_df, customers_df).collect()
    assert len(result) == 4
    row = [r for r in result if r["order_id"] == 1][0]
    assert row["customer_name"] == "Ana"
    assert row["value"] == 250.0


def test_top_n_customers_by_spend(orders_df, customers_df):
    result = top_n_customers_by_spend(orders_df, customers_df, 2).collect()
    assert len(result) == 2
    assert result[0]["customer_name"] == "Ana"
    assert result[0]["total_spend"] == 550.0
    assert result[1]["customer_name"] == "Bruno"
