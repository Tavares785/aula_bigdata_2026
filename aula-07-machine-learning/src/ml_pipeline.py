"""
Aula 07 - Machine Learning com Big Data
Lab: Pipeline basico de classificacao usando Spark MLlib.
"""
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


def build_feature_vector(df, feature_cols):
    """Combina as colunas de entrada em uma coluna vetorial chamada features."""
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    return assembler.transform(df)


def train_classifier(train_df, label_col="label"):
    """Treina e retorna uma Regressao Logistica ajustada aos dados."""
    classifier = LogisticRegression(featuresCol="features", labelCol=label_col)
    return classifier.fit(train_df)


def evaluate_accuracy(model, test_df, label_col="label"):
    """Avalia o modelo no conjunto de teste e retorna a acuracia como float."""
    predictions = model.transform(test_df)
    evaluator = MulticlassClassificationEvaluator(
        labelCol=label_col,
        predictionCol="prediction",
        metricName="accuracy",
    )
    return float(evaluator.evaluate(predictions))
