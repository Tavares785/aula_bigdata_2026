"""
Execucao LOCAL do job da aula-06 (sem AWS Glue).

Usado como evidencia alternativa porque o acesso ao AWS Academy Learner Lab
expirou. Reaproveita as funcoes de job/dataframe_job.py com uma SparkSession
local (master local[2]), lendo os mesmos CSVs (pedidos.csv e clientes.csv) e
gravando o TOP-N de clientes em CSV com header, como faz o main() do Glue.

Uso (a partir de aws-lab/):
    python evidencias/6325231/executar_local.py data/pedidos.csv data/clientes.csv /tmp/output/top_clientes 5
"""
import os
import sys

from pyspark.sql import SparkSession

AWS_LAB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AWS_LAB, "job"))

from dataframe_job import (  # noqa: E402
    top_n_customers_by_spend,
    total_revenue_by_category,
)


def main():
    pedidos_path, clientes_path, saida, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    spark = SparkSession.builder.master("local[2]").appName("aula06-topn-local").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    pedidos = spark.read.option("header", True).option("inferSchema", True).csv(pedidos_path)
    clientes = spark.read.option("header", True).option("inferSchema", True).csv(clientes_path)
    print(f"pedidos: {pedidos.count()} linhas | clientes: {clientes.count()} linhas")

    print("=== Receita total por categoria (category,total_revenue) ===")
    total_revenue_by_category(pedidos).show(truncate=False)

    resultado = top_n_customers_by_spend(pedidos, clientes, n)
    print("=== Top clientes por gasto (customer_id,customer_name,total_spend) ===")
    resultado.show(truncate=False)
    for linha in resultado.collect():
        print(f"{linha['customer_id']},{linha['customer_name']},{linha['total_spend']}")

    resultado.coalesce(1).write.mode("overwrite").option("header", True).csv(saida)
    print(f"Resultado gravado em: {saida}")
    spark.stop()


if __name__ == "__main__":
    main()
