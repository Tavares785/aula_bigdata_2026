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
      1. Crie um RDD a partir de `lines` com `sc.parallelize(lines)`.
      2. Use `flatMap` para quebrar cada linha em palavras (separadas por
         espaco) JA convertidas para minusculas.
      3. Use `map` para transformar cada palavra em (palavra, 1).
      4. Use `reduceByKey` para somar as ocorrencias de cada palavra.
      5. Retorne uma lista de tuplas (palavra, contagem), ORDENADA por contagem
         decrescente e, em empate, por ordem alfabetica crescente da palavra.

    Exemplo:
        word_count_rdd(sc, ["gato rato gato", "rato correu gato"])
        -> [("gato", 3), ("rato", 2), ("correu", 1)]
    """
    # 1. Distribui a lista `lines` em partições do cluster (RDD = Resilient
    #    Distributed Dataset). Cada item da lista vira um registro do RDD.
    rdd = sc.parallelize(lines)

    # 2. flatMap: para CADA linha, aplicamos uma função que retorna uma LISTA
    #    de palavras (linha.lower().split()) e o Spark "achata" (flatten) o
    #    resultado, juntando todas as listas numa única sequência de palavras.
    #    Se usássemos `map` em vez de `flatMap`, o resultado seria um RDD de
    #    listas de palavras (uma lista por linha), não de palavras soltas.
    palavras = rdd.flatMap(lambda linha: linha.lower().split())

    # 3. map: transforma cada palavra numa tupla (palavra, 1). Esse "1" é a
    #    contagem inicial de cada ocorrência — é o padrão clássico de word
    #    count (map-reduce): primeiro conta "1 por aparição", depois soma.
    pares = palavras.map(lambda palavra: (palavra, 1))

    # 4. reduceByKey: agrupa as tuplas pela chave (a palavra) e combina os
    #    valores de cada grupo usando a função dada — aqui, soma (a + b).
    #    Isso roda de forma distribuída: cada executor soma localmente as
    #    palavras da sua partição antes de combinar os resultados parciais.
    contagens = pares.reduceByKey(lambda a, b: a + b)

    # 5. collect() traz o resultado do cluster (executors) de volta para o
    #    driver, como uma lista Python normal. A partir daqui não é mais
    #    processamento distribuído, é só ordenação local da lista final.
    #    Ordenamos por: contagem decrescente (-contagem) e, em empate,
    #    palavra em ordem alfabética crescente.
    resultado = contagens.collect()
    resultado_ordenado = sorted(resultado, key=lambda par: (-par[1], par[0]))

    return resultado_ordenado


def top_n_palavras(sc, lines, n):
    """
    TODO 2:
    Retorne as `n` palavras mais frequentes de `lines`, como lista de tuplas
    (palavra, contagem), na mesma ordenacao de word_count_rdd (contagem
    decrescente e, em empate, alfabetica crescente).

    Dica: reutilize word_count_rdd(sc, lines) e pegue os `n` primeiros itens.

    Exemplo:
        top_n_palavras(sc, ["gato rato gato", "rato correu gato"], 2)
        -> [("gato", 3), ("rato", 2)]
    """
    # Reaproveita word_count_rdd: ela já devolve a lista ordenada por
    # contagem desc / alfabética asc, então "top N" é simplesmente pegar
    # os N primeiros itens dessa lista (fatiamento de lista Python comum).
    resultado_completo = word_count_rdd(sc, lines)
    return resultado_completo[:n]


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
    sc.parallelize(resultado).map(
        lambda t: f"{t[0]},{t[1]}"
    ).saveAsTextFile(args["OUTPUT"])

    print(f"Resultado gravado em: {args['OUTPUT']}")

    # Finaliza o job (marca a execução como concluída no Glue).
    job.commit()


if __name__ == "__main__":
    main()
