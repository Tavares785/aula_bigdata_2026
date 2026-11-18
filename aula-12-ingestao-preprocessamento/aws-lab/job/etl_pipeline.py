"""
Aula 12 - Pipeline ETL MercadoFacil
Arquitetura Medalhão: raw (bronze) -> silver -> gold

Roda como AWS Glue Job (glueetl, PySpark, Glue 4.0).
"""
import sys
import re

from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

try:
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
except ImportError:
    getResolvedOptions = None
    GlueContext = None
    Job = None


# ---------------------------------------------------------------------------
# Constantes de qualidade
# ---------------------------------------------------------------------------
COLUNAS_OBRIGATORIAS = [
    "pedido_id", "item_id", "data_pedido", "status_pedido", "canal",
    "cliente_id", "estado", "categoria", "sku", "produto",
    "preco_unitario", "quantidade", "valor_total",
    "transportadora", "prazo_estimado_dias", "prazo_real_dias",
]

STATUS_VALIDOS = {
    "entregue", "cancelado", "devolvido", "em_transito", "processando"
}

CANAIS_VALIDOS = {
    "app", "site", "marketplace"
}


# ---------------------------------------------------------------------------
# Camada SILVER - limpeza e padronizacao
# ---------------------------------------------------------------------------
def build_silver(df):
    """Aplica as regras de qualidade documentadas em REGRAS_SILVER.md."""

    # R01 - Padroniza strings: strip + lower nas colunas categoricas
    for col in ["status_pedido", "canal", "categoria", "estado",
                "transportadora", "forma_pagamento", "cliente_segmento"]:
        df = df.withColumn(col, F.trim(F.lower(F.col(col))))

    # R02 - Tipagem: converte colunas numericas (chegam como string no CSV)
    numericas = {
        "preco_unitario": "double",
        "custo_unitario": "double",
        "quantidade": "int",
        "desconto_pct": "double",
        "valor_total": "double",
        "parcelas": "int",
        "prazo_estimado_dias": "int",
        "prazo_real_dias": "int",
        "atraso_dias": "int",
        "nota_avaliacao": "double",
    }
    for col, dtype in numericas.items():
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast(dtype))

    # R03 - Tipagem: converte datas
    for col in ["data_pedido", "data_entrega", "cliente_data_cadastro"]:
        if col in df.columns:
            df = df.withColumn(col, F.to_date(F.col(col)))

    # R04 - Quarentena: linhas com campos obrigatorios nulos
    cond_nulos = F.lit(False)
    for col in COLUNAS_OBRIGATORIAS:
        if col in df.columns:
            cond_nulos = cond_nulos | F.col(col).isNull()

    # R05 - Quarentena: valores negativos em preco/quantidade/valor_total
    cond_negativos = (
        (F.col("preco_unitario") < 0) |
        (F.col("quantidade") <= 0) |
        (F.col("valor_total") < 0)
    )

    # R06 - Quarentena: status invalido
    cond_status = ~F.col("status_pedido").isin(list(STATUS_VALIDOS))

    cond_quarentena = cond_nulos | cond_negativos | cond_status
    quarentena = df.filter(cond_quarentena).withColumn(
        "motivo_quarentena",
        F.when(cond_nulos, "campo_obrigatorio_nulo")
         .when(cond_negativos, "valor_negativo_ou_zero")
         .when(cond_status, "status_invalido")
         .otherwise("outro")
    )
    silver = df.filter(~cond_quarentena)

    # R07 - Deduplicacao: mantém a linha mais recente por (pedido_id, item_id)
    w = Window.partitionBy("pedido_id", "item_id").orderBy(
        F.col("data_pedido").desc()
    )
    silver = (
        silver
        .withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # R08 - Mascara dados pessoais (LGPD): hash de cliente_cpf e cliente_email
    if "cliente_cpf" in silver.columns:
        silver = silver.withColumn(
            "cliente_cpf", F.sha2(F.col("cliente_cpf").cast("string"), 256)
        )
    if "cliente_email" in silver.columns:
        silver = silver.withColumn(
            "cliente_email", F.sha2(F.col("cliente_email").cast("string"), 256)
        )

    # R09 - Coluna derivada: flag de atraso
    silver = silver.withColumn(
        "atrasado",
        F.when(F.col("atraso_dias") > 0, True).otherwise(False)
    )

    # R10 - Coluna derivada: valor_total recalculado (consistencia)
    silver = silver.withColumn(
        "valor_total_calculado",
        F.round(
            F.col("preco_unitario") * F.col("quantidade") *
            (1 - F.coalesce(F.col("desconto_pct"), F.lit(0)) / 100),
            2
        )
    )

    return silver, quarentena


# ---------------------------------------------------------------------------
# Camada GOLD - tabelas de negocio
# ---------------------------------------------------------------------------
def build_gold_atraso_por_estado_categoria(silver_df):
    """Gold 1: Taxa de atraso e atraso medio por estado e categoria."""
    return (
        silver_df
        .groupBy("estado", "categoria")
        .agg(
            F.count("*").alias("total_pedidos"),
            F.sum(F.col("atrasado").cast("int")).alias("total_atrasados"),
            F.round(
                F.sum(F.col("atrasado").cast("int")) / F.count("*") * 100, 2
            ).alias("taxa_atraso_pct"),
            F.round(F.avg(
                F.when(F.col("atrasado"), F.col("atraso_dias"))
            ), 1).alias("atraso_medio_dias"),
        )
        .orderBy(F.col("taxa_atraso_pct").desc())
    )


def build_gold_cancelamentos_devolucoes(silver_df):
    """Gold 2: Cancelamentos e devolucoes por canal, categoria e mes."""
    return (
        silver_df
        .filter(F.col("status_pedido").isin("cancelado", "devolvido"))
        .withColumn("mes_pedido", F.date_format(F.col("data_pedido"), "yyyy-MM"))
        .groupBy("mes_pedido", "canal", "categoria", "status_pedido")
        .agg(
            F.count("*").alias("quantidade"),
            F.round(F.sum("valor_total"), 2).alias("valor_total_perdido"),
        )
        .orderBy("mes_pedido", F.col("quantidade").desc())
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "INPUT", "OUTPUT_SILVER", "OUTPUT_GOLD", "OUTPUT_QUARENTENA"],
    )

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # --- raw (bronze): le o CSV como chegou ---
    raw_df = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .option("encoding", "UTF-8")
        .csv(args["INPUT"])
    )
    print(f"[raw] {raw_df.count()} linhas lidas.")

    # --- silver: limpa e padroniza ---
    silver_df, quarentena_df = build_silver(raw_df)
    print(f"[silver] {silver_df.count()} linhas aprovadas.")
    print(f"[quarentena] {quarentena_df.count()} linhas rejeitadas.")

    silver_df.write.mode("overwrite").parquet(args["OUTPUT_SILVER"] + "pedidos/")
    quarentena_df.write.mode("overwrite").parquet(
        args["OUTPUT_QUARENTENA"] + "pedidos_rejeitados/"
    )

    # --- gold: tabelas de negocio ---
    gold1 = build_gold_atraso_por_estado_categoria(silver_df)
    gold1.write.mode("overwrite").parquet(args["OUTPUT_GOLD"] + "atraso_por_estado_categoria/")
    print("[gold] atraso_por_estado_categoria gravada.")

    gold2 = build_gold_cancelamentos_devolucoes(silver_df)
    gold2.write.mode("overwrite").parquet(args["OUTPUT_GOLD"] + "cancelamentos_devolucoes/")
    print("[gold] cancelamentos_devolucoes gravada.")

    print("Pipeline concluido com sucesso.")
    job.commit()


if __name__ == "__main__":
    main()
