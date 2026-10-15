"""
Aula 06 - Spark SQL / DataFrames no AWS Glue
============================================
Implementacao dos TODOs por Fernanda (RA 4025109).

Fluxo: le 2 CSVs do S3 (pedidos, clientes), faz join + agregacao com a API de
DataFrames/Spark SQL para calcular o TOP-N de clientes por gasto e grava o
resultado como CSV no S3.
"""

import sys

from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

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
    EXEMPLO PRONTO (referencia de DataFrame).
    Retorna apenas as linhas em que `value` >= `min_value`.
    """
    return sales_df.filter(F.col("value") >= min_value)


def join_orders_with_customers(orders_df, customers_df):
    """
    REFERENCIA PRONTA (usada pelo TODO 2).
    INNER JOIN entre pedidos e clientes por `customer_id`, selecionando
    order_id, customer_id, customer_name e value.
    """
    return orders_df.join(customers_df, on="customer_id", how="inner").select(
        "order_id",
        "customer_id",
        "customer_name",
        "value",
    )


def total_revenue_by_category(orders_df):
    """
    Receita total por categoria:
      1. groupBy por `category`.
      2. soma de `value` como `total_revenue`.
      3. ordena por `total_revenue` decrescente.
    Retorna DataFrame com colunas: category, total_revenue.
    """
    return (
        orders_df
        .groupBy("category")
        .agg(F.sum("value").alias("total_revenue"))
        .orderBy(F.col("total_revenue").desc())
    )


def top_n_customers_by_spend(orders_df, customers_df, n):
    """
    TOP-N clientes por gasto:
      1. reutiliza join_orders_with_customers.
      2. groupBy por (customer_id, customer_name).
      3. soma de `value` como `total_spend`.
      4. ordena por `total_spend` decrescente.
      5. limita a `n` linhas.
    Retorna DataFrame com colunas: customer_id, customer_name, total_spend.
    """
    joined = join_orders_with_customers(orders_df, customers_df)
    return (
        joined
        .groupBy("customer_id", "customer_name")
        .agg(F.sum("value").alias("total_spend"))
        .orderBy(F.col("total_spend").desc())
        .limit(n)
    )


def main():
    """Ponto de entrada executado pelo AWS Glue (glueetl / spark-submit)."""
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "PEDIDOS", "CLIENTES", "OUTPUT", "TOP_N"],
    )

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    pedidos = (
        spark.read.option("header", True).option("inferSchema", True).csv(args["PEDIDOS"])
    )
    clientes = (
        spark.read.option("header", True).option("inferSchema", True).csv(args["CLIENTES"])
    )

    n = int(args["TOP_N"])

    resultado = top_n_customers_by_spend(pedidos, clientes, n)

    print("=== Top clientes por gasto (customer_id,customer_name,total_spend) ===")
    resultado.show(truncate=False)
    for linha in resultado.collect():
        print(f"{linha['customer_id']},{linha['customer_name']},{linha['total_spend']}")

    # Bonus: receita por categoria no log do driver.
    print("=== Receita total por categoria (category,total_revenue) ===")
    total_revenue_by_category(pedidos).show(truncate=False)

    resultado.coalesce(1).write.mode("overwrite").option("header", True).csv(args["OUTPUT"])

    print(f"Resultado gravado em: {args['OUTPUT']}")

    job.commit()


if __name__ == "__main__":
    main()