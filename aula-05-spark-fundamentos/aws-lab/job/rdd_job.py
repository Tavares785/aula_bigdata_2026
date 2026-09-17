"""
Aula 05 - Spark/RDDs no AWS Glue
================================

Este script roda como um AWS GLUE JOB (tipo glueetl, PySpark), usando a mesma
API de RDDs da aula-05 local (src/rdd_basics.py). A diferença é ONDE ele roda:
aqui o driver e os executors sao gerenciados pelo Glue (provisionados sob
demanda quando o job é disparado), e os dados vem/vao para o S3 (nao para o
disco local).

Por que Glue (e nao EMR Serverless)?
  Neste Learner Lab o EMR Serverless esta bloqueado, mas o Glue funciona (a
  LabRole confia em glue.amazonaws.com). É o mesmo serviço usado na prova.

Fluxo:
  1. Le um arquivo de texto do S3 (argumento --INPUT, ex.:
     s3://SEU_BUCKET/input/sample_lines.txt).
  2. Calcula a contagem de palavras com RDDs (word_count_rdd).
  3. Escreve o resultado (uma linha "palavra,contagem" por registro) no S3
     (argumento --OUTPUT, ex.: s3://SEU_BUCKET/output/wordcount).
  4. Tambem imprime o resultado no stdout do driver — que vai para o log do
     driver no CloudWatch (grupo /aws-glue/jobs/output).

Como o script recebe um SparkContext:
  No Glue criamos o SparkContext e o GlueContext dentro de main(); a
  SparkSession vem de glue.spark_session. As funcoes recebem `sc` como
  parametro, igual à aula-05.

⚠️ ANTES DE SUBIR: complete os dois TODOs abaixo (word_count_rdd e
   top_n_palavras). Enquanto nao completar, as funcoes levantam
   NotImplementedError (mas o modulo importa/compila normalmente).
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession

# Imports específicos do Glue — disponíveis no runtime do AWS Glue.
# No ambiente local (sem o SDK do Glue) eles não existem; por isso o try/except
# com fallback None permite que o módulo importe/compile localmente.
try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:  # ambiente local sem o SDK do Glue
    getResolvedOptions = None
    GlueContext = None
    Job = None


def word_count_rdd(sc, lines):
    """
    TODO 1 (mesmo contrato da aula-05):
    Receba `sc` (SparkContext) e uma lista de strings `lines` (cada item é uma
    "linha" de texto) e retorne a contagem de palavras usando RDDs:
    """

    rdd = sc.parallelize(lines)

    palavras = rdd.flatMap(lambda linha: linha.split(" "))

    palavras_minusculas = palavras.map(lambda palavra: palavra.lower())

    pares = palavras_minusculas.map(lambda palavra: (palavra, 1))

    contagem = pares.reduceByKey(lambda a, b: a + b)

    resultado = contagem.collect()

    resultado.sort(key=lambda x: (-x[1], x[0]))

    return resultado


def top_n_palavras(sc, lines, n):
    """
    TODO 2:
    Retorne as `n` palavras mais frequentes de `lines`.
    """

    resultado = word_count_rdd(sc, lines)

    return resultado[:n]


def main():
    """Ponto de entrada executado pelo AWS Glue (glueetl / spark-submit)."""
    # Le os argumentos do Glue. JOB_NAME é injetado pelo Glue; INPUT/OUTPUT vêm
    # dos default_arguments definidos no aws_glue_job (--INPUT / --OUTPUT).
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "INPUT", "OUTPUT"])

    # Contexto Spark/Glue: o SparkContext e o GlueContext são gerenciados pelo
    # Glue; a SparkSession vem do GlueContext. O Job registra início/fim.
    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # Le o texto do S3 como uma lista de linhas (strings).
    # spark.read.text(...).rdd traz cada linha; row[0] é a coluna "value".
    linhas = spark.read.text(args["INPUT"]).rdd.map(lambda r: r[0]).collect()

    # Calcula a contagem de palavras com a API de RDDs (funcao do aluno).
    resultado = word_count_rdd(sc, linhas)

    # Imprime no stdout do driver (aparece no log do driver no CloudWatch).
    print("=== Word count (palavra,contagem) ===")
    for palavra, contagem in resultado:
        print(f"{palavra},{contagem}")

    # Grava o resultado no S3 como texto: uma linha "palavra,contagem".
    # Distribui a escrita entre os executors via RDD.saveAsTextFile.
    hadoop_conf = sc._jsc.hadoopConfiguration()
    hadoop_conf.set("mapreduce.outputcommitter.class", "org.apache.hadoop.mapred.FileOutputCommitter")
    hadoop_conf.set("mapred.output.committer.class", "org.apache.hadoop.mapred.FileOutputCommitter")
    sc.parallelize(resultado).map(
        lambda t: f"{t[0]},{t[1]}"
    ).saveAsTextFile(args["OUTPUT"])

    print(f"Resultado gravado em: {args['OUTPUT']}")

    # Finaliza o job (marca a execução como concluída no Glue).
    job.commit()


if __name__ == "__main__":
    main()
