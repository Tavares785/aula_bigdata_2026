"""ETL medalhao (raw -> silver/quarentena -> gold) do pipeline MercadoFacil.

Roda no AWS Glue 4.0 (PySpark). Argumentos: --raw_path --silver_path
--quarantine_path --gold_path (prefixos S3). As regras estao documentadas
em aws-lab/REGRAS_SILVER.md.
"""
import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

NULL_TOKENS = ["", "-", "n/a", "null"]
PII_COLS = ["cliente_nome", "cliente_email", "cliente_cpf"]
ACENTOS = ("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
TOLERANCIA_TOTAL = 0.02

CATEGORIAS = [
    "Eletrônicos", "Moda", "Casa e Cozinha", "Esporte",
    "Beleza e Saúde", "Livros", "Brinquedos", "Pet",
]
UFS = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA",
    "CEARA": "CE", "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO",
    "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO",
    "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def unaccent(s):
    return F.translate(s, *ACENTOS)


def clean(col):
    """trim + tokens de nulo ('', '-', 'N/A', 'NULL') viram null."""
    s = F.trim(F.col(col))
    return F.when(F.lower(s).isin(NULL_TOKENS), F.lit(None)).otherwise(s)


def norm_key(col):
    return unaccent(F.lower(clean(col)))


def money(col):
    """'R$ 1.234,56' | '49,24' | '49.24' -> double."""
    s = F.regexp_replace(clean(col), r"[R$\s]", "")
    s = F.when(
        s.contains(","), F.regexp_replace(F.regexp_replace(s, r"\.", ""), ",", ".")
    ).otherwise(s)
    return s.cast("double")


def to_int(col):
    return clean(col).cast("int")


def parse_date(col):
    """ISO, ISO com hora e dd/MM/yyyy; qualquer outra coisa ('ontem') vira null."""
    s = F.substring(clean(col), 1, 10)
    return (
        F.when(s.rlike(r"^\d{4}-\d{2}-\d{2}$"), F.to_date(s, "yyyy-MM-dd"))
        .when(s.rlike(r"^\d{2}/\d{2}/\d{4}$"), F.to_date(s, "dd/MM/yyyy"))
    )


def padroniza_status(col):
    k = norm_key(col)
    return (
        F.when(k.isin("entregue", "delivered"), "ENTREGUE")
        .when(k.isin("cancelado", "canceled"), "CANCELADO")
        .when(k.isin("devolvido", "returned"), "DEVOLVIDO")
    )


def padroniza_estado(col):
    k = F.upper(norm_key(col))
    nome_para_uf = F.create_map(*[F.lit(x) for kv in UFS.items() for x in kv])
    uf = F.when(F.length(k) == 2, k).otherwise(nome_para_uf[k])
    return F.when(uf.isin(*UFS.values()), uf)


def padroniza_categoria(col):
    """Prefixo de uma categoria canonica ('Mod', 'Esport', 'Eletronico')."""
    k = norm_key(col)
    expr = F.lit(None).cast("string")
    for cat in reversed(CATEGORIAS):
        canon = unaccent(F.lit(cat.lower()))
        expr = F.when((F.length(k) >= 2) & canon.startswith(k), cat).otherwise(expr)
    return expr


def padroniza_pagamento(col):
    k = norm_key(col)
    return (
        F.when(k.contains("pix"), "PIX")
        .when(k.contains("boleto"), "BOLETO")
        .when(k.contains("debito"), "CARTAO_DEBITO")
        .when(k.contains("credito"), "CARTAO_CREDITO")
    )


def transforma_raw(raw):
    """Aplica tipagem/padronizacao e devolve o DataFrame com a coluna `motivo`."""
    w = Window.partitionBy("item_id").orderBy("_ordem")
    df = (
        raw.withColumn("_ordem", F.monotonically_increasing_id())
        .withColumn("_rn", F.row_number().over(w))
        .withColumn("preco", money("preco_unitario"))
        .withColumn("qtd", to_int("quantidade"))
        .withColumn("desc_raw", F.regexp_replace(clean("desconto_pct"), "%", "").cast("double"))
        .withColumn("total_abs", F.abs(money("valor_total")))
        .withColumn("bruto", F.col("preco") * F.col("qtd"))
        .withColumn(
            "desc_inferido",
            F.when(
                F.col("desc_raw").isNull() & F.col("total_abs").isNotNull() & (F.col("bruto") > 0),
                F.round((1 - F.col("total_abs") / F.col("bruto")) * 100, 0),
            ),
        )
        .withColumn("desconto", F.coalesce("desc_raw", "desc_inferido"))
        .withColumn("calc", F.col("bruto") * (1 - F.col("desconto") / 100))
        .withColumn("dt_pedido", parse_date("data_pedido"))
        .withColumn("uf", padroniza_estado("estado"))
        .withColumn("status", padroniza_status("status_pedido"))
        .withColumn("categoria_pad", padroniza_categoria("categoria"))
    )
    motivo = (
        F.when(F.col("_rn") > 1, "duplicado_item_id")
        .when(F.col("dt_pedido").isNull(), "data_pedido_invalida")
        .when(F.col("status").isNull(), "status_invalido")
        .when(F.col("uf").isNull(), "estado_invalido")
        .when(F.col("categoria_pad").isNull(), "categoria_invalida")
        .when(F.col("qtd").isNull() | (F.col("qtd") <= 0), "quantidade_invalida")
        .when(F.col("preco").isNull() | (F.col("preco") <= 0), "preco_invalido")
        .when(
            F.col("desconto").isNull() | (F.col("desconto") < 0) | (F.col("desconto") > 100),
            "desconto_invalido",
        )
        .when(
            F.col("desc_raw").isNotNull()
            & F.col("total_abs").isNotNull()
            & (F.abs(F.col("total_abs") - F.col("calc")) > TOLERANCIA_TOTAL),
            "valor_total_incoerente",
        )
    )
    return df.withColumn("motivo", motivo)


def monta_silver(ok):
    real = to_int("prazo_real_dias")
    estimado = F.col("prazo_estimado_dias").cast("int")
    atraso_txt = to_int("atraso_dias")
    cancelado = F.col("status") == "CANCELADO"
    nota = to_int("nota_avaliacao")
    return ok.select(
        "pedido_id",
        "item_id",
        F.col("dt_pedido").alias("data_pedido"),
        F.date_format("dt_pedido", "yyyy-MM").alias("ano_mes"),
        F.col("status").alias("status_pedido"),
        F.lower(clean("canal")).alias("canal"),
        "cliente_id",
        F.coalesce(F.lower(clean("cliente_segmento")), F.lit("nao_informado")).alias("cliente_segmento"),
        parse_date("cliente_data_cadastro").alias("cliente_data_cadastro"),
        F.col("uf").alias("estado"),
        F.trim("cidade").alias("cidade"),
        F.col("categoria_pad").alias("categoria"),
        F.trim("sku").alias("sku"),
        F.trim("produto").alias("produto"),
        F.trim("marca").alias("marca"),
        F.trim("fornecedor").alias("fornecedor"),
        money("custo_unitario").alias("custo_unitario"),
        F.col("preco").alias("preco_unitario"),
        F.col("qtd").alias("quantidade"),
        F.col("desconto").alias("desconto_pct"),
        F.coalesce("total_abs", F.round("calc", 2)).alias("valor_total"),
        padroniza_pagamento("forma_pagamento").alias("forma_pagamento"),
        to_int("parcelas").alias("parcelas"),
        F.initcap(F.lower(clean("transportadora"))).alias("transportadora"),
        F.upper(clean("centro_distribuicao")).alias("centro_distribuicao"),
        estimado.alias("prazo_estimado_dias"),
        F.when(cancelado, None).otherwise(real).alias("prazo_real_dias"),
        F.when(cancelado, None).otherwise(parse_date("data_entrega")).alias("data_entrega"),
        F.when(cancelado, None)
        .otherwise(
            F.when(real.isNotNull(), F.greatest(real - estimado, F.lit(0)))
            .otherwise(F.greatest(atraso_txt, F.lit(0)))
        )
        .alias("atraso_dias"),
        F.when(nota.between(1, 5), nota).alias("nota_avaliacao"),
        clean("comentario").alias("comentario"),
        F.col("total_abs").isNull().alias("flag_valor_total_imputado"),
        (F.col("desc_raw").isNull()).alias("flag_desconto_inferido"),
    )


def monta_gold(silver):
    entregues = silver.filter(F.col("status_pedido").isin("ENTREGUE", "DEVOLVIDO"))
    atrasado = (F.col("atraso_dias") > 0).cast("int")

    atraso = entregues.groupBy("estado", "transportadora").agg(
        F.count("*").alias("itens"),
        F.round(F.avg(atrasado), 4).alias("pct_atrasados"),
        F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
        F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
    )

    faixa = (
        F.when(F.col("atraso_dias") == 0, "0_no_prazo")
        .when(F.col("atraso_dias") <= 3, "1_a_3_dias")
        .when(F.col("atraso_dias") <= 7, "4_a_7_dias")
        .otherwise("8_ou_mais_dias")
    )
    nota_faixa = (
        entregues.filter(F.col("atraso_dias").isNotNull() & F.col("nota_avaliacao").isNotNull())
        .withColumn("faixa_atraso", faixa)
        .groupBy("faixa_atraso")
        .agg(F.count("*").alias("avaliacoes"), F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"))
    )

    cancel = silver.groupBy("categoria", "canal").agg(
        F.count("*").alias("itens"),
        F.sum((F.col("status_pedido") == "CANCELADO").cast("int")).alias("itens_cancelados"),
        F.sum((F.col("status_pedido") == "DEVOLVIDO").cast("int")).alias("itens_devolvidos"),
        F.round(F.avg((F.col("status_pedido") == "CANCELADO").cast("int")), 4).alias("pct_cancelado"),
        F.round(F.avg((F.col("status_pedido") == "DEVOLVIDO").cast("int")), 4).alias("pct_devolvido"),
        F.round(F.sum(F.when(F.col("status_pedido") == "ENTREGUE", F.col("valor_total"))), 2).alias("receita_entregue"),
    )

    mensal = silver.groupBy("ano_mes").agg(
        F.count("*").alias("itens"),
        F.countDistinct("pedido_id").alias("pedidos"),
        F.round(F.sum(F.when(F.col("status_pedido") != "CANCELADO", F.col("valor_total"))), 2).alias("receita"),
        F.round(F.avg((F.col("status_pedido") == "CANCELADO").cast("int")), 4).alias("pct_cancelado"),
        F.round(F.avg(F.when(F.col("atraso_dias").isNotNull(), (F.col("atraso_dias") > 0).cast("int"))), 4).alias("pct_atrasados"),
    )
    return {
        "gold_atraso_por_estado_transportadora": atraso,
        "gold_nota_por_faixa_atraso": nota_faixa,
        "gold_cancelamento_por_categoria_canal": cancel,
        "gold_vendas_mensal": mensal,
    }


def main():
    args = getResolvedOptions(sys.argv, ["raw_path", "silver_path", "quarantine_path", "gold_path"])
    spark = SparkSession.builder.appName("mercadofacil-etl-medalhao").getOrCreate()
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")

    raw = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .csv(args["raw_path"])  # tudo como string: o raw chega sujo
    )
    total = raw.count()

    df = transforma_raw(raw).cache()

    # Quarentena: linhas rejeitadas + motivo; sem PII direta (LGPD).
    quarentena = df.filter(F.col("motivo").isNotNull()).select(
        *[c for c in raw.columns if c not in PII_COLS], "motivo"
    )
    quarentena.write.mode("overwrite").parquet(args["quarantine_path"])

    silver = monta_silver(df.filter(F.col("motivo").isNull())).cache()
    silver.write.mode("overwrite").parquet(args["silver_path"])

    for nome, tabela in monta_gold(silver).items():
        tabela.write.mode("overwrite").parquet(args["gold_path"].rstrip("/") + "/" + nome + "/")

    print("RESUMO raw=%d silver=%d quarentena=%d" % (total, silver.count(), quarentena.count()))
    quarentena.groupBy("motivo").count().orderBy(F.desc("count")).show(truncate=False)


if __name__ == "__main__":
    main()
