"""Implementacao de REFERENCIA compartilhada do Job_ML (`job/ml_job.py`).

No `job/ml_job.py` as tres funcoes do aluno (`build_feature_vector`,
`train_classifier`, `evaluate_accuracy`) estao no estado TODO e levantam
`NotImplementedError` (Req 8.4). Para que os testes de PROPRIEDADE das
Correctness Properties PASSEM agora — sem alterar o `ml_job.py` de exercicio —
este modulo fornece a implementacao de REFERENCIA das tres funcoes, exatamente
como descrito no design.md ("Implementacao esperada"):

  - build_feature_vector: VectorAssembler(inputCols=FEATURES, outputCol="features").transform(df)
  - train_classifier:     LogisticRegression(featuresCol="features", labelCol="label").fit(treino)
  - evaluate_accuracy:    MulticlassClassificationEvaluator(..., metricName="accuracy").evaluate(previsoes)

Fica num modulo proprio (e nao dentro do `conftest.py`) para poder ser importado
de forma inequivoca pelos arquivos de teste (`from ml_reference import ...`),
evitando a ambiguidade de importar pelo nome especial `conftest`.
"""

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Colunas de features do dataset de churn (espelha FEATURES em job/ml_job.py).
FEATURES = ["meses_ativo", "gasto_mensal", "chamados_suporte", "atraso_pagamento"]


def ref_build_feature_vector(df):
    """Monta a coluna vetorial `features` a partir de FEATURES (referencia)."""
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    return assembler.transform(df)


def ref_train_classifier(treino):
    """Treina e retorna um LogisticRegressionModel (referencia, APENAS LR)."""
    lr = LogisticRegression(featuresCol="features", labelCol="label")
    return lr.fit(treino)


def ref_evaluate_accuracy(previsoes):
    """Calcula a acuracia (float em [0,1]) das previsoes (referencia)."""
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    return evaluator.evaluate(previsoes)
