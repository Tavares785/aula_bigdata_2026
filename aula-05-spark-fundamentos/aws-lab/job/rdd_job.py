"""
Aula 05 - Spark/RDDs no AWS Glue
================================
Implementacao dos TODOs por Fernanda (aula-05-aws-fernanda).
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession, Row

try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:
    getResolvedOptions = None
    GlueContext = None
    Job = None


def word_count_rdd(sc, lines):
    """
    Contagem de palavras com RDDs.
    Retorna lista de (palavra, contagem) ordenada por contagem desc,
    e em empate alfabetica asc.

    Exemplo:
        word_count_rdd(sc, ["gato rato gato", "rato correu gato"])
        -> [("gato", 3), ("rato", 2), ("correu", 1)]
    """
    rdd = sc.parallelize(lines)
    contagens = (
        rdd
        .flatMap(lambda linha: linha.lower().split())
        .map(lambda palavra: (palavra, 1))
        .reduceByKey(lambda a, b: a + b)
    )
    resultado = contagens.sortBy(lambda t: (-t[1], t[0])).collect()
    return resultado


def top_n_palavras(sc, lines, n):
    """
    Retorna as n palavras mais frequentes de lines.

    Exemplo:
        top_n_palavras(sc, ["gato rato gato", "rato correu gato"], 2)
        -> [("gato", 3), ("rato", 2)]
    """
    return word_count_rdd(sc, lines)[:n]


def main():
    """Ponto de entrada executado pelo AWS Glue (glueetl / spark-submit)."""
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "INPUT", "OUTPUT"])

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # Le o texto do S3 como lista de linhas
    linhas = spark.read.text(args["INPUT"]).rdd.map(lambda r: r[0]).collect()

    # Word count com RDDs
    resultado = word_count_rdd(sc, linhas)

    # Imprime no CloudWatch
    print("=== Word count (palavra,contagem) ===")
    for palavra, contagem in resultado:
        print(f"{palavra},{contagem}")

    # Top 5 palavras (bonus)
    top5 = top_n_palavras(sc, linhas, 5)
    print("=== Top 5 palavras ===")
    for palavra, contagem in top5:
        print(f"{palavra},{contagem}")

    # Grava o resultado no S3 via DataFrame (compativel com Glue 4.0 + S3)
    # Converte a lista de tuplas em DataFrame e salva como CSV (texto simples)
    rows = [Row(value=f"{p},{c}") for p, c in resultado]
    df = spark.createDataFrame(rows)
    df.write.mode("overwrite").text(args["OUTPUT"])

    print(f"Resultado gravado em: {args['OUTPUT']}")

    job.commit()


if __name__ == "__main__":
    main()