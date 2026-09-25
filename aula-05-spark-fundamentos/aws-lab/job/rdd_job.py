import sys

from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.job import Job


def word_count_rdd(sc, lines):
    rdd = sc.parallelize(lines)
    palavras = rdd.flatMap(lambda linha: linha.lower().split())
    pares = palavras.map(lambda palavra: (palavra, 1))
    contagem = pares.reduceByKey(lambda a, b: a + b)
    resultado = contagem.collect()
    resultado.sort(key=lambda x: (-x[1], x[0]))
    return resultado


def top_n_palavras(sc, lines, n):
    return word_count_rdd(sc, lines)[:n]


def main():
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "INPUT", "OUTPUT"]
    )

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session

    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    linhas = (
        spark.read
        .text(args["INPUT"])
        .rdd
        .map(lambda r: r[0])
        .collect()
    )

    resultado = word_count_rdd(sc, linhas)

    print("=== Word count (palavra,contagem) ===")

    for palavra, contagem in resultado:
        print(f"{palavra},{contagem}")

    resultado_df = spark.createDataFrame(
        resultado,
        ["palavra", "contagem"]
    )

    resultado_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(args["OUTPUT"])

    print("Resultado gravado em: " + args["OUTPUT"])

    job.commit()


if __name__ == "__main__":
    main()
