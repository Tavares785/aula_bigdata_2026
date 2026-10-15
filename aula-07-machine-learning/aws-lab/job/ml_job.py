"""Pipeline de classificacao de churn com Spark MLlib no AWS Glue.

Trabalho Final - Aula 07 - Machine Learning com Big Data
RA: 6325028

Fluxo:
1. Leitura do dataset no S3.
2. Preparacao das features.
3. Divisao dos dados em treino e teste.
4. Treinamento com regressao logistica.
5. Avaliacao da acuracia e AUC-ROC.
6. Gravacao dos resultados no S3.
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import (
    MulticlassClassificationEvaluator,
    BinaryClassificationEvaluator,
)

# Permite importar o modulo localmente sem o SDK do AWS Glue.
try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:
    getResolvedOptions = None
    GlueContext = None
    Job = None


# Colunas utilizadas pelo modelo.
FEATURES = [
    "meses_ativo",
    "gasto_mensal",
    "chamados_suporte",
    "atraso_pagamento",
]


# ---------------------------------------------------------
# TODO 1 - Preparacao das features
# ---------------------------------------------------------

def build_feature_vector(df):
    """Agrupa as colunas de entrada em um vetor de features."""

    assembler = VectorAssembler(
        inputCols=FEATURES,
        outputCol="features"
    )

    return assembler.transform(df)


# ---------------------------------------------------------
# TODO 2 - Treinamento do classificador
# ---------------------------------------------------------

def train_classifier(treino):
    """Treina um modelo de regressao logistica."""

    lr = LogisticRegression(
        featuresCol="features",
        labelCol="label"
    )

    modelo = lr.fit(treino)

    return modelo


# ---------------------------------------------------------
# TODO 3 - Avaliacao da acuracia
# ---------------------------------------------------------

def evaluate_accuracy(previsoes):
    """Calcula a acuracia das previsoes."""

    avaliador = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    )

    acuracia = avaliador.evaluate(previsoes)

    return float(acuracia)


# ---------------------------------------------------------
# Execucao principal do AWS Glue Job
# ---------------------------------------------------------

def main():
    """Executa o pipeline de Machine Learning."""

    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "INPUT", "OUTPUT"]
    )

    # Inicializacao do Spark e AWS Glue.
    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session

    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # Leitura dos dados do S3.
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(args["INPUT"])
        .withColumnRenamed("churn", "label")
    )

    # Preparacao das features.
    dados = build_feature_vector(df)

    # Divisao: 70% treinamento e 30% teste.
    treino, teste = dados.randomSplit(
        [0.7, 0.3],
        seed=42
    )

    # Treinamento.
    modelo = train_classifier(treino)

    # Geracao das previsoes.
    previsoes = modelo.transform(teste)

    # Calculo da acuracia.
    acc = evaluate_accuracy(previsoes)

    # Calculo da area sob a curva ROC.
    auc = BinaryClassificationEvaluator(
        labelCol="label",
        metricName="areaUnderROC"
    ).evaluate(previsoes)

    # Exibicao das metricas.
    print("=== Metricas (churn) ===")
    print(f"accuracy,{acc:.4f}")
    print(f"areaUnderROC,{auc:.4f}")

    # Diretorio de saida no S3.
    out = args["OUTPUT"].rstrip("/")

    # Criacao do DataFrame de metricas.
    metrics = spark.createDataFrame(
        [
            ("accuracy", float(acc)),
            ("areaUnderROC", float(auc))
        ],
        ["metrica", "valor"]
    )

    # Gravacao das metricas no S3.
    (
        metrics.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(f"{out}/metrics")
    )

    # Amostra das previsoes.
    amostra = previsoes.select(
        *FEATURES,
        "label",
        "prediction"
    )

    # Gravacao das previsoes no S3.
    (
        amostra.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(f"{out}/predictions")
    )

    print(
        f"Resultado gravado em: "
        f"{out}/metrics e {out}/predictions"
    )

    # Finalizacao do Glue Job.
    job.commit()


if __name__ == "__main__":
    main()
