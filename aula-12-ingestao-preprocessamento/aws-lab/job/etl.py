"""
ETL MercadoFácil — Arquitetura Medalhão (raw → silver → gold)
Glue Job (PySpark, Glue 4.0)

Argumentos esperados:
  --RAW_PATH    s3://<bucket>/raw/pedidos_mercadofacil.csv
  --SILVER_PATH s3://<bucket>/silver/
  --GOLD_PATH   s3://<bucket>/gold/
"""

import sys
import hashlib
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, DateType

# ---------------------------------------------------------------------------
# 1. Inicialização
# ---------------------------------------------------------------------------
args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "RAW_PATH", "SILVER_PATH", "GOLD_PATH"]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

RAW_PATH    = args["RAW_PATH"]
SILVER_PATH = args["SILVER_PATH"]
GOLD_PATH   = args["GOLD_PATH"]

# ---------------------------------------------------------------------------
# 2. RAW (bronze) — leitura sem alterações
# ---------------------------------------------------------------------------
raw_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")   # tudo como string, como chega
    .option("multiLine", "true")
    .option("quote", '"')
    .option("escape", '"')
    .csv(RAW_PATH)
)

print(f"[RAW] linhas lidas: {raw_df.count()}")

# ---------------------------------------------------------------------------
# 3. SILVER — limpeza, tipagem, padronização
# ---------------------------------------------------------------------------

# ---- Helper: parse de datas com múltiplos formatos -------------------------
def parse_date_col(col_name):
    """Tenta YYYY-MM-DD, dd/MM/yyyy e YYYY-MM-DD HH:mm:ss nessa ordem."""
    return (
        F.coalesce(
            F.to_date(F.col(col_name), "yyyy-MM-dd"),
            F.to_date(F.col(col_name), "dd/MM/yyyy"),
            F.to_date(F.regexp_extract(F.col(col_name), r"^(\d{4}-\d{2}-\d{2})", 1), "yyyy-MM-dd"),
        )
    )

# ---- Helper: limpeza de valores monetários ---------------------------------
def clean_money(col_name):
    """Remove 'R$', espaços, pontos-milhar; troca vírgula-decimal por ponto."""
    return F.regexp_replace(
        F.regexp_replace(
            F.regexp_replace(F.trim(F.col(col_name)), r"R\$\s*", ""),
            r"\.",   # ponto separador de milhar (ex: 1.517)
            ""
        ),
        ",", "."
    ).cast(DoubleType())

# ---- Helper: limpeza de percentual -----------------------------------------
def clean_pct(col_name):
    cleaned = F.regexp_replace(F.trim(F.col(col_name)), "%", "")
    return F.when(
        cleaned.isin("N/A", "-", "null", "NULL", ""),
        F.lit(None)
    ).otherwise(cleaned.cast(DoubleType()))

# ---- Helper: sentinelas → NULL ---------------------------------------------
SENTINELS = ["N/A", "null", "NULL", "-", ""]

def nullify(col_name):
    return F.when(F.trim(F.col(col_name)).isin(SENTINELS), F.lit(None)).otherwise(F.trim(F.col(col_name)))

# ---- Helper: hash SHA-256 (LGPD) -------------------------------------------
@F.udf("string")
def sha256_udf(value):
    if value is None:
        return None
    digits = "".join(filter(str.isdigit, value))
    return hashlib.sha256(digits.encode()).hexdigest()

# ---- Mapa de normalização de status ----------------------------------------
STATUS_MAP = {
    "entregue": "entregue",
    "delivered": "entregue",
    "cancelado": "cancelado",
    "cancelled": "cancelado",
    "devolvido": "devolvido",
    "returned": "devolvido",
    "em_transito": "em_transito",
    "processando": "processando",
}

STATUS_VALID = list(STATUS_MAP.values())

def normalize_status(col_name):
    lowered = F.lower(F.trim(F.col(col_name)))
    expr = F.lit(None).cast("string")
    for k, v in STATUS_MAP.items():
        expr = F.when(lowered == k, v).otherwise(expr)
    return expr

# ---- Mapa de normalização de UF --------------------------------------------
UF_MAP = {
    "distrito federal": "DF",
    "são paulo": "SP",
    "rio de janeiro": "RJ",
    "minas gerais": "MG",
    "bahia": "BA",
    "ceará": "CE",
    "pernambuco": "PE",
    "amazonas": "AM",
    "pará": "PA",
    "paraná": "PR",
    "rio grande do sul": "RS",
    "santa catarina": "SC",
    "goiás": "GO",
}

VALID_UFS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
    "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
]

def normalize_uf(col_name):
    lowered = F.lower(F.trim(F.col(col_name)))
    upper   = F.upper(F.trim(F.col(col_name)))
    # substitui nome por extenso pela sigla
    expr = upper
    for name, sigla in UF_MAP.items():
        expr = F.when(lowered == name, sigla).otherwise(expr)
    return expr

# ---------------------------------------------------------------------------
# 3a. Aplicar transformações
# ---------------------------------------------------------------------------
silver_df = (
    raw_df
    # --- trim geral em todas as colunas string ---
    .select([F.trim(F.col(c)).alias(c) for c in raw_df.columns])

    # --- sentinelas → NULL ---
    .withColumn("cliente_cpf",        nullify("cliente_cpf"))
    .withColumn("nota_avaliacao",     nullify("nota_avaliacao"))
    .withColumn("atraso_dias",        nullify("atraso_dias"))
    .withColumn("prazo_real_dias",    nullify("prazo_real_dias"))
    .withColumn("parcelas",           nullify("parcelas"))
    .withColumn("comentario",         nullify("comentario"))
    .withColumn("fornecedor",         nullify("fornecedor"))
    .withColumn("data_entrega",       nullify("data_entrega"))

    # --- datas ---
    .withColumn("data_pedido",           parse_date_col("data_pedido"))
    .withColumn("data_entrega",          parse_date_col("data_entrega"))
    .withColumn("cliente_data_cadastro", parse_date_col("cliente_data_cadastro"))

    # --- valores monetários ---
    .withColumn("preco_unitario", clean_money("preco_unitario"))
    .withColumn("custo_unitario", clean_money("custo_unitario"))
    .withColumn("valor_total",    clean_money("valor_total"))

    # --- numéricos simples ---
    .withColumn("desconto_pct",       clean_pct("desconto_pct"))
    .withColumn("quantidade",         F.col("quantidade").cast(IntegerType()))
    .withColumn("parcelas",           F.col("parcelas").cast(IntegerType()))
    .withColumn("prazo_estimado_dias",F.col("prazo_estimado_dias").cast(IntegerType()))
    .withColumn("prazo_real_dias",    F.col("prazo_real_dias").cast(IntegerType()))
    .withColumn("atraso_dias",        F.col("atraso_dias").cast(IntegerType()))
    .withColumn("nota_avaliacao",     F.col("nota_avaliacao").cast(IntegerType()))

    # --- status_pedido ---
    .withColumn("status_pedido", normalize_status("status_pedido"))

    # --- estado / cidade ---
    .withColumn("estado", normalize_uf("estado"))
    .withColumn("cidade", F.initcap(F.col("cidade")))

    # --- categoria / canal / forma_pagamento: minúsculas ---
    .withColumn("categoria",       F.lower(F.col("categoria")))
    .withColumn("canal",           F.lower(F.col("canal")))
    .withColumn("forma_pagamento", F.lower(F.trim(F.col("forma_pagamento"))))
    .withColumn("cliente_segmento",F.lower(F.trim(F.col("cliente_segmento"))))

    # --- LGPD: pseudonimizar CPF ---
    .withColumn("cliente_cpf_hash", sha256_udf(F.col("cliente_cpf")))
    .drop("cliente_cpf")           # remove CPF original

    # --- e-mail: minúsculas ---
    .withColumn("cliente_email", F.lower(F.col("cliente_email")))

    # --- nome: padronização ---
    .withColumn("cliente_nome", F.initcap(F.col("cliente_nome")))

    # --- flag de inconsistência de atraso ---
    .withColumn(
        "flag_atraso_inconsistente",
        F.when(
            (F.col("prazo_real_dias").isNotNull()) &
            (F.col("prazo_estimado_dias").isNotNull()) &
            (F.abs(F.col("atraso_dias") - (F.col("prazo_real_dias") - F.col("prazo_estimado_dias"))) > 1),
            F.lit(True)
        ).otherwise(F.lit(False))
    )

    # --- atraso_dias NULL para cancelados/devolvidos sem prazo_real ---
    .withColumn(
        "atraso_dias",
        F.when(
            F.col("status_pedido").isin("cancelado", "devolvido") &
            F.col("prazo_real_dias").isNull(),
            F.lit(None).cast(IntegerType())
        ).otherwise(F.col("atraso_dias"))
    )
)

# ---------------------------------------------------------------------------
# 3b. Deduplicação
# ---------------------------------------------------------------------------
silver_df = silver_df.dropDuplicates(["pedido_id", "item_id"])

# ---------------------------------------------------------------------------
# 3c. Separar quarentena
# ---------------------------------------------------------------------------
# Colunas obrigatórias
OBRIGATORIAS = ["pedido_id", "item_id", "cliente_id", "data_pedido", "valor_total"]

cond_nulo = F.lit(False)
for col in OBRIGATORIAS:
    cond_nulo = cond_nulo | F.col(col).isNull()

cond_email_invalido = ~F.col("cliente_email").contains("@")
cond_uf_invalida    = ~F.col("estado").isin(VALID_UFS)
cond_status_inv     = F.col("status_pedido").isNull()
cond_valor_inv      = F.col("valor_total").isNull() | (F.col("valor_total") <= 0)
cond_desconto_inv   = F.col("desconto_pct") > 100

quarentena_cond = (
    cond_nulo |
    cond_email_invalido |
    cond_uf_invalida |
    cond_status_inv |
    cond_valor_inv |
    cond_desconto_inv
)

# Motivo da quarentena (primeiro que disparar)
motivo = (
    F.when(cond_nulo,         "campo_obrigatorio_nulo")
     .when(cond_email_invalido,"email_invalido")
     .when(cond_uf_invalida,  "uf_invalida")
     .when(cond_status_inv,   "status_desconhecido")
     .when(cond_valor_inv,    "valor_monetario_invalido")
     .when(cond_desconto_inv, "desconto_fora_de_range")
)

quarentena_df = silver_df.filter(quarentena_cond).withColumn("motivo_quarentena", motivo)
silver_clean  = silver_df.filter(~quarentena_cond)

print(f"[SILVER] linhas aprovadas: {silver_clean.count()}")
print(f"[QUARENTENA] linhas rejeitadas: {quarentena_df.count()}")

# ---------------------------------------------------------------------------
# 3d. Gravar silver e quarentena
# ---------------------------------------------------------------------------
(
    silver_clean.write
    .mode("overwrite")
    .partitionBy("estado")
    .parquet(SILVER_PATH + "pedidos/")
)

(
    quarentena_df.write
    .mode("overwrite")
    .parquet(SILVER_PATH + "quarentena/")
)

print("[SILVER] gravado com sucesso.")

# ---------------------------------------------------------------------------
# 4. GOLD — tabelas de negócio
# ---------------------------------------------------------------------------

# ---- Gold 1: Resumo de atrasos por transportadora e estado ----------------
# Pergunta: quais transportadoras e estados concentram mais atrasos?
gold_atrasos = (
    silver_clean
    .filter(F.col("status_pedido") == "entregue")
    .groupBy("transportadora", "estado")
    .agg(
        F.count("*").alias("total_entregas"),
        F.sum(F.when(F.col("atraso_dias") > 0, 1).otherwise(0)).alias("total_atrasadas"),
        F.round(F.avg("atraso_dias"), 2).alias("media_atraso_dias"),
        F.round(F.avg("nota_avaliacao"), 2).alias("media_nota"),
    )
    .withColumn(
        "pct_atrasadas",
        F.round(F.col("total_atrasadas") / F.col("total_entregas") * 100, 1)
    )
    .orderBy(F.col("pct_atrasadas").desc())
)

(
    gold_atrasos.write
    .mode("overwrite")
    .parquet(GOLD_PATH + "atrasos_por_transportadora_estado/")
)

print("[GOLD] tabela atrasos_por_transportadora_estado gravada.")

# ---- Gold 2: Cancelamentos e devoluções por categoria e canal -------------
# Pergunta: quais categorias e canais têm mais cancelamento/devolução?
gold_cancel = (
    silver_clean
    .groupBy("categoria", "canal")
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum(F.when(F.col("status_pedido") == "cancelado", 1).otherwise(0)).alias("cancelados"),
        F.sum(F.when(F.col("status_pedido") == "devolvido", 1).otherwise(0)).alias("devolvidos"),
        F.round(F.avg("nota_avaliacao"), 2).alias("media_nota"),
        F.round(F.sum("valor_total"), 2).alias("valor_total_perdido"),
    )
    .withColumn(
        "pct_cancelamento_devolucao",
        F.round(
            (F.col("cancelados") + F.col("devolvidos")) / F.col("total_pedidos") * 100, 1
        )
    )
    .orderBy(F.col("pct_cancelamento_devolucao").desc())
)

(
    gold_cancel.write
    .mode("overwrite")
    .parquet(GOLD_PATH + "cancelamentos_devolucoes_por_categoria_canal/")
)

print("[GOLD] tabela cancelamentos_devolucoes_por_categoria_canal gravada.")

# ---- Gold 3: Sazonalidade — vendas e atrasos por mês ----------------------
# Pergunta: como Black Friday (nov) e Natal (dez) afetam vendas e logística?
gold_sazonal = (
    silver_clean
    .withColumn("ano_mes", F.date_format("data_pedido", "yyyy-MM"))
    .withColumn("mes",     F.month("data_pedido"))
    .groupBy("ano_mes", "mes")
    .agg(
        F.countDistinct("pedido_id").alias("total_pedidos"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("atraso_dias"), 2).alias("media_atraso_dias"),
        F.sum(F.when(F.col("atraso_dias") > 0, 1).otherwise(0)).alias("entregas_atrasadas"),
        F.round(F.avg("nota_avaliacao"), 2).alias("media_nota"),
    )
    .orderBy("ano_mes")
)

(
    gold_sazonal.write
    .mode("overwrite")
    .parquet(GOLD_PATH + "sazonalidade_mensal/")
)

print("[GOLD] tabela sazonalidade_mensal gravada.")

# ---------------------------------------------------------------------------
# 5. Finalizar job
# ---------------------------------------------------------------------------
job.commit()
print("[ETL] Job concluído com sucesso.")
