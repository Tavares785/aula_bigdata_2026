"""
Aula 06 - Spark SQL / DataFrames no AWS Glue
============================================

Este script roda como um AWS GLUE JOB (tipo glueetl, PySpark), usando a API de
DataFrames / Spark SQL da aula-06. A diferença para o notebook/local é ONDE ele
roda: aqui o driver e os executors são gerenciados pelo Glue (provisionados sob
demanda quando o job é disparado), e os dados vêm/vão para o S3 (não para o
disco local).

Por que Glue (e não EMR Serverless)?
  Neste Learner Lab o EMR Serverless está bloqueado, mas o Glue funciona (a
  LabRole confia em glue.amazonaws.com). É o mesmo serviço usado na prova.

Fluxo:
  1. Lê DOIS CSVs do S3:
       - --PEDIDOS  (ex.: s3://SEU_BUCKET/input/pedidos.csv),
         colunas: order_id, customer_id, category, value.
       - --CLIENTES (ex.: s3://SEU_BUCKET/input/clientes.csv),
         colunas: customer_id, customer_name, customer_uf.
  2. Faz join + agregação com a API de DataFrames/Spark SQL para calcular o
     TOP-N de clientes por gasto (top_n_customers_by_spend).
  3. Escreve o resultado como CSV no S3 (argumento --OUTPUT, ex.:
     s3://SEU_BUCKET/output/top_clientes) com header.
  4. Também imprime o resultado no stdout do driver — que vai para o log do
     driver no CloudWatch (grupo /aws-glue/jobs/output).

Como o script recebe a SparkSession:
  No Glue criamos o SparkContext e o GlueContext dentro de main(); a
  SparkSession vem de glue.spark_session. As funções abaixo recebem DataFrames
  como parâmetro (a mesma API vista na aula-06).

⚠️ ANTES DE SUBIR: complete os dois TODOs abaixo (total_revenue_by_category e
   top_n_customers_by_spend). Enquanto não completar, essas funções levantam
   NotImplementedError (mas o módulo importa/compila normalmente, pois o erro
   só acontece em tempo de execução).
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

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


def filter_high_value_sales(sales_df, min_value):
    """
    EXEMPLO PRONTO (referência de DataFrame — serve de modelo para o aluno).

    Retorna apenas as linhas em que a coluna `value` é maior ou igual a
    `min_value`. Usa a API de DataFrames (filter + F.col), sem SQL textual.

    Exemplo:
        filter_high_value_sales(vendas_df, 1000)  # linhas com value >= 1000
    """
    return sales_df.filter(F.col("value") >= min_value)


def join_orders_with_customers(orders_df, customers_df):
    """
    REFERÊNCIA PRONTA (usada pelo TODO 2 abaixo).

    Faz um INNER JOIN entre pedidos e clientes pela coluna `customer_id` e
    seleciona apenas as 4 colunas de interesse: order_id, customer_id,
    customer_name e value.

    - orders_df:    order_id, customer_id, category, value.
    - customers_df: customer_id, customer_name, customer_uf.

    Retorna um DataFrame com: order_id, customer_id, customer_name, value.
    """
    return orders_df.join(customers_df, on="customer_id", how="inner").select(
        "order_id",
        "customer_id",
        "customer_name",
        "value",
    )


def total_revenue_by_category(orders_df):
    """
    TODO 1 (implemente com a API de DataFrames/Spark SQL):
    Calcule a receita total por categoria a partir de `orders_df`
    (colunas: order_id, customer_id, category, value):
      1. Agrupe por `category` (groupBy).
      2. Some a coluna `value` e nomeie o resultado como `total_revenue`
         (use F.sum("value").alias("total_revenue")).
      3. Ordene por `total_revenue` de forma DECRESCENTE (orderBy ... desc).

    Retorne um DataFrame com as colunas: category, total_revenue.

    Exemplo (conceitual):
        total_revenue_by_category(pedidos)
        -> category   | total_revenue
           eletronicos| 12345.67
           moveis     |  6789.00
           ...        | ...
    """
    return (orders_df.groupBy("category").agg(F.sum("value").alias("total_revenue")).orderBy(F.col("total_revenue").desc()))


def top_n_customers_by_spend(orders_df, customers_df, n):
    """
    TODO 2 (implemente com a API de DataFrames/Spark SQL):
    Calcule os `n` clientes que mais gastaram:
      1. Reutilize join_orders_with_customers(orders_df, customers_df) para
         obter order_id, customer_id, customer_name, value.
      2. Agrupe por (customer_id, customer_name) (groupBy com as duas colunas).
      3. Some a coluna `value` e nomeie como `total_spend`
         (F.sum("value").alias("total_spend")).
      4. Ordene por `total_spend` DECRESCENTE (orderBy ... desc).
      5. Pegue apenas as `n` primeiras linhas (limit(n)).

    Retorne um DataFrame com as colunas: customer_id, customer_name, total_spend.

    Exemplo (conceitual):
        top_n_customers_by_spend(pedidos, clientes, 5)
        -> customer_id | customer_name | total_spend
           C009        | Isabela Nunes | 12928.10
           ...         | ...           | ...
    """
    joined = join_orders_with_customers(orders_df, customers_df)
    return (joined.groupBy("customer_id", "customer_name").agg(F.sum("value").alias("total_spend")).orderBy(F.col("total_spend").desc()).limit(n))


def main():
    """Ponto de entrada executado pelo AWS Glue (glueetl / spark-submit)."""
    # Lê os argumentos do Glue. JOB_NAME é injetado pelo Glue; os demais vêm dos
    # default_arguments definidos no aws_glue_job (--PEDIDOS/--CLIENTES/etc.).
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "PEDIDOS", "CLIENTES", "OUTPUT", "TOP_N"],
    )

    # Contexto Spark/Glue: o SparkContext e o GlueContext são gerenciados pelo
    # Glue; a SparkSession vem do GlueContext. O Job registra início/fim.
    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # Lê os dois CSVs do S3 como DataFrames (com header e inferência de schema).
    pedidos = (
        spark.read.option("header", True).option("inferSchema", True).csv(args["PEDIDOS"])
    )
    clientes = (
        spark.read.option("header", True).option("inferSchema", True).csv(args["CLIENTES"])
    )

    # Quantos clientes retornar no TOP-N (vem como string do Glue).
    n = int(args["TOP_N"])

    # Calcula o TOP-N de clientes por gasto (função do aluno — TODO 2).
    resultado = top_n_customers_by_spend(pedidos, clientes, n)

    # Imprime no stdout do driver (aparece no log do driver no CloudWatch).
    print("=== Top clientes por gasto (customer_id,customer_name,total_spend) ===")
    resultado.show(truncate=False)
    for linha in resultado.collect():
        print(f"{linha['customer_id']},{linha['customer_name']},{linha['total_spend']}")

    # Grava o resultado no S3 como CSV (um arquivo, com header).
    # coalesce(1) junta em uma única partição para facilitar a leitura no lab.
    resultado.coalesce(1).write.mode("overwrite").option("header", True).csv(args["OUTPUT"])

    print(f"Resultado gravado em: {args['OUTPUT']}")

    # Finaliza o job (marca a execução como concluída no Glue).
    job.commit()


if __name__ == "__main__":
    main()
