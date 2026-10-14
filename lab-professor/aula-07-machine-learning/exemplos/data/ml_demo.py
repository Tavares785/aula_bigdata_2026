"""
Aula 07 - Demo AO VIVO: Machine Learning em escala com Spark MLlib (cluster real).

Submetido via `spark-submit /data/ml_demo.py` dentro do spark-master
(veja exemplos/demo.sh). Cenario realista: prever CHURN (cancelamento)
de clientes a partir de historico de uso.

Pipeline linear e didatico (sem Pipeline nem CrossValidator):
VectorAssembler -> split treino/teste (70/30) -> compara dois classificadores
(LogisticRegression x RandomForest) sobre o MESMO split, reportando
acuracia, F1 e AUC-ROC para cada modelo.
"""
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import (
    MulticlassClassificationEvaluator,
    BinaryClassificationEvaluator,
)

FEATURES = ["meses_ativo", "gasto_mensal", "chamados_suporte", "atraso_pagamento"]


def avaliar(previsoes):
    """Retorna (acuracia, f1, auc_roc) de um DataFrame de previsoes.

    Usa MulticlassClassificationEvaluator para acuracia e F1 e
    BinaryClassificationEvaluator para a area sob a curva ROC.
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
    return acc, f1, auc


def main():
    spark = SparkSession.builder.appName("aula07-demo-mllib").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Le o dataset de churn e renomeia a coluna alvo para "label".
    df = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv("/data/churn_clientes.csv")
        .withColumnRenamed("churn", "label")
    )

    print("\n=== Amostra do dataset de churn ===")
    df.show(5, truncate=False)

    # Monta a coluna unica de features exigida pelo MLlib.
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    dados = assembler.transform(df)

    # Split treino/teste reprodutivel; o MESMO split alimenta os dois modelos.
    treino, teste = dados.randomSplit([0.7, 0.3], seed=42)
    print(f"\nTreino: {treino.count()} linhas | Teste: {teste.count()} linhas")

    # Modelo 1: Regressao Logistica.
    print("\n=== Treinando Regressao Logistica (MLlib) ===")
    modelo_lr = LogisticRegression(
        featuresCol="features", labelCol="label"
    ).fit(treino)
    previsoes_lr = modelo_lr.transform(teste)
    acc_lr, f1_lr, auc_lr = avaliar(previsoes_lr)

    # Modelo 2: Random Forest (sobre o mesmo split de treino).
    print("=== Treinando Random Forest (MLlib) ===")
    modelo_rf = RandomForestClassifier(
        featuresCol="features", labelCol="label"
    ).fit(treino)
    previsoes_rf = modelo_rf.transform(teste)
    acc_rf, f1_rf, auc_rf = avaliar(previsoes_rf)

    # Tabela de comparacao dos dois classificadores no stdout do driver.
    print("\n=== Comparacao de classificadores (churn) ===")
    print(f"{'Modelo':<22}{'Acuracia':>10}{'F1':>8}{'AUC-ROC':>10}")
    print(f"{'LogisticRegression':<22}{acc_lr:>10.3f}{f1_lr:>8.3f}{auc_lr:>10.3f}")
    print(f"{'RandomForest':<22}{acc_rf:>10.3f}{f1_rf:>8.3f}{auc_rf:>10.3f}")

    spark.stop()


if __name__ == "__main__":
    main()
