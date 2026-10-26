
"""
Aula 09 - Data Warehousing e Data Lakes
Lab: Consultas SQL sobre uma tabela "estilo Hive" usando Spark SQL.
"""


def register_sales_table(spark, rows):
    """
    Ja implementado: cria uma view temporaria "sales" a partir de uma lista
    de tuplas (region, product, revenue).
    """
    df = spark.createDataFrame(rows, ["region", "product", "revenue"])
    df.createOrReplaceTempView("sales")
    return df


def total_revenue_by_region(spark):
    """Retorna {region: total_revenue}, da maior para a menor receita."""
    result = spark.sql(
        """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
        """
    )
    return {row["region"]: row["total_revenue"] for row in result.collect()}


def top_n_products(spark, n):
    """Retorna a lista com os nomes dos n produtos de maior receita total."""
    result = spark.sql(
        f"""
        SELECT product, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY product
        ORDER BY total_revenue DESC
        LIMIT {int(n)}
        """
    )
    return [row["product"] for row in result.collect()]


def regions_above_threshold(spark, threshold):
    """Retorna as regioes com receita total > threshold, da maior para a menor."""
    result = spark.sql(
        f"""
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        HAVING SUM(revenue) > {threshold}
        ORDER BY total_revenue DESC
        """
    )
    return [row["region"] for row in result.collect()]
