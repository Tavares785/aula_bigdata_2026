"""Fixtures e implementacoes de referencia compartilhadas pelos testes do Job_ML.

O arquivo `job/ml_job.py` mantem as tres funcoes (`build_feature_vector`,
`train_classifier`, `evaluate_accuracy`) no estado TODO — elas levantam
`NotImplementedError` ate o aluno completa-las. Para que os testes de
propriedade possam VALIDAR o comportamento esperado (as Correctness Properties
do design) sem depender de uma implementacao do aluno, este `conftest.py`
fornece IMPLEMENTACOES DE REFERENCIA das tres funcoes, exatamente como descrito
na secao de design "Job_ML / funcoes do aluno".

Os testes importam estas referencias (sob os nomes `build_feature_vector`,
`train_classifier`, `evaluate_accuracy` e tambem os aliases `ref_*`) em vez das
funcoes TODO do `ml_job.py`, de modo que PASSEM sem alterar o modulo de
exercicio.

Tambem expoe:
  - a fixture `spark`: uma `SparkSession` local (`master("local[1]")`) de escopo
    de sessao, reutilizada por todos os testes;
  - a fixture `feature_builder`: a referencia de `build_feature_vector`.
"""

import pytest

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Mesmas features declaradas em job/ml_job.py (FEATURES).
FEATURES = ["meses_ativo", "gasto_mensal", "chamados_suporte", "atraso_pagamento"]


# ---------------------------------------------------------------------------
# Implementacoes de REFERENCIA (gabarito) das tres funcoes do Job_ML.
# Espelham a secao "Job_ML" do design.md. NAO modificam job/ml_job.py.
# ---------------------------------------------------------------------------
def build_feature_vector(df):
    """Referencia de `build_feature_vector` (Property 1).

    Monta as colunas de `FEATURES` em uma unica coluna vetorial `features`,
    preservando todas as colunas originais e a contagem de linhas.
    """
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    return assembler.transform(df)


def train_classifier(treino):
    """Referencia de `train_classifier` (Property 2).

    Treina APENAS um `LogisticRegression` sobre as colunas `features`/`label`
    e retorna o modelo treinado (`.fit(treino)`).
    """
    lr = LogisticRegression(featuresCol="features", labelCol="label")
    return lr.fit(treino)


def evaluate_accuracy(previsoes):
    """Referencia de `evaluate_accuracy` (Property 3 e Property 4).

    Calcula a acuracia comparando `prediction` com `label` via
    `MulticlassClassificationEvaluator`, retornando um float em [0, 1].
    """
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    return float(evaluator.evaluate(previsoes))


# Aliases explicitos `ref_*` para quem prefere deixar claro, no import, que se
# trata da implementacao de referencia (gabarito) e nao da funcao TODO.
ref_build_feature_vector = build_feature_vector
ref_train_classifier = train_classifier
ref_evaluate_accuracy = evaluate_accuracy


@pytest.fixture(scope="session")
def spark():
    """SparkSession local de escopo de sessao para os testes (sem Glue)."""
    session = (
        SparkSession.builder.appName("aula07-ml-tests")
        .master("local[1]")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def feature_builder():
    """Referencia de `build_feature_vector`, exposta como fixture."""
    return build_feature_vector
