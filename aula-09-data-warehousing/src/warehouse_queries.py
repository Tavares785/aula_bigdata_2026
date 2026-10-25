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
    TODO 1:
    Escreva e execute (via `spark.sql(...)`) uma query SQL sobre a
    tabela "sales" que retorne o total de receita ("revenue") por
    regiao ("region"), ORDENADO da maior para a menor receita.

    Retorne o resultado como um dicionario {region: total_revenue}.

    Dica: SELECT region, SUM(revenue) AS total_revenue FROM sales
          GROUP BY region ORDER BY total_revenue DESC
    """
    df = spark.sql(
        """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
        """
    )
    return {row["region"]: row["total_revenue"] for row in df.collect()}


def top_n_products(spark, n):
    """
    TODO 2:
    Escreva uma query SQL que retorne os `n` PRODUTOS com maior receita
    total (somando "revenue" por "product"), ordenados do maior para o
    menor. Retorne apenas os NOMES dos produtos, como uma lista de
    strings (na ordem correta).

    Dica: use LIMIT {n} na sua query (pode usar f-string para inserir o
    valor de n).
    """
    df = spark.sql(
        f"""
        SELECT product, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY product
        ORDER BY total_revenue DESC
        LIMIT {int(n)}
        """
    )
    return [row["product"] for row in df.collect()]


def regions_above_threshold(spark, threshold):
    """
    TODO 3:
    Escreva uma query SQL que retorne as regioes cuja receita TOTAL
    (soma de "revenue") seja MAIOR que `threshold`, ordenadas da maior
    para a menor receita. Retorne apenas os NOMES das regioes, como uma
    lista de strings.

    Dica: use a clausula HAVING para filtrar depois do GROUP BY (WHERE
    nao funciona sobre valores agregados).
    """
    df = spark.sql(
        f"""
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales
        GROUP BY region
        HAVING SUM(revenue) > {float(threshold)}
        ORDER BY total_revenue DESC
        """
    )
    return [row["region"] for row in df.collect()]
