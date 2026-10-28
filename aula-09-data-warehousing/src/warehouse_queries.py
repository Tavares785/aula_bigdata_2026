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
    Retorna a receita total por regiao, da maior para a menor.
    """
    query = """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
    """

    resultado = spark.sql(query).collect()

    return {linha["region"]: linha["total_revenue"] for linha in resultado}


def top_n_products(spark, n):
    """
    Retorna os n produtos com maior receita total.
    """
    query = f"""
        SELECT product, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY product
        ORDER BY total_revenue DESC
        LIMIT {int(n)}
    """

    resultado = spark.sql(query).collect()

    return [linha["product"] for linha in resultado]


def regions_above_threshold(spark, threshold):
    """
    Retorna as regioes cuja receita total supera o limite informado.
    """
    query = f"""
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        HAVING SUM(revenue) > {float(threshold)}
        ORDER BY total_revenue DESC
    """

    resultado = spark.sql(query).collect()

    return [linha["region"] for linha in resultado]