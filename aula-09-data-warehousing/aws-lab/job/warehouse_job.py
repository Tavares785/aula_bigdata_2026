"""Job_DW — consultas de Data Warehouse com Spark SQL (AWS Glue).

Roda como Glue Job (`glueetl`) e reaproveita as queries do TF da aula-09
(`src/warehouse_queries.py`, enviado ao Glue via `--extra-py-files`).

Fluxo do `main()`:
  1. Le o CSV de vendas do S3 (`--INPUT`) — camada "raw" do lake.
  2. Grava a camada "curated" em Parquet particionado por `region`
     (`--OUTPUT`/lake/sales) e le de volta, como uma tabela Hive no HDFS.
  3. Registra a view "sales" e executa as 3 queries do warehouse.
  4. Imprime os resultados no stdout (vao para o CloudWatch).
  5. Grava cada resultado em CSV no S3 (`--OUTPUT`/<consulta>).
"""

import sys

from pyspark.context import SparkContext

import warehouse_queries as wq

# O SDK do AWS Glue so existe no ambiente gerenciado da AWS; o try/except
# mantem o modulo importavel localmente.
try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:  # ambiente local sem o SDK do Glue
    getResolvedOptions = None
    GlueContext = None
    Job = None


def main():
    """Orquestra o pipeline do warehouse dentro do Glue Job."""
    args = getResolvedOptions(
        sys.argv, ["JOB_NAME", "INPUT", "OUTPUT", "TOP_N", "THRESHOLD"]
    )
    top_n = int(args["TOP_N"])
    threshold = float(args["THRESHOLD"])
    out = args["OUTPUT"].rstrip("/")

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # 1. Camada raw: CSV de vendas.
    raw = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv(args["INPUT"])
    )

    # 2. Camada curated: Parquet particionado por regiao (layout de tabela Hive).
    lake = f"{out}/lake/sales"
    raw.write.mode("overwrite").partitionBy("region").parquet(lake)
    curated = spark.read.parquet(lake)

    # 3. Registra a view "sales" (mesmo schema do TF) e roda as queries.
    rows = [
        (r["region"], r["product"], float(r["revenue"]))
        for r in curated.select("region", "product", "revenue").collect()
    ]
    wq.register_sales_table(spark, rows)

    por_regiao = wq.total_revenue_by_region(spark)
    top = wq.top_n_products(spark, top_n)
    acima = wq.regions_above_threshold(spark, threshold)

    # 4. Resultados no stdout do driver (CloudWatch /aws-glue/jobs/output).
    print("=== Receita total por regiao ===")
    for regiao, total in por_regiao.items():
        print(f"{regiao},{total}")
    print(f"=== Top {top_n} produtos ===")
    print(",".join(top))
    print(f"=== Regioes com receita > {threshold} ===")
    print(",".join(acima))

    # 5. Grava cada resultado como CSV no S3.
    def salvar(nome, dados, colunas):
        spark.createDataFrame(dados, colunas).coalesce(1).write.mode(
            "overwrite"
        ).option("header", True).csv(f"{out}/{nome}")

    salvar("revenue_by_region", list(por_regiao.items()), ["region", "total_revenue"])
    salvar("top_products", [(i + 1, p) for i, p in enumerate(top)], ["rank", "product"])
    salvar("regions_above_threshold", [(r,) for r in acima], ["region"])

    print(f"Resultado gravado em: {out}/")
    job.commit()


if __name__ == "__main__":
    main()
