import os
import sys

import pytest
from pyspark import SparkContext, SparkConf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rdd_basics import word_count_rdd, filter_and_square_evens, average_by_key


@pytest.fixture(scope="module")
def sc():
    conf = SparkConf().setMaster("local[2]").setAppName("aula05-tests")
    spark_context = SparkContext.getOrCreate(conf)
    yield spark_context
    spark_context.stop()


def test_word_count_basic(sc):
    lines = ["gato rato gato", "rato correu gato"]
    result = word_count_rdd(sc, lines)
    assert result == [("gato", 3), ("rato", 2), ("correu", 1)]


def test_word_count_case_insensitive(sc):
    lines = ["Gato GATO gato"]
    result = word_count_rdd(sc, lines)
    assert result == [("gato", 3)]


def test_word_count_empty_input(sc):
    assert word_count_rdd(sc, []) == []


def test_filter_and_square_evens(sc):
    result = filter_and_square_evens(sc, [1, 2, 3, 4, 5, 6])
    assert result == [4, 16, 36]


def test_filter_and_square_evens_no_evens(sc):
    result = filter_and_square_evens(sc, [1, 3, 5])
    assert result == []


def test_average_by_key(sc):
    pairs = [("a", 10), ("b", 20), ("a", 30), ("b", 40), ("a", 20)]
    result = average_by_key(sc, pairs)
    assert result == {"a": 20.0, "b": 30.0}


def test_average_by_key_single_value(sc):
    result = average_by_key(sc, [("x", 5)])
    assert result == {"x": 5.0}
