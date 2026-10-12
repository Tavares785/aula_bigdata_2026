"""
Aula 06 - Spark SQL e DataFrames
Lab: Filtragem, agregacao e juncao de dados usando a API de DataFrames.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
from pyspark.sql import functions as F


def filter_high_value_sales(sales_df, min_value):
    """
    Receba um DataFrame `sales_df` com colunas ("category", "value") e
    retorne apenas as linhas cujo "value" seja MAIOR OU IGUAL a
    `min_value`.

    Dica: use `.filter(...)` com `F.col("value") >= min_value`.
    """
    return sales_df.filter(F.col("value") >= min_value)


def total_revenue_by_category(sales_df):
    """
    Receba um DataFrame `sales_df` com colunas ("category", "value") e
    retorne um DataFrame agregado com colunas ("category",
    "total_revenue"), somando o "value" por categoria, ORDENADO por
    "total_revenue" DECRESCENTE.

    Dica: `.groupBy("category").agg(F.sum("value").alias("total_revenue"))`
    seguido de `.orderBy(F.desc("total_revenue"))`.
    """
    return (
        sales_df.groupBy("category")
        .agg(F.sum("value").alias("total_revenue"))
        .orderBy(F.desc("total_revenue"))
    )


def join_orders_with_customers(orders_df, customers_df):
    """
    Receba `orders_df` (colunas: order_id, customer_id, value) e
    `customers_df` (colunas: customer_id, customer_name) e retorne um
    DataFrame com o JOIN entre os dois (inner join pela coluna
    "customer_id"), selecionando apenas as colunas:
        order_id, customer_id, customer_name, value
    """
    return orders_df.join(customers_df, on="customer_id", how="inner").select(
        "order_id",
        "customer_id",
        "customer_name",
        "value",
    )


def top_n_customers_by_spend(orders_df, customers_df, n):
    """
    Usando o resultado de `join_orders_with_customers`, calcule o total
    gasto (soma de "value") por cliente (agrupando por customer_id E
    customer_name) e retorne os `n` clientes que MAIS gastaram, em um
    DataFrame com colunas (customer_id, customer_name, total_spend),
    ordenado do maior para o menor gasto.

    Dica: reaproveite a funcao `join_orders_with_customers` que voce
    acabou de implementar -- essa e a ideia de compor operacoes de
    DataFrame em pipelines maiores.
    """
    joined = join_orders_with_customers(orders_df, customers_df)
    return (
        joined.groupBy("customer_id", "customer_name")
        .agg(F.sum("value").alias("total_spend"))
        .orderBy(F.desc("total_spend"))
        .limit(n)
    )
