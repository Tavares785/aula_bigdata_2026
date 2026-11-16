"""
ETL MercadoFacil (Glue 4.0 / PySpark) - arquitetura medalhao.

raw (CSV, sem alteracao) -> silver (Parquet limpo) + quarantine (Parquet com
motivo) -> gold (Parquet, tabelas de negocio).

As regras de limpeza estao documentadas em aws-lab/REGRAS_SILVER.md.
Argumentos (passados pelo Terraform): --raw_path --silver_path --gold_path
--quarantine_path.
"""
import argparse
import sys

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

NULL_TOKENS = ["", "N/A", "NULL", "-", "NAN", "NONE"]

ACCENTS_FROM = "áàâãäéèêëíìîïóòôõöúùûüç"
ACCENTS_TO = "aaaaaeeeeiiiiooooouuuuc"

UF_POR_NOME = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM",
    "bahia": "BA", "ceara": "CE", "distrito federal": "DF",
    "espirito santo": "ES", "goias": "GO", "maranhao": "MA",
    "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE",
    "piaui": "PI", "rio de janeiro": "RJ", "rio grande do norte": "RN",
    "rio grande do sul": "RS", "rondonia": "RO", "roraima": "RR",
    "santa catarina": "SC", "sao paulo": "SP", "sergipe": "SE",
    "tocantins": "TO",
}
UFS_VALIDAS = sorted(set(UF_POR_NOME.values()))

RAW_COLS = [
    "pedido_id", "item_id", "data_pedido", "cliente_id", "cliente_nome",
    "cliente_email", "cliente_cpf", "cliente_segmento",
    "cliente_data_cadastro", "estado", "cidade", "canal", "categoria", "sku",
    "produto", "marca", "fornecedor", "custo_unitario", "preco_unitario",
    "quantidade", "desconto_pct", "valor_total", "forma_pagamento",
    "parcelas", "status_pedido", "transportadora", "centro_distribuicao",
    "prazo_estimado_dias", "prazo_real_dias", "data_entrega", "atraso_dias",
    "nota_avaliacao", "comentario",
]


# --------------------------------------------------------------------------
# Funcoes de limpeza (colunas Spark)
# --------------------------------------------------------------------------
def blank_to_null(col):
    """Remove espacos e transforma '', N/A, NULL, '-' em nulo."""
    t = F.trim(col)
    return F.when(~F.upper(t).isin(NULL_TOKENS), t)


def strip_accents_lower(col):
    return F.translate(F.lower(F.trim(col)), ACCENTS_FROM, ACCENTS_TO)


def to_int(col):
    s = blank_to_null(col)
    return F.when(s.rlike(r"^-?\d+$"), s.cast("int"))


def to_money(col):
    """'R$ 1.234,56' / '1234,56' / '1234.56' -> double."""
    s = F.trim(F.regexp_replace(blank_to_null(col), r"[Rr]\$", ""))
    br = F.regexp_replace(F.regexp_replace(s, r"\.", ""), ",", ".")
    num = F.when(s.contains(","), br).otherwise(s)
    return F.when(num.rlike(r"^-?\d+(\.\d+)?$"), num.cast("double"))


def to_percent(col):
    s = F.trim(F.regexp_replace(blank_to_null(col), "%", ""))
    return F.when(s.rlike(r"^\d+(\.\d+)?$"), s.cast("double"))


def to_date_multi(col):
    """Aceita yyyy-MM-dd, dd/MM/yyyy e yyyy-MM-dd HH:mm:ss."""
    s = blank_to_null(col)
    iso = F.when(
        s.rlike(r"^\d{4}-\d{2}-\d{2}"),
        F.to_date(F.substring(s, 1, 10), "yyyy-MM-dd"),
    )
    br = F.when(
        s.rlike(r"^\d{2}/\d{2}/\d{4}"),
        F.to_date(F.substring(s, 1, 10), "dd/MM/yyyy"),
    )
    return F.coalesce(iso, br)


def mode_by(df, key_cols, value_col, out_col):
    """Anexa a `out_col` o valor mais frequente de `value_col` por chave."""
    counts = (
        df.where(F.col(value_col).isNotNull())
        .groupBy(*key_cols, value_col)
        .count()
    )
    w = Window.partitionBy(*key_cols).orderBy(F.desc("count"), F.col(value_col))
    ref = (
        counts.withColumn("_rn", F.row_number().over(w))
        .where("_rn = 1")
        .select(*key_cols, F.col(value_col).alias(out_col))
    )
    return df.join(ref, on=key_cols, how="left")


def sub(path, name):
    return path.rstrip("/") + "/" + name + "/"


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
def clean(raw):
    """Aplica as regras de padronizacao; mantem as colunas originais."""
    uf_map = F.create_map(
        *[F.lit(x) for kv in UF_POR_NOME.items() for x in kv]
    )
    estado_up = F.upper(F.trim(F.col("estado")))
    estado_key = strip_accents_lower(F.col("estado"))
    forma_key = strip_accents_lower(F.col("forma_pagamento"))
    status_key = strip_accents_lower(F.col("status_pedido"))

    df = (
        raw
        .withColumn("c_pedido_id", F.upper(blank_to_null(F.col("pedido_id"))))
        .withColumn("c_item_id", F.upper(blank_to_null(F.col("item_id"))))
        .withColumn("c_data_pedido", to_date_multi(F.col("data_pedido")))
        .withColumn(
            "c_status",
            F.when(status_key.rlike("entreg|deliver"), "entregue")
            .when(status_key.rlike("cancel"), "cancelado")
            .when(status_key.rlike("devolv|return"), "devolvido"),
        )
        .withColumn("c_canal", F.lower(blank_to_null(F.col("canal"))))
        .withColumn("c_cliente_id", F.upper(blank_to_null(F.col("cliente_id"))))
        .withColumn(
            "c_segmento",
            F.coalesce(
                F.lower(blank_to_null(F.col("cliente_segmento"))),
                F.lit("nao_informado"),
            ),
        )
        .withColumn("c_data_cadastro", to_date_multi(F.col("cliente_data_cadastro")))
        .withColumn(
            "c_estado",
            F.when(F.length(estado_up) == 2, estado_up).otherwise(
                F.element_at(uf_map, estado_key)
            ),
        )
        .withColumn("c_cidade_t", blank_to_null(F.col("cidade")))
        .withColumn(
            "cidade_key",
            F.regexp_replace(strip_accents_lower(F.col("cidade")), r"\s+", " "),
        )
        .withColumn("c_sku", F.upper(blank_to_null(F.col("sku"))))
        .withColumn("c_categoria_t", blank_to_null(F.col("categoria")))
        .withColumn("c_produto_t", blank_to_null(F.col("produto")))
        .withColumn("c_marca_t", blank_to_null(F.col("marca")))
        .withColumn("c_fornecedor_t", blank_to_null(F.col("fornecedor")))
        .withColumn("c_custo", to_money(F.col("custo_unitario")))
        .withColumn("c_preco", to_money(F.col("preco_unitario")))
        .withColumn("c_qtd", to_int(F.col("quantidade")))
        .withColumn("c_desc", to_percent(F.col("desconto_pct")))
        .withColumn("c_total_src", to_money(F.col("valor_total")))
        .withColumn(
            "c_forma",
            F.when(forma_key.contains("credito"), "cartao_credito")
            .when(forma_key.contains("debito"), "cartao_debito")
            .when(forma_key.contains("pix"), "pix")
            .when(forma_key.contains("boleto"), "boleto"),
        )
        .withColumn("c_parcelas_src", to_int(F.col("parcelas")))
        .withColumn(
            "c_transportadora_t",
            F.lower(blank_to_null(F.col("transportadora"))),
        )
        .withColumn("c_cd", F.upper(blank_to_null(F.col("centro_distribuicao"))))
        .withColumn("c_prazo_est", to_int(F.col("prazo_estimado_dias")))
        .withColumn("c_prazo_real_src", to_int(F.col("prazo_real_dias")))
        .withColumn("c_data_entrega", to_date_multi(F.col("data_entrega")))
        .withColumn("c_atraso_src", to_int(F.col("atraso_dias")))
        .withColumn("c_nota_src", to_int(F.col("nota_avaliacao")))
        .withColumn("c_comentario", blank_to_null(F.col("comentario")))
        .withColumn(
            "c_cpf_digitos", F.regexp_replace(F.col("cliente_cpf"), r"\D", "")
        )
        .withColumn("c_email", F.lower(blank_to_null(F.col("cliente_email"))))
    )

    # Referencia por SKU e por chave normalizada: valor mais frequente.
    df = mode_by(df, ["cidade_key"], "c_cidade_t", "ref_cidade")
    df = mode_by(df, ["c_sku"], "c_categoria_t", "ref_categoria")
    df = mode_by(df, ["c_sku"], "c_produto_t", "ref_produto")
    df = mode_by(df, ["c_sku"], "c_marca_t", "ref_marca")
    df = mode_by(df, ["c_sku"], "c_fornecedor_t", "ref_fornecedor")

    desc_ok = F.coalesce(F.col("c_desc").between(0, 100), F.lit(False))
    desc_final = F.when(desc_ok, F.col("c_desc")).otherwise(F.lit(0.0))
    valor_calc = F.round(
        F.col("c_preco") * F.col("c_qtd") * (1 - desc_final / 100), 2
    )
    total_consistente = (
        F.col("c_total_src").isNotNull()
        & desc_ok
        & (F.abs(valor_calc - F.col("c_total_src")) <= 0.02)
    )

    df = (
        df
        .withColumn("s_categoria", F.coalesce("ref_categoria", "c_categoria_t"))
        .withColumn("s_cidade", F.coalesce("ref_cidade", "c_cidade_t"))
        .withColumn("s_transportadora", F.initcap("c_transportadora_t"))
        .withColumn("s_desconto", desc_final)
        .withColumn("flag_desconto_imputado", ~desc_ok)
        .withColumn(
            "s_valor_total",
            F.when(
                F.col("c_total_src").isNotNull() & ~desc_ok, F.col("c_total_src")
            ).otherwise(
                F.when(total_consistente, F.col("c_total_src")).otherwise(valor_calc)
            ),
        )
        .withColumn(
            "flag_valor_corrigido",
            F.coalesce(
                F.col("c_total_src").isNotNull()
                & desc_ok
                & ~total_consistente
                & valor_calc.isNotNull(),
                F.lit(False),
            ),
        )
        .withColumn(
            "s_parcelas",
            F.when(F.col("c_parcelas_src") >= 1, F.col("c_parcelas_src")).otherwise(
                F.when(F.col("c_forma").isin("pix", "boleto", "cartao_debito"), 1)
            ),
        )
        .withColumn(
            "s_prazo_real",
            F.coalesce(
                F.when(F.col("c_prazo_real_src") >= 0, F.col("c_prazo_real_src")),
                F.when(
                    F.col("c_data_entrega").isNotNull()
                    & F.col("c_data_pedido").isNotNull()
                    & (F.col("c_data_entrega") >= F.col("c_data_pedido")),
                    F.datediff("c_data_entrega", "c_data_pedido"),
                ),
            ),
        )
        .withColumn(
            "s_atraso",
            F.coalesce(
                F.when(
                    F.col("s_prazo_real").isNotNull() & F.col("c_prazo_est").isNotNull(),
                    F.greatest(F.col("s_prazo_real") - F.col("c_prazo_est"), F.lit(0)),
                ),
                F.when(F.col("c_atraso_src") >= 0, F.col("c_atraso_src")),
            ),
        )
        .withColumn("s_nota", F.when(F.col("c_nota_src").between(1, 5), F.col("c_nota_src")))
        .withColumn(
            "cpf_valido", F.coalesce(F.length("c_cpf_digitos") == 11, F.lit(False))
        )
        .withColumn(
            "s_cpf_hash",
            F.when(F.col("cpf_valido"), F.sha2(F.col("c_cpf_digitos"), 256)),
        )
        .withColumn(
            "s_email_hash",
            F.when(
                F.col("c_email").rlike(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
                F.sha2(F.col("c_email"), 256),
            ),
        )
    )

    # Motivos de quarentena (o primeiro que se aplicar).
    motivo = (
        F.when(F.col("c_item_id").isNull(), "item_id_ausente")
        .when(F.col("c_data_pedido").isNull(), "data_pedido_invalida")
        .when(F.col("c_status").isNull(), "status_invalido")
        .when(F.col("c_estado").isNull() | ~F.col("c_estado").isin(UFS_VALIDAS), "estado_invalido")
        .when(F.col("s_categoria").isNull(), "categoria_ausente")
        .when(F.col("c_qtd").isNull() | (F.col("c_qtd") <= 0), "quantidade_invalida")
        .when(F.col("c_preco").isNull() | (F.col("c_preco") <= 0), "preco_invalido")
        .when(F.col("s_valor_total").isNull(), "valor_total_indeterminado")
    )
    return df.withColumn("motivo", motivo)


def split_silver_quarantine(df):
    invalid = df.where(F.col("motivo").isNotNull())

    completude = sum(
        F.when(F.col(c).isNotNull(), 1).otherwise(0)
        for c in ["c_nota_src", "c_comentario", "c_prazo_real_src", "c_data_entrega",
                  "c_email", "c_cpf_digitos", "c_forma", "c_cd"]
    )
    w = Window.partitionBy("c_item_id").orderBy(F.desc("_completude"))
    valid = (
        df.where(F.col("motivo").isNull())
        .withColumn("_completude", completude)
        .withColumn("_rn", F.row_number().over(w))
    )
    dupes = valid.where("_rn > 1").withColumn("motivo", F.lit("duplicado"))
    silver_df = valid.where("_rn = 1")

    # Na quarentena, dados pessoais tambem viram hash (LGPD).
    pii = {"cliente_nome", "cliente_email", "cliente_cpf"}
    cols = [
        F.sha2(F.col(c), 256).alias(c) if c in pii else F.col(c)
        for c in RAW_COLS
    ] + [F.col("motivo")]
    quarantine = invalid.select(*cols).unionByName(dupes.select(*cols))

    silver = silver_df.select(
        F.col("c_pedido_id").alias("pedido_id"),
        F.col("c_item_id").alias("item_id"),
        F.col("c_data_pedido").alias("data_pedido"),
        F.date_format("c_data_pedido", "yyyy-MM").alias("ano_mes"),
        F.col("c_status").alias("status_pedido"),
        F.col("c_canal").alias("canal"),
        F.col("c_cliente_id").alias("cliente_id"),
        F.col("s_cpf_hash").alias("cliente_cpf_hash"),
        F.col("s_email_hash").alias("cliente_email_hash"),
        F.col("c_segmento").alias("cliente_segmento"),
        F.col("c_data_cadastro").alias("cliente_data_cadastro"),
        F.col("c_estado").alias("estado"),
        F.col("s_cidade").alias("cidade"),
        F.col("s_categoria").alias("categoria"),
        F.col("c_sku").alias("sku"),
        F.coalesce("ref_produto", "c_produto_t").alias("produto"),
        F.coalesce("ref_marca", "c_marca_t").alias("marca"),
        F.coalesce("ref_fornecedor", "c_fornecedor_t").alias("fornecedor"),
        F.col("c_custo").alias("custo_unitario"),
        F.col("c_preco").alias("preco_unitario"),
        F.col("c_qtd").alias("quantidade"),
        F.col("s_desconto").alias("desconto_pct"),
        F.col("s_valor_total").alias("valor_total"),
        F.col("c_forma").alias("forma_pagamento"),
        F.col("s_parcelas").alias("parcelas"),
        F.col("s_transportadora").alias("transportadora"),
        F.col("c_cd").alias("centro_distribuicao"),
        F.col("c_prazo_est").alias("prazo_estimado_dias"),
        F.col("s_prazo_real").alias("prazo_real_dias"),
        F.col("c_data_entrega").alias("data_entrega"),
        F.col("s_atraso").alias("atraso_dias"),
        (F.col("s_atraso") > 0).alias("atrasado"),
        F.col("s_nota").alias("nota_avaliacao"),
        F.col("c_comentario").alias("comentario"),
        F.col("cpf_valido"),
        F.col("flag_desconto_imputado"),
        F.col("flag_valor_corrigido"),
    )
    return silver, quarantine


def build_gold(silver):
    entregues = silver.where(
        F.col("status_pedido").isin("entregue", "devolvido")
        & F.col("atraso_dias").isNotNull()
    )
    atraso_estado_transp = entregues.groupBy("estado", "transportadora").agg(
        F.count("*").alias("itens_entregues"),
        F.sum(F.col("atrasado").cast("int")).alias("itens_atrasados"),
        F.round(F.avg(F.col("atrasado").cast("int")) * 100, 2).alias("pct_atraso"),
        F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
        F.round(F.avg("prazo_real_dias"), 2).alias("prazo_real_medio_dias"),
    )

    faixa = (
        F.when(F.col("atraso_dias") == 0, "1_no_prazo")
        .when(F.col("atraso_dias") <= 3, "2_atraso_1_a_3_dias")
        .when(F.col("atraso_dias") <= 7, "3_atraso_4_a_7_dias")
        .otherwise("4_atraso_8_ou_mais_dias")
    )
    nota_faixa = (
        entregues.where(F.col("nota_avaliacao").isNotNull())
        .withColumn("faixa_atraso", faixa)
        .groupBy("faixa_atraso")
        .agg(
            F.count("*").alias("itens_avaliados"),
            F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
            F.round(
                F.avg((F.col("nota_avaliacao") <= 2).cast("int")) * 100, 2
            ).alias("pct_nota_baixa"),
        )
    )

    vendas = silver.groupBy("ano_mes", "categoria").agg(
        F.count("*").alias("itens"),
        F.countDistinct("pedido_id").alias("pedidos"),
        F.sum("quantidade").alias("unidades"),
        F.round(F.sum("valor_total"), 2).alias("receita_bruta"),
        F.round(
            F.sum(F.when(F.col("status_pedido") == "entregue", F.col("valor_total"))), 2
        ).alias("receita_entregue"),
        F.sum((F.col("status_pedido") == "cancelado").cast("int")).alias("itens_cancelados"),
        F.sum((F.col("status_pedido") == "devolvido").cast("int")).alias("itens_devolvidos"),
        F.round(
            F.avg((F.col("status_pedido") == "cancelado").cast("int")) * 100, 2
        ).alias("pct_cancelamento"),
        F.round(
            F.avg((F.col("status_pedido") == "devolvido").cast("int")) * 100, 2
        ).alias("pct_devolucao"),
    )
    return atraso_estado_transp, nota_faixa, vendas


def main(argv):
    p = argparse.ArgumentParser()
    for name in ("raw_path", "silver_path", "gold_path", "quarantine_path"):
        p.add_argument(f"--{name}", required=True)
    args, _ = p.parse_known_args(argv)  # ignora args do Glue (--JOB_NAME etc.)

    spark = SparkSession.builder.appName("etl-pedidos-mercadofacil").getOrCreate()
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")

    # RAW (bronze): leitura fiel, tudo como texto.
    raw = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .option("encoding", "UTF-8")
        .csv(args.raw_path)
    )

    cleaned = clean(raw)
    silver, quarantine = split_silver_quarantine(cleaned)
    silver = silver.cache()
    quarantine = quarantine.cache()

    # SILVER e QUARENTENA (overwrite evita duplicar em reexecucoes).
    silver.write.mode("overwrite").parquet(sub(args.silver_path, "pedidos_itens"))
    quarantine.write.mode("overwrite").parquet(
        sub(args.quarantine_path, "pedidos_rejeitados")
    )

    # GOLD
    atraso, nota, vendas = build_gold(silver)
    atraso.write.mode("overwrite").parquet(
        sub(args.gold_path, "atraso_por_estado_transportadora")
    )
    nota.write.mode("overwrite").parquet(sub(args.gold_path, "nota_por_faixa_atraso"))
    vendas.write.mode("overwrite").parquet(
        sub(args.gold_path, "vendas_mensais_categoria")
    )

    print(f"raw={raw.count()} silver={silver.count()} quarentena={quarantine.count()}")
    quarantine.groupBy("motivo").count().show(truncate=False)
    spark.stop()


if __name__ == "__main__":
    main(sys.argv[1:])
