import os
import sys

import pytest
from pyspark.sql import SparkSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ml_pipeline import build_feature_vector, train_classifier, evaluate_accuracy


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]").appName("aula07-tests").getOrCreate()
    )
    yield session
    session.stop()


def _linearly_separable_rows():
    # label = 1 quando x1 + x2 > 10, senao 0 -- um problema simples e
    # linearmente separavel, ideal para validar o pipeline (nao para
    # avaliar a "inteligencia" do modelo).
    rows = []
    for x1 in range(0, 12, 2):
        for x2 in range(0, 12, 2):
            label = 1.0 if (x1 + x2) > 10 else 0.0
            rows.append((float(x1), float(x2), label))
    return rows


@pytest.fixture
def train_test_dfs(spark):
    rows = _linearly_separable_rows()
    split = int(len(rows) * 0.7)
    train_df = spark.createDataFrame(rows[:split], ["x1", "x2", "label"])
    test_df = spark.createDataFrame(rows[split:], ["x1", "x2", "label"])
    return train_df, test_df


def test_build_feature_vector_adds_features_column(spark):
    df = spark.createDataFrame([(1.0, 2.0)], ["x1", "x2"])
    result = build_feature_vector(df, ["x1", "x2"])
    assert "features" in result.columns


def test_build_feature_vector_preserves_row_count(spark):
    df = spark.createDataFrame([(1.0, 2.0), (3.0, 4.0)], ["x1", "x2"])
    result = build_feature_vector(df, ["x1", "x2"])
    assert result.count() == 2


def test_train_classifier_returns_fitted_model(train_test_dfs):
    train_df, _ = train_test_dfs
    train_df = build_feature_vector(train_df, ["x1", "x2"])
    model = train_classifier(train_df)
    assert hasattr(model, "transform")


def test_pipeline_achieves_good_accuracy(train_test_dfs):
    train_df, test_df = train_test_dfs
    train_df = build_feature_vector(train_df, ["x1", "x2"])
    test_df = build_feature_vector(test_df, ["x1", "x2"])

    model = train_classifier(train_df)
    accuracy = evaluate_accuracy(model, test_df)

    # Problema linearmente separavel: um modelo correto deve acertar
    # praticamente tudo.
    assert accuracy >= 0.8


def test_evaluate_accuracy_is_between_zero_and_one(train_test_dfs):
    train_df, test_df = train_test_dfs
    train_df = build_feature_vector(train_df, ["x1", "x2"])
    test_df = build_feature_vector(test_df, ["x1", "x2"])
    model = train_classifier(train_df)
    accuracy = evaluate_accuracy(model, test_df)
    assert 0.0 <= accuracy <= 1.0
