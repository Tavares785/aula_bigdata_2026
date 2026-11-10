"""
Execucao LOCAL do job da aula-07 (churn com Spark MLlib), sem AWS Glue.

Usado como evidencia alternativa porque o acesso ao AWS Academy Learner Lab
expirou. Reproduz o fluxo do main() de job/ml_job.py com uma SparkSession local
(master local[2]), usando as funcoes do aluno (build_feature_vector,
train_classifier, evaluate_accuracy):
  1. le data/churn.csv e renomeia churn -> label;
  2. monta o vetor de features e divide treino/teste 70/30 (seed=42);
  3. treina a LogisticRegression e gera previsoes;
  4. calcula accuracy (funcao do aluno) e areaUnderROC;
  5. grava output/metrics e output/predictions em CSV com header.

Uso (a partir de aws-lab/):
    python evidencias/6325231/executar_local.py data/churn.csv /tmp/output
"""
import os
import sys

from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql import SparkSession

AWS_LAB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AWS_LAB, "job"))

from ml_job import (  # noqa: E402
    FEATURES,
    build_feature_vector,
    evaluate_accuracy,
    train_classifier,
)


def main():
    entrada, saida = sys.argv[1], sys.argv[2].rstrip("/")
    spark = SparkSession.builder.master("local[2]").appName("aula07-churn-local").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    df = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv(entrada)
        .withColumnRenamed("churn", "label")
    )

    dados = build_feature_vector(df)
    treino, teste = dados.randomSplit([0.7, 0.3], seed=42)
    print(f"linhas: total={df.count()} treino={treino.count()} teste={teste.count()}")

    modelo = train_classifier(treino)
    previsoes = modelo.transform(teste)

    acc = evaluate_accuracy(previsoes)
    auc = BinaryClassificationEvaluator(
        labelCol="label", metricName="areaUnderROC"
    ).evaluate(previsoes)

    print("=== Metricas (churn) ===")
    print(f"accuracy,{acc:.4f}")
    print(f"areaUnderROC,{auc:.4f}")

    print("=== Coeficientes da LogisticRegression ===")
    for nome, coef in zip(FEATURES, modelo.coefficients.toArray()):
        print(f"{nome},{coef:.4f}")
    print(f"intercept,{modelo.intercept:.4f}")

    metrics = spark.createDataFrame(
        [("accuracy", float(acc)), ("areaUnderROC", float(auc))], ["metrica", "valor"]
    )
    metrics.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{saida}/metrics")

    amostra = previsoes.select(*FEATURES, "label", "prediction")
    amostra.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{saida}/predictions")

    print(f"Resultado gravado em: {saida}/metrics e {saida}/predictions")
    spark.stop()


if __name__ == "__main__":
    main()
