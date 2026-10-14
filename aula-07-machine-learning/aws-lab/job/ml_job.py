"""Job_ML — pipeline de classificacao de churn com Spark MLlib (AWS Glue).

Este modulo roda como um Glue Job (`glueetl`) na AWS, mas tambem precisa ser
IMPORTAVEL e COMPILAVEL em ambiente local (sem o SDK do Glue), para que o aluno
teste as funcoes TODO antes de subir para a nuvem (Req 8.5).

Fluxo do `main()` (Req 9.1-9.3):
  1. Le o CSV de churn do S3 (`--INPUT`) e renomeia a coluna `churn` -> `label`.
  2. Monta o vetor de features (`build_feature_vector`).
  3. Divide treino/teste 70/30 com `seed=42`.
  4. Treina o classificador (`train_classifier`) e gera previsoes.
  5. Avalia acuracia (`evaluate_accuracy`) e AUC-ROC (no proprio fluxo).
  6. Imprime as metricas no stdout (vao para o CloudWatch).
  7. Grava `output/metrics` e `output/predictions` no S3 (`--OUTPUT`).

As tres funcoes `build_feature_vector`, `train_classifier` e `evaluate_accuracy`
sao implementadas pelo aluno (tarefa 3.2) — aqui ficam apenas como placeholders
que levantam `NotImplementedError`.
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

# O SDK do AWS Glue so existe no ambiente gerenciado da AWS. Importamos dentro
# de try/except para que o modulo continue importavel/compilavel localmente
# (sem o SDK do Glue), permitindo testar as funcoes TODO antes de subir (Req 8.5).
try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:  # ambiente local sem o SDK do Glue
    getResolvedOptions = None
    GlueContext = None
    Job = None

# Colunas de entrada usadas para montar o vetor de features (Req 1.2 / 8.1).
FEATURES = ["meses_ativo", "gasto_mensal", "chamados_suporte", "atraso_pagamento"]


# ---------------------------------------------------------------------------
# Funcoes do aluno (TODO) — placeholders temporarios.
# A tarefa 3.2 refina estas tres funcoes com as docstrings/mensagens exatas.
# O `main()` abaixo ja as CHAMA; por isso elas precisam existir para o modulo
# compilar nesta etapa.
# ---------------------------------------------------------------------------
def build_feature_vector(df):
    """
    TODO 1:
    O MLlib exige que as features de entrada de um modelo estejam
    reunidas em UMA UNICA coluna do tipo vetor, chamada por convencao de
    "features". Use `VectorAssembler` para transformar as colunas
    listadas na constante `FEATURES` (meses_ativo, gasto_mensal,
    chamados_suporte, atraso_pagamento) em uma nova coluna "features", e
    retorne o DataFrame resultante (com todas as colunas originais + a
    nova coluna "features").
    """
    raise NotImplementedError("TODO 1: implemente build_feature_vector")


def train_classifier(treino):
    """
    TODO 2:
    Treine um classificador de Regressao Logistica (`LogisticRegression`
    do `pyspark.ml.classification`) usando a coluna "features" (ja
    montada por `build_feature_vector`) e a coluna de rotulo "label".
    Treine APENAS o LogisticRegression e retorne o MODELO TREINADO (ou
    seja, o resultado de `.fit(treino)`, nao o estimador em si).
    """
    raise NotImplementedError("TODO 2: implemente train_classifier")


def evaluate_accuracy(previsoes):
    """
    TODO 3:
    Receba o DataFrame `previsoes` (ja com as colunas "prediction" e
    "label") e calcule a ACURACIA dessas previsoes usando
    `MulticlassClassificationEvaluator` (metricName="accuracy"),
    comparando a coluna "prediction" com a coluna "label". Retorne a
    acuracia como um numero float entre 0 e 1.
    """
    raise NotImplementedError("TODO 3: implemente evaluate_accuracy")


# ---------------------------------------------------------------------------
# Orquestracao do Glue Job (Req 9.1-9.3).
# ---------------------------------------------------------------------------
def main():
    """Orquestra o pipeline de ML de churn dentro do Glue Job."""
    # Resolve os argumentos passados pelo Glue (--JOB_NAME, --INPUT, --OUTPUT).
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "INPUT", "OUTPUT"])

    # Inicializa o contexto do Spark/Glue e o controle do Job.
    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # 1. Le o CSV de churn do S3 e renomeia a coluna churn -> label.
    df = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv(args["INPUT"])
        .withColumnRenamed("churn", "label")
    )

    # 2. Monta o vetor de features e divide treino/teste (split fixo com seed=42).
    dados = build_feature_vector(df)
    treino, teste = dados.randomSplit([0.7, 0.3], seed=42)

    # 3. Treina o classificador e gera previsoes sobre o teste.
    modelo = train_classifier(treino)
    previsoes = modelo.transform(teste)

    # 4. Metricas: acuracia (funcao do aluno) e AUC-ROC (calculada aqui no fluxo).
    acc = evaluate_accuracy(previsoes)
    auc = BinaryClassificationEvaluator(
        labelCol="label", metricName="areaUnderROC"
    ).evaluate(previsoes)

    # 5. Imprime as metricas no stdout do driver (aparecem no CloudWatch).
    print("=== Metricas (churn) ===")
    print(f"accuracy,{acc:.4f}")
    print(f"areaUnderROC,{auc:.4f}")

    # 6. Grava metricas e amostra de previsoes no S3, a partir do prefixo --OUTPUT.
    out = args["OUTPUT"].rstrip("/")

    metrics = spark.createDataFrame(
        [("accuracy", float(acc)), ("areaUnderROC", float(auc))],
        ["metrica", "valor"],
    )
    metrics.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{out}/metrics"
    )

    amostra = previsoes.select(*FEATURES, "label", "prediction")
    amostra.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{out}/predictions"
    )

    print(f"Resultado gravado em: {out}/metrics e {out}/predictions")

    # 7. Finaliza o Job do Glue (marca o run como concluido).
    job.commit()


if __name__ == "__main__":
    main()
