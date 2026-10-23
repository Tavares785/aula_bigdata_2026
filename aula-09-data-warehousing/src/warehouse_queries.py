"""
Aula 09 - Data Warehousing e Data Lakes
Lab: Consultas SQL sobre uma tabela "estilo Hive" usando Spark SQL.

Contexto
--------
Aqui usamos o Spark SQL com suporte a Hive (`enableHiveSupport()`) para
simular, localmente, o mesmo tipo de tabela e consulta HiveQL que voce
rodaria sobre dados no HDFS em um cluster real com Apache Hive. A sessao
Spark (`spark`) ja vem pronta nos testes -- seu trabalho e escrever as
queries.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""


def register_sales_table(spark, rows):
    """
    Ja implementado para voce: cria uma "tabela" (view temporaria)
    chamada "sales" a partir de uma lista de tuplas (region, product,
    revenue), para que voce possa consultar com `spark.sql(...)` nas
    funcoes abaixo.
    """
    df = spark.createDataFrame(rows, ["region", "product", "revenue"])
    df.createOrReplaceTempView("sales")
    return df


def total_revenue_by_region(spark):
    """
    TODO 1: total de receita por regiao, ordenado da maior para a menor.
    Retorna um dicionario {region: total_revenue}.
    """
    rows = spark.sql(
        """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
        """
    ).collect()
    return {row["region"]: row["total_revenue"] for row in rows}


def top_n_products(spark, n):
    """
    TODO 2: os `n` produtos com maior receita total, em ordem decrescente.
    Retorna uma lista com os nomes dos produtos.
    """
    n = int(n)
    rows = spark.sql(
        f"""
        SELECT product, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY product
        ORDER BY total_revenue DESC
        LIMIT {n}
        """
    ).collect()
    return [row["product"] for row in rows]


def regions_above_threshold(spark, threshold):
    """
    TODO 3: regioes cuja receita total e maior que `threshold`, em ordem
    decrescente. Retorna uma lista com os nomes das regioes.
    HAVING filtra sobre o agregado; WHERE nao faria isso.
    """
    threshold = float(threshold)
    rows = spark.sql(
        f"""
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        HAVING SUM(revenue) > {threshold}
        ORDER BY total_revenue DESC
        """
    ).collect()
    return [row["region"] for row in rows]
