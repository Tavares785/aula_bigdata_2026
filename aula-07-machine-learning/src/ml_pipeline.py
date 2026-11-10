"""
Aula 07 - Machine Learning com Big Data
Lab: Pipeline basico de classificacao usando Spark MLlib.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


def build_feature_vector(df, feature_cols):
    """
    TODO 1:
    O MLlib exige que as features de entrada de um modelo estejam
    reunidas em UMA UNICA coluna do tipo vetor, chamada por convencao de
    "features". Use `VectorAssembler` para transformar as colunas
    listadas em `feature_cols` (ex: ["x1", "x2"]) em uma nova coluna
    "features", e retorne o DataFrame resultante (com todas as colunas
    originais + a nova coluna "features").
    """
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    return assembler.transform(df)


def train_classifier(train_df, label_col="label"):
    """
    TODO 2:
    Treine um classificador de Regressao Logistica (`LogisticRegression`
    do `pyspark.ml.classification`) usando a coluna "features" (ja
    montada por `build_feature_vector`) e a coluna de rotulo indicada em
    `label_col`. Retorne o MODELO TREINADO (ou seja, o resultado de
    `.fit(train_df)`, nao o estimador em si).
    """
    lr = LogisticRegression(featuresCol="features", labelCol=label_col)
    return lr.fit(train_df)


def evaluate_accuracy(model, test_df, label_col="label"):
    """
    TODO 3:
    Use o `model` ja treinado para gerar previsoes sobre `test_df`
    (`model.transform(test_df)`), e entao calcule a ACURACIA dessas
    previsoes usando `MulticlassClassificationEvaluator` (metricName=
    "accuracy"), comparando a coluna "prediction" com `label_col`.
    Retorne a acuracia como um numero float entre 0 e 1.
    """
    predictions = model.transform(test_df)
    evaluator = MulticlassClassificationEvaluator(
        labelCol=label_col, predictionCol="prediction", metricName="accuracy"
    )
    return float(evaluator.evaluate(predictions))
