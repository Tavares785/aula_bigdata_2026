"""
Aula 06 - Demo AO VIVO: Spark SQL e DataFrames (cluster real).

Submetido via `spark-submit /data/dataframe_demo.py` dentro do
spark-master (veja exemplos/demo.sh). Le dois CSVs realistas -- pedidos e
clientes -- e aplica as MESMAS operacoes do lab (filter, groupBy/agg,
join) alem de uma consulta via Spark SQL, mostrando as duas APIs
(DataFrame e SQL) sobre os mesmos dados.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def main():
    spark = SparkSession.builder.appName("aula06-demo-dataframes").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")


    pedidos = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv("/data/pedidos.csv")
    )

    clientes = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv("/data/clientes.csv")
    )

    print("\n=== Pedidos (schema inferido) ===")
    pedidos.printSchema()

    print("\n=== 1) Pedidos de alto valor (value >= 1000) -- API DataFrame ===")
    pedidos.filter(F.col("value") >= 1000).show(truncate=False)

    print("\n=== 2) Receita por categoria (groupBy + agg) ===")
    (
        pedidos.groupBy("category")
        .agg(F.round(F.sum("value"), 2).alias("receita"), F.count("*").alias("pedidos"))
        .orderBy(F.desc("receita"))
        .show(truncate=False)
    )

    print("\n=== 3) JOIN pedidos x clientes: top clientes por gasto ===")
    joined = pedidos.join(clientes, on="customer_id", how="inner")
    (
        joined.groupBy("customer_id", "customer_name", "segmento")
        .agg(F.round(F.sum("value"), 2).alias("total_gasto"))
        .orderBy(F.desc("total_gasto"))
        .show(truncate=False)
    )

    print("\n=== 4) A MESMA analise via Spark SQL (createOrReplaceTempView) ===")
    joined.createOrReplaceTempView("vendas")
    spark.sql(
        """
        SELECT segmento,
               ROUND(SUM(value), 2) AS receita,
               COUNT(*)             AS pedidos
        FROM vendas
        GROUP BY segmento
        ORDER BY receita DESC
        """
    ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
