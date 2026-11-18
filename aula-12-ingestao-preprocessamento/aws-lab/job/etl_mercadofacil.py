# -*- coding: utf-8 -*-
"""
Aula 12 - ETL MercadoFacil (Glue Job, PySpark)

Pipeline medalhao:
    raw  (CSV, exatamente como chega)
    -> silver (dado tipado, padronizado, dedup, PII pseudonimizada, quarentena)
    -> gold   (tabelas de negocio em Parquet para o Athena)

Argumentos recebidos do Terraform (default_arguments do aws_glue_job):
    --s3_raw_path    s3://<bucket>/raw/pedidos_mercadofacil.csv
    --s3_silver_path s3://<bucket>/silver/
    --s3_gold_path   s3://<bucket>/gold/
"""
import argparse
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--s3_raw_path", required=True)
    p.add_argument("--s3_silver_path", required=True)
    p.add_argument("--s3_gold_path", required=True)
    p.add_argument("--database_name", default="mercadofacil_db")
    return p.parse_args()


def get_spark():
    return (
        SparkSession.builder.appName("mercadofacil-etl")
        .config("spark.sql.session.timeZone", "America/Sao_Paulo")
        .getOrCreate()
    )


# ---------------------------------------------------------------------------
# raw (bronze): leitura do CSV exatamente como chega (tudo texto)
# ---------------------------------------------------------------------------
def read_raw(spark, raw_path):
    df = (
        spark.read.option("header", True)
        .option("quote", '"')
        .option("escape", '"')
        .csv(raw_path)
    )
    df.createOrReplaceTempView("raw_pedidos")
    return df


# ---------------------------------------------------------------------------
# limpeza: tipagem, padronizacao e pseudonimizacao (LGPD)
# ---------------------------------------------------------------------------
def _to_money(col):
    """'R$ 49,24' / '47,60' / '47.60' -> double."""
    cleaned = F.regexp_replace(col, r"[R$\s\"]", "")
    cleaned = F.regexp_replace(cleaned, ",", ".")
    return F.when(cleaned == "-", None).otherwise(cleaned.cast("double"))


def _to_date_flex(col):
    """Aceita 'DD/MM/AAAA' e 'AAAA-MM-DD' -> date (ISO)."""
    d1 = F.to_date(col, "dd/MM/yyyy")
    d2 = F.to_date(col, "yyyy-MM-dd")
    return F.coalesce(d1, d2)


def clean(df):
    c = df

    # datas com formatos mistos -> date
    c = c.withColumn("data_pedido_dt", _to_date_flex(F.col("data_pedido")))
    c = c.withColumn("data_cadastro_dt", _to_date_flex(F.col("cliente_data_cadastro")))
    c = c.withColumn("data_entrega_dt", _to_date_flex(F.col("data_entrega")))

    # valores monetarios (moeda e separador mistos)
    c = c.withColumn("custo_unitario_v", _to_money(F.col("custo_unitario")))
    c = c.withColumn("preco_unitario_v", _to_money(F.col("preco_unitario")))
    c = c.withColumn("valor_total_v", _to_money(F.col("valor_total")))

    # numericos com sentinelas '-' / 'N/A'
    c = c.withColumn(
        "quantidade_v",
        F.when(F.col("quantidade").isin("-", "N/A", ""), None)
        .otherwise(F.col("quantidade").cast("int")),
    )
    c = c.withColumn(
        "desconto_pct_v",
        F.when(F.col("desconto_pct").isin("-", "N/A", ""), None)
        .otherwise(F.col("desconto_pct").cast("int")),
    )
    c = c.withColumn(
        "parcelas_v",
        F.when(F.col("parcelas").isin("-", "N/A", ""), None)
        .otherwise(F.col("parcelas").cast("int")),
    )
    c = c.withColumn(
        "prazo_estimado_v",
        F.when(F.col("prazo_estimado_dias").isin("-", "N/A", ""), None)
        .otherwise(F.col("prazo_estimado_dias").cast("int")),
    )
    c = c.withColumn(
        "prazo_real_v",
        F.when(F.col("prazo_real_dias").isin("-", "N/A", ""), None)
        .otherwise(F.col("prazo_real_dias").cast("int")),
    )
    c = c.withColumn(
        "atraso_dias_v",
        F.when(F.col("atraso_dias").isin("-", "N/A", ""), None)
        .otherwise(F.col("atraso_dias").cast("int")),
    )
    c = c.withColumn(
        "nota_avaliacao_v",
        F.when(F.col("nota_avaliacao").isin("-", "N/A", ""), None)
        .otherwise(F.col("nota_avaliacao").cast("int")),
    )

    # status padronizado (entregue/ENTREGUE/DELIVERED -> enum canonicas)
    s = F.lower(F.trim(F.col("status_pedido")))
    c = c.withColumn(
        "status_v",
        F.when(s.isin("entregue", "delivered"), "entregue")
        .when(s.isin("cancelado", "canceled", "cancelled"), "cancelado")
        .when(s.isin("devolvido", "returned"), "devolvido")
        .when(s.isin("enviado", "shipped"), "enviado")
        .when(s.isin("processando", "processing"), "processando")
        .otherwise(s),
    )

    # forma de pagamento padronizada
    f = F.lower(F.trim(F.col("forma_pagamento")))
    c = c.withColumn(
        "forma_pagamento_v",
        F.when(f.contains("credito"), "cartao_credito")
        .when(f.contains("debito"), "cartao_debito")
        .when(f.contains("pix"), "pix")
        .when(f.contains("boleto"), "boleto")
        .otherwise(f),
    )

    # categorias/estados: trim e caixa unica
    c = c.withColumn("categoria_v", F.initcap(F.trim(F.col("categoria"))))
    c = c.withColumn("estado_v", F.upper(F.trim(F.col("estado"))))
    c = c.withColumn("cidade_v", F.trim(F.col("cidade")))
    c = c.withColumn("canal_v", F.lower(F.trim(F.col("canal"))))
    c = c.withColumn(
        "transportadora_v", F.initcap(F.trim(F.col("transportadora")))
    )
    c = c.withColumn(
        "centro_distribuicao_v", F.upper(F.trim(F.col("centro_distribuicao")))
    )

    # comentario: 'N/A'/vazio -> null
    c = c.withColumn(
        "comentario_v",
        F.nullif(F.trim(F.col("comentario")), F.lit("N/A")),
    )

    # LGPD: pseudonimizacao de PII (nome, e-mail e CPF -> SHA-256)
    c = c.withColumn("cliente_cpf_hash", F.sha2(F.trim(F.col("cliente_cpf")), 256))
    c = c.withColumn(
        "cliente_email_hash", F.sha2(F.lower(F.trim(F.col("cliente_email"))), 256)
    )
    c = c.withColumn("cliente_nome_hash", F.sha2(F.trim(F.col("cliente_nome")), 256))

    # dedup: chave natural (pedido_id, item_id); mantem a primeira ocorrencia
    w = Window.partitionBy("pedido_id", "item_id").orderBy("cliente_id")
    c = c.withColumn("_rn", F.row_number().over(w))

    c = c.dropDuplicates(["pedido_id", "item_id"])
    return c


# ---------------------------------------------------------------------------
# quarentena: linhas que nao podem entrar na silver (com o motivo)
# ---------------------------------------------------------------------------
def build_quarantine(cleaned):
    motivos = [
        cleaned.filter(
            F.col("pedido_id").isNull() | F.col("item_id").isNull()
        ).withColumn("motivo", F.lit("chave_pedido_item_invalida")),
        cleaned.filter(F.col("data_pedido_dt").isNull()).withColumn(
            "motivo", F.lit("data_pedido_invalida_ou_ausente")
        ),
        cleaned.filter(
            F.col("quantidade_v").isNull() | (F.col("quantidade_v") <= 0)
        ).withColumn("motivo", F.lit("quantidade_invalida")),
        cleaned.filter(
            F.col("valor_total_v").isNull() & (F.col("status_v") == "entregue")
        ).withColumn("motivo", F.lit("valor_total_invalido_em_entregue")),
    ]
    return motivos[0].unionByName(*motivos[1:]).withColumn(
        "_rn", F.lit(0)
    )


# ---------------------------------------------------------------------------
# silver: apenas linhas validas, com colunas finais tipadas
# ---------------------------------------------------------------------------
def build_silver(cleaned, quarantine):
    bad = quarantine.select("pedido_id", "item_id", "motivo")
    silver = (
        cleaned.join(bad, on=["pedido_id", "item_id"], how="left_anti")
        .filter(F.col("_rn") == 1)
    )

    silver = silver.select(
        "pedido_id",
        "item_id",
        F.col("data_pedido_dt").alias("data_pedido"),
        "cliente_id",
        "cliente_nome_hash",
        "cliente_email_hash",
        "cliente_cpf_hash",
        F.trim(F.col("cliente_segmento")).alias("cliente_segmento"),
        F.col("data_cadastro_dt").alias("cliente_data_cadastro"),
        "estado_v",
        "cidade_v",
        "canal_v",
        "categoria_v",
        "sku",
        F.trim(F.col("produto")).alias("produto"),
        F.trim(F.col("marca")).alias("marca"),
        F.trim(F.col("fornecedor")).alias("fornecedor"),
        "custo_unitario_v",
        "preco_unitario_v",
        "quantidade_v",
        "desconto_pct_v",
        "valor_total_v",
        "forma_pagamento_v",
        "parcelas_v",
        "status_v",
        "transportadora_v",
        "centro_distribuicao_v",
        "prazo_estimado_v",
        "prazo_real_v",
        "data_entrega_dt",
        "atraso_dias_v",
        "nota_avaliacao_v",
        "comentario_v",
    )
    return silver


# ---------------------------------------------------------------------------
# gold: tabelas de negocio (>= 2) para as perguntas do projeto
# ---------------------------------------------------------------------------
def build_gold(silver):
    fato = silver.select(
        "pedido_id",
        "item_id",
        "data_pedido",
        "data_entrega_dt",
        "estado_v",
        "cidade_v",
        "canal_v",
        "categoria_v",
        "sku",
        "status_v",
        "transportadora_v",
        "centro_distribuicao_v",
        "prazo_estimado_v",
        "prazo_real_v",
        "atraso_dias_v",
        "quantidade_v",
        "preco_unitario_v",
        "valor_total_v",
        "forma_pagamento_v",
        "parcelas_v",
        "nota_avaliacao_v",
        "comentario_v",
        F.coalesce(F.col("atraso_dias_v"), F.lit(0)).alias("atraso_dias_0"),
    )
    fato = fato.withColumn(
        "atrasou", F.when(F.col("atraso_dias_0") > 0, True).otherwise(False)
    )
    fato = fato.drop("atraso_dias_0")

    faixa = (
        F.when(F.col("atraso_dias_v").isNull(), "sem_entrega")
        .when(F.col("atraso_dias_v") == 0, "no_prazo")
        .when(F.col("atraso_dias_v") <= 5, "1_5_dias")
        .when(F.col("atraso_dias_v") <= 10, "6_10_dias")
        .otherwise("mais_10_dias")
    )

    atraso_nota = (
        fato.groupBy(faixa.alias("faixa_atraso"))
        .agg(
            F.count(F.lit(1)).alias("itens"),
            F.round(F.avg("nota_avaliacao_v"), 2).alias("nota_media"),
            F.round(
                F.avg(F.when(F.col("atrasou"), 1.0).otherwise(0.0)), 4
            ).alias("taxa_atraso"),
            F.round(F.avg("prazo_real_v"), 2).alias("prazo_medio_dias"),
        )
        .orderBy("faixa_atraso")
    )

    sazonal = (
        fato.withColumn("ano_mes", F.date_format("data_pedido", "yyyy-MM"))
        .groupBy("ano_mes", "canal_v")
        .agg(
            F.countDistinct("pedido_id").alias("pedidos"),
            F.round(F.sum("valor_total_v"), 2).alias("receita_total"),
            F.sum(
                F.when(F.col("status_v").isin("cancelado", "devolvido"), 1)
                .otherwise(0)
            ).alias("cancelamentos_devolucoes"),
            F.round(F.avg("atraso_dias_v"), 2).alias("atraso_medio_dias"),
        )
        .orderBy("ano_mes", "canal_v")
    )

    return fato, atraso_nota, sazonal


def main():
    args = parse_args()
    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = read_raw(spark, args.s3_raw_path)
    print(f"raw: {raw.count()} linhas")

    cleaned = clean(raw)
    quarantine = build_quarantine(cleaned)
    silver = build_silver(cleaned, quarantine)
    print(f"silver: {silver.count()} linhas | quarentena: {quarantine.count()} linhas")

    fato, atraso_nota, sazonal = build_gold(silver)

    os.makedirs("/tmp", exist_ok=True)  # no-op seguro no Glue

    # silver (Parquet) + area de quarentena
    silver.write.mode("overwrite").parquet(args.s3_silver_path)
    quarantine.write.mode("overwrite").parquet(
        args.s3_silver_path.replace("silver/", "quarentena/")
    )

    # gold (Parquet): fato_entregas, agregado_atraso_nota, sazonalidade_mensal
    fato.write.mode("overwrite").parquet(args.s3_gold_path + "fato_entregas/")
    atraso_nota.write.mode("overwrite").parquet(args.s3_gold_path + "agregado_atraso_nota/")
    sazonal.write.mode("overwrite").parquet(args.s3_gold_path + "sazonalidade_mensal/")

    print("ETL concluido: silver, quarentena e gold gravados.")
    spark.stop()


if __name__ == "__main__":
    main()
