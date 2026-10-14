"""acoes_job — DEMO DO PROFESSOR: previsão de direção de ações com Spark MLlib (AWS Glue).

Esta é a DEMO DO PROFESSOR da aula-07. Diferente do Trabalho Final do aluno
(classificação de CHURN), aqui o cenário é a PREVISÃO DE DIREÇÃO DE AÇÕES:
classificação binária de se a ação SOBE (1) ou CAI (0) no dia seguinte, a partir
de features técnicas sintéticas (retornos, médias móveis, volume relativo e
volatilidade). O objetivo é mostrar o MESMO pipeline MLlib + Glue aplicado a
OUTRO domínio, para dar repertório — este script já vem COMPLETO e PRONTO para
rodar, sem TODOs.

Diferença didática extra em relação ao TF: aqui treinamos e comparamos DOIS
classificadores sobre o mesmo conjunto de treino — Regressão Logística e Random
Forest — e imprimimos uma tabela comparativa (acurácia, F1 e AUC-ROC) no stdout
(que vai para o CloudWatch).

Este módulo roda como um Glue Job (`glueetl`) na AWS, mas também é IMPORTÁVEL e
COMPILÁVEL localmente (sem o SDK do Glue), graças ao try/except ImportError.

Fluxo do `main()`:
  1. Lê o CSV de ações do S3 (`--INPUT`) e renomeia a coluna `subiu` -> `label`.
  2. Monta o vetor de features (`VectorAssembler` sobre FEATURES).
  3. Divide treino/teste 70/30 com `seed=42`.
  4. Treina Regressão Logística E Random Forest sobre o MESMO treino.
  5. Para cada modelo: gera previsões e calcula acurácia, F1 e AUC-ROC.
  6. Imprime a tabela comparativa no stdout (vai para o CloudWatch).
  7. Grava `output/metrics` (modelo,metrica,valor) e `output/predictions`
     (amostra do Random Forest) no S3 (`--OUTPUT`).
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import (
    MulticlassClassificationEvaluator,
    BinaryClassificationEvaluator,
)

# O SDK do AWS Glue só existe no ambiente gerenciado da AWS. Importamos dentro
# de try/except para que o módulo continue importável/compilável localmente
# (sem o SDK do Glue), facilitando a validação da demo antes de subir.
try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:  # ambiente local sem o SDK do Glue
    getResolvedOptions = None
    GlueContext = None
    Job = None

# Colunas de entrada (features técnicas sintéticas) usadas para montar o vetor.
# A coluna alvo no CSV chama-se "subiu" (1 = ação subiu no dia seguinte, 0 = caiu)
# e é renomeada para "label" na leitura.
FEATURES = [
    "retorno_1d",
    "retorno_5d",
    "media_movel_5",
    "media_movel_10",
    "volume_rel",
    "volatilidade_5",
]


# ---------------------------------------------------------------------------
# Funções do pipeline (COMPLETAS — esta é a demo pronta do professor).
# ---------------------------------------------------------------------------
def build_feature_vector(df):
    """Monta a coluna vetorial "features" a partir das colunas em FEATURES.

    O MLlib exige que todas as features de entrada estejam reunidas em UMA
    única coluna do tipo vetor (por convenção chamada "features"). Usamos o
    `VectorAssembler` para transformar as colunas técnicas (retornos, médias
    móveis, volume relativo e volatilidade) nessa coluna e retornamos o
    DataFrame resultante (colunas originais + a nova coluna "features").
    """
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    return assembler.transform(df)


def train_logistic_regression(treino):
    """Treina um classificador de Regressão Logística e retorna o modelo treinado."""
    lr = LogisticRegression(featuresCol="features", labelCol="label")
    return lr.fit(treino)


def train_random_forest(treino):
    """Treina um classificador Random Forest e retorna o modelo treinado.

    Usamos uma floresta pequena (50 árvores) — suficiente para a demo e barato
    no Glue.
    """
    rf = RandomForestClassifier(
        featuresCol="features", labelCol="label", numTrees=50, seed=42
    )
    return rf.fit(treino)


def evaluate_model(previsoes):
    """Calcula acurácia, F1 e AUC-ROC de um DataFrame de previsões.

    Recebe o DataFrame `previsoes` (já com as colunas "prediction",
    "probability"/"rawPrediction" e "label") e retorna uma tupla
    (acuracia, f1, auc) com valores float:
      - acuracia e f1 via MulticlassClassificationEvaluator;
      - auc (areaUnderROC) via BinaryClassificationEvaluator.
    """
    acc = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    ).evaluate(previsoes)

    f1 = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="f1"
    ).evaluate(previsoes)

    auc = BinaryClassificationEvaluator(
        labelCol="label", metricName="areaUnderROC"
    ).evaluate(previsoes)

    return float(acc), float(f1), float(auc)


# ---------------------------------------------------------------------------
# Orquestração do Glue Job.
# ---------------------------------------------------------------------------
def main():
    """Orquestra o pipeline de previsão de direção de ações dentro do Glue Job."""
    # Resolve os argumentos passados pelo Glue (--JOB_NAME, --INPUT, --OUTPUT).
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "INPUT", "OUTPUT"])

    # Inicializa o contexto do Spark/Glue e o controle do Job.
    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # 1. Lê o CSV de ações do S3 e renomeia a coluna subiu -> label.
    df = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv(args["INPUT"])
        .withColumnRenamed("subiu", "label")
    )

    # 2. Monta o vetor de features e divide treino/teste (split fixo com seed=42).
    dados = build_feature_vector(df)
    treino, teste = dados.randomSplit([0.7, 0.3], seed=42)

    # 3. Treina os DOIS modelos sobre o MESMO conjunto de treino.
    modelo_lr = train_logistic_regression(treino)
    modelo_rf = train_random_forest(treino)

    # 4. Gera previsões no teste e avalia cada modelo (acurácia, F1, AUC-ROC).
    previsoes_lr = modelo_lr.transform(teste)
    previsoes_rf = modelo_rf.transform(teste)

    acc_lr, f1_lr, auc_lr = evaluate_model(previsoes_lr)
    acc_rf, f1_rf, auc_rf = evaluate_model(previsoes_rf)

    # 5. Imprime a tabela comparativa no stdout do driver (vai para o CloudWatch).
    print("=== Comparacao de modelos (previsao de direcao de acoes) ===")
    print(f"{'modelo':<22}{'acuracia':>10}{'f1':>10}{'auc_roc':>10}")
    print(f"{'LogisticRegression':<22}{acc_lr:>10.4f}{f1_lr:>10.4f}{auc_lr:>10.4f}")
    print(f"{'RandomForest':<22}{acc_rf:>10.4f}{f1_rf:>10.4f}{auc_rf:>10.4f}")

    # 6. Grava métricas e amostra de previsões no S3, a partir do prefixo --OUTPUT.
    out = args["OUTPUT"].rstrip("/")

    # Métricas de AMBOS os modelos no formato longo (modelo,metrica,valor).
    linhas_metricas = [
        ("LogisticRegression", "accuracy", acc_lr),
        ("LogisticRegression", "f1", f1_lr),
        ("LogisticRegression", "areaUnderROC", auc_lr),
        ("RandomForest", "accuracy", acc_rf),
        ("RandomForest", "f1", f1_rf),
        ("RandomForest", "areaUnderROC", auc_rf),
    ]
    metrics = spark.createDataFrame(
        [(m, met, float(v)) for (m, met, v) in linhas_metricas],
        ["modelo", "metrica", "valor"],
    )
    metrics.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{out}/metrics"
    )

    # Amostra de previsões do Random Forest (features + label real + previsão).
    amostra = previsoes_rf.select(*FEATURES, "label", "prediction")
    amostra.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{out}/predictions"
    )

    print(f"Resultado gravado em: {out}/metrics e {out}/predictions")

    # 7. Finaliza o Job do Glue (marca o run como concluído).
    job.commit()


if __name__ == "__main__":
    main()
