"""
ETL MercadoFácil — Aula 12
Arquitetura medalhão: raw (CSV) → silver (Parquet limpo) → gold (tabelas de negócio)

Execução no AWS Glue 4.0 (PySpark 3.3).
Argumentos passados pelo Glue Job:
  --INPUT_PATH   s3://<bucket>/raw/pedidos_mercadofacil.csv
  --SILVER_PATH  s3://<bucket>/silver/
  --GOLD_PATH    s3://<bucket>/gold/
"""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# ---------------------------------------------------------------------------
# Inicialização do contexto Glue / Spark
# ---------------------------------------------------------------------------
args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "INPUT_PATH", "SILVER_PATH", "GOLD_PATH"]
)

sc = SparkContext()
glue_context = GlueContext(sc)
spark: SparkSession = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

INPUT_PATH = args["INPUT_PATH"]
SILVER_PATH = args["SILVER_PATH"]
GOLD_PATH = args["GOLD_PATH"]

# ---------------------------------------------------------------------------
# Helpers de limpeza
# ---------------------------------------------------------------------------

def clean_money(col_name: str) -> F.Column:
    """
    Remove prefixo 'R$ ', troca vírgula decimal por ponto e converte para
    DoubleType.  Exemplos que trata: 'R$ 49,24', '"91,67"', '44.32'.
    """
    return (
        F.regexp_replace(F.regexp_replace(F.col(col_name), r"R\$\s*", ""), r",", ".")
        .cast(T.DoubleType())
    )


def clean_pct(col_name: str) -> F.Column:
    """
    Remove o símbolo '%' e converte para DoubleType.
    Trata também 'N/A' e '-' como nulo.
    """
    cleaned = F.regexp_replace(F.col(col_name), r"%", "")
    return F.when(cleaned.isin("N/A", "-", "null", "NULL", ""), None).otherwise(
        cleaned.cast(T.DoubleType())
    )


def normalize_null(col_name: str) -> F.Column:
    """Padroniza as várias representações de nulo para null real."""
    return F.when(
        F.upper(F.trim(F.col(col_name))).isin("N/A", "NULL", "NA", "-", ""),
        None,
    ).otherwise(F.trim(F.col(col_name)))


def parse_date(col_name: str) -> F.Column:
    """
    Tenta converter datas nos formatos encontrados no CSV:
      - dd/MM/yyyy
      - yyyy-MM-dd
      - yyyy-MM-dd HH:mm:ss
    Retorna DateType (sem hora).
    """
    c = F.trim(F.col(col_name))
    return F.coalesce(
        F.to_date(c, "dd/MM/yyyy"),
        F.to_date(c, "yyyy-MM-dd"),
        F.to_date(c, "yyyy-MM-dd HH:mm:ss"),
    )


def normalize_status(col_name: str) -> F.Column:
    """
    Padroniza status_pedido para valores canônicos em português.
    Mapeamento: variações de ENTREGUE, CANCELLED, RETURNED, etc.
    """
    upper = F.upper(F.trim(F.col(col_name)))
    return (
        F.when(upper.isin("ENTREGUE", "DELIVERED"), "entregue")
        .when(upper.isin("CANCELADO", "CANCELLED", "CANCELED"), "cancelado")
        .when(upper.isin("DEVOLVIDO", "RETURNED"), "devolvido")
        .when(upper.isin("EM TRANSITO", "IN_TRANSIT", "EM TRÂNSITO"), "em_transito")
        .when(upper.isin("PENDENTE", "PENDING"), "pendente")
        .otherwise(F.lower(F.trim(F.col(col_name))))
    )


def normalize_uf(col_name: str) -> F.Column:
    """Converte sigla de estado para maiúsculas e remove espaços."""
    return F.upper(F.trim(F.col(col_name)))


def normalize_categoria(col_name: str) -> F.Column:
    """Título-case e trim para padronizar categorias."""
    return F.initcap(F.trim(F.col(col_name)))


def mask_cpf(col_name: str) -> F.Column:
    """
    LGPD: mascara o CPF mantendo apenas os 3 últimos dígitos.
    Remove qualquer formatação antes de mascarar.
    Exemplo: '737.295.450-38' → '***.***.***-38'
    """
    digits_only = F.regexp_replace(F.col(col_name), r"[.\-\s]", "")
    last3 = F.substring(digits_only, -3, 3)
    return F.when(
        F.col(col_name).isNull()
        | F.upper(F.trim(F.col(col_name))).isin("N/A", "NULL", "-", ""),
        None,
    ).otherwise(F.concat(F.lit("***.***.***-"), last3))


def mask_email(col_name: str) -> F.Column:
    """
    LGPD: mantém apenas o domínio do e-mail (remove a parte local).
    Exemplo: 'vitor@exemplo.com' → '***@exemplo.com'
    Se não contiver '@', marca como inválido.
    """
    return F.when(
        F.col(col_name).contains("@"),
        F.concat(F.lit("***@"), F.element_at(F.split(F.col(col_name), "@"), 2)),
    ).otherwise(F.lit("email_invalido"))


def is_valid_email(col_name: str) -> F.Column:
    """Retorna True se o e-mail contém '@' (validação mínima)."""
    return F.col(col_name).contains("@")


# ---------------------------------------------------------------------------
# CAMADA RAW — leitura do CSV exatamente como chega
# ---------------------------------------------------------------------------
print(f"[ETL] Lendo raw CSV de: {INPUT_PATH}")

raw_df: DataFrame = (
    spark.read.option("header", "true")
    .option("inferSchema", "false")
    .option("quote", '"')
    .option("escape", '"')
    .option("multiLine", "true")
    .csv(INPUT_PATH)
)

print(f"[ETL] Raw: {raw_df.count()} linhas, {len(raw_df.columns)} colunas")

# ---------------------------------------------------------------------------
# SILVER — limpeza, padronização, tipagem e quarentena
# ---------------------------------------------------------------------------

# 1. Deduplicação: mantém a primeira ocorrência de cada (pedido_id, item_id)
window_dedup = Window.partitionBy("pedido_id", "item_id").orderBy(F.monotonically_increasing_id())
dedup_df = (
    raw_df
    .withColumn("_rn", F.row_number().over(window_dedup))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

# 2. Aplica limpezas coluna a coluna
cleaned_df = (
    dedup_df
    # --- Identificadores ---
    .withColumn("pedido_id",   F.trim(F.col("pedido_id")))
    .withColumn("item_id",     F.trim(F.col("item_id")))
    .withColumn("cliente_id",  F.trim(F.col("cliente_id")))
    .withColumn("sku",         F.trim(F.col("sku")))

    # --- Datas (formatos mistos) ---
    .withColumn("data_pedido",          parse_date("data_pedido"))
    .withColumn("cliente_data_cadastro", parse_date("cliente_data_cadastro"))
    .withColumn("data_entrega",          parse_date("data_entrega"))

    # --- Dados pessoais: LGPD ---
    .withColumn("cliente_nome",  F.initcap(F.trim(F.col("cliente_nome"))))
    .withColumn("cliente_cpf",   mask_cpf("cliente_cpf"))
    .withColumn("cliente_email", mask_email(F.lower(F.trim(F.col("cliente_email").cast("string"))).alias("_e")))

    # --- Texto / categorias ---
    .withColumn("estado",           normalize_uf("estado"))
    .withColumn("cidade",           F.initcap(F.trim(F.col("cidade"))))
    .withColumn("canal",            F.lower(F.trim(F.col("canal"))))
    .withColumn("categoria",        normalize_categoria("categoria"))
    .withColumn("produto",          F.trim(F.col("produto")))
    .withColumn("marca",            F.trim(F.col("marca")))
    .withColumn("fornecedor",       F.trim(F.col("fornecedor")))
    .withColumn("transportadora",   F.upper(F.trim(F.col("transportadora"))))
    .withColumn("centro_distribuicao", F.upper(F.trim(F.col("centro_distribuicao"))))
    .withColumn("cliente_segmento", F.lower(F.trim(F.col("cliente_segmento"))))

    # --- Status ---
    .withColumn("status_pedido",    normalize_status("status_pedido"))

    # --- Pagamento ---
    .withColumn("forma_pagamento",
        F.when(F.lower(F.trim(F.col("forma_pagamento"))).isin(
            "cartao credito", "cartão de crédito", "credito", "cartao_credito", "credito"
        ), "cartao_credito")
        .when(F.lower(F.trim(F.col("forma_pagamento"))).isin(
            "cartao debito", "cartão de débito", "debito", "cartao_debito", "cartao débito"
        ), "cartao_debito")
        .when(F.lower(F.trim(F.col("forma_pagamento"))).isin("pix"), "pix")
        .when(F.lower(F.trim(F.col("forma_pagamento"))).isin(
            "boleto", "boleto bancario", "boleto bancário"
        ), "boleto")
        .otherwise(F.lower(F.trim(F.col("forma_pagamento"))))
    )
    .withColumn("parcelas",
        F.when(normalize_null("parcelas").isNull(), None)
        .otherwise(F.trim(F.col("parcelas")).cast(T.IntegerType()))
    )

    # --- Valores monetários (R$ + vírgula decimal) ---
    .withColumn("custo_unitario",  clean_money("custo_unitario"))
    .withColumn("preco_unitario",  clean_money("preco_unitario"))
    .withColumn("valor_total",     clean_money("valor_total"))

    # --- Percentual de desconto (pode ter % ou ser N/A) ---
    .withColumn("desconto_pct", clean_pct("desconto_pct"))

    # --- Numéricos simples ---
    .withColumn("quantidade",          F.trim(F.col("quantidade")).cast(T.IntegerType()))
    .withColumn("prazo_estimado_dias", F.trim(F.col("prazo_estimado_dias")).cast(T.IntegerType()))
    .withColumn("prazo_real_dias",
        F.when(normalize_null("prazo_real_dias").isNull(), None)
        .otherwise(F.trim(F.col("prazo_real_dias")).cast(T.IntegerType()))
    )
    .withColumn("atraso_dias",
        F.when(normalize_null("atraso_dias").isNull(), F.lit(0).cast(T.IntegerType()))
        .otherwise(F.trim(F.col("atraso_dias")).cast(T.IntegerType()))
    )
    .withColumn("nota_avaliacao",
        F.when(normalize_null("nota_avaliacao").isNull(), None)
        .otherwise(F.trim(F.col("nota_avaliacao")).cast(T.IntegerType()))
    )

    # --- Comentário: trim e nulos ---
    .withColumn("comentario",
        F.when(normalize_null("comentario").isNull(), None)
        .otherwise(F.trim(F.col("comentario")))
    )
)

# 3. Separa linhas inválidas (quarentena) das linhas aproveitáveis (silver)
#    Regras de quarentena: pedido_id nulo, data_pedido não parseável,
#    preco_unitario nulo/zero, quantidade nula/zero, e-mail inválido.
quarentena_df = cleaned_df.filter(
    F.col("pedido_id").isNull()
    | F.col("data_pedido").isNull()
    | F.col("preco_unitario").isNull()
    | (F.col("preco_unitario") <= 0)
    | F.col("quantidade").isNull()
    | (F.col("quantidade") <= 0)
    | F.col("cliente_email").eqNullSafe("email_invalido")
).withColumn("motivo_quarentena",
    F.concat_ws("; ",
        F.when(F.col("pedido_id").isNull(),         F.lit("pedido_id nulo")),
        F.when(F.col("data_pedido").isNull(),        F.lit("data_pedido invalida")),
        F.when(F.col("preco_unitario").isNull()
               | (F.col("preco_unitario") <= 0),     F.lit("preco_unitario invalido")),
        F.when(F.col("quantidade").isNull()
               | (F.col("quantidade") <= 0),         F.lit("quantidade invalida")),
        F.when(F.col("cliente_email").eqNullSafe("email_invalido"),
                                                     F.lit("email sem @")),
    )
)

silver_df = cleaned_df.filter(
    F.col("pedido_id").isNotNull()
    & F.col("data_pedido").isNotNull()
    & F.col("preco_unitario").isNotNull()
    & (F.col("preco_unitario") > 0)
    & F.col("quantidade").isNotNull()
    & (F.col("quantidade") > 0)
    & ~F.col("cliente_email").eqNullSafe("email_invalido")
)

# Adiciona coluna de partição por ano/mês para leitura eficiente
silver_df = silver_df.withColumn("ano_pedido", F.year("data_pedido"))

silver_count = silver_df.count()
quarentena_count = quarentena_df.count()
print(f"[ETL] Silver: {silver_count} linhas válidas")
print(f"[ETL] Quarentena: {quarentena_count} linhas rejeitadas")

# Grava silver (Parquet, particionado por ano)
silver_df.write.mode("overwrite").partitionBy("ano_pedido").parquet(SILVER_PATH)
print(f"[ETL] Silver gravado em: {SILVER_PATH}")

# Grava quarentena
if quarentena_count > 0:
    quarentena_df.write.mode("overwrite").parquet(SILVER_PATH + "quarentena/")
    print(f"[ETL] Quarentena gravada em: {SILVER_PATH}quarentena/")

# ---------------------------------------------------------------------------
# GOLD — tabelas de negócio prontas para o Athena
# ---------------------------------------------------------------------------
# Reutiliza o silver já limpo (releitura do parquet para consistência)
silver = spark.read.parquet(SILVER_PATH).filter(
    ~F.col("ano_pedido").isNull()
    & (F.col("status_pedido") != "quarentena")
).drop("ano_pedido")

# ---------------------------------------------------------------------------
# Gold 1: fact_pedidos
# Nível: 1 linha por item de pedido (granularidade original).
# Contém todos os campos de negócio sem dados pessoais.
# Responde: volume de vendas, ticket médio, atrasos, avaliações.
# ---------------------------------------------------------------------------
fact_pedidos = silver.select(
    "pedido_id",
    "item_id",
    "data_pedido",
    "status_pedido",
    "canal",
    "estado",
    "cidade",
    "categoria",
    "sku",
    "produto",
    "marca",
    "fornecedor",
    "custo_unitario",
    "preco_unitario",
    "quantidade",
    "desconto_pct",
    "valor_total",
    "forma_pagamento",
    "parcelas",
    "transportadora",
    "centro_distribuicao",
    "prazo_estimado_dias",
    "prazo_real_dias",
    "data_entrega",
    "atraso_dias",
    "nota_avaliacao",
    F.year("data_pedido").alias("ano"),
    F.month("data_pedido").alias("mes"),
)

fact_pedidos.write.mode("overwrite").parquet(GOLD_PATH + "fact_pedidos/")
print(f"[ETL] gold/fact_pedidos gravado: {fact_pedidos.count()} linhas")

# ---------------------------------------------------------------------------
# Gold 2: agg_atraso_por_estado_categoria
# Responde: quais estados e categorias concentram mais atrasos?
# Ferramenta principal para análise de logística.
# ---------------------------------------------------------------------------
agg_atraso = (
    silver
    .filter(F.col("status_pedido").isin("entregue", "devolvido"))
    .groupBy("estado", "categoria", "transportadora")
    .agg(
        F.count("pedido_id").alias("total_pedidos"),
        F.sum(F.when(F.col("atraso_dias") > 0, 1).otherwise(0)).alias("pedidos_atrasados"),
        F.round(F.avg("atraso_dias"), 2).alias("media_atraso_dias"),
        F.round(F.avg("nota_avaliacao"), 2).alias("media_nota"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
    )
    .withColumn(
        "pct_atrasados",
        F.round(F.col("pedidos_atrasados") / F.col("total_pedidos") * 100, 1),
    )
    .orderBy(F.col("pedidos_atrasados").desc())
)

agg_atraso.write.mode("overwrite").parquet(GOLD_PATH + "agg_atraso_por_estado_categoria/")
print(f"[ETL] gold/agg_atraso_por_estado_categoria gravado: {agg_atraso.count()} linhas")

# ---------------------------------------------------------------------------
# Gold 3: agg_cancelamento_devolucao
# Responde: quais categorias, canais e estados têm mais cancelamento/devolução?
# ---------------------------------------------------------------------------
agg_cancel = (
    silver
    .groupBy("estado", "categoria", "canal", "status_pedido")
    .agg(
        F.count("pedido_id").alias("total_pedidos"),
        F.round(F.sum("valor_total"), 2).alias("valor_total"),
    )
    .filter(F.col("status_pedido").isin("cancelado", "devolvido"))
    .orderBy(F.col("total_pedidos").desc())
)

agg_cancel.write.mode("overwrite").parquet(GOLD_PATH + "agg_cancelamento_devolucao/")
print(f"[ETL] gold/agg_cancelamento_devolucao gravado: {agg_cancel.count()} linhas")

# ---------------------------------------------------------------------------
# Gold 4: agg_sazonalidade_mensal
# Responde: como Black Friday (nov) e Natal (dez) afetam vendas e logística?
# ---------------------------------------------------------------------------
agg_sazonal = (
    silver
    .withColumn("ano_mes", F.date_format("data_pedido", "yyyy-MM"))
    .groupBy("ano_mes", F.year("data_pedido").alias("ano"), F.month("data_pedido").alias("mes"))
    .agg(
        F.count("pedido_id").alias("total_pedidos"),
        F.round(F.sum("valor_total"), 2).alias("receita_total"),
        F.round(F.avg("atraso_dias"), 2).alias("media_atraso_dias"),
        F.sum(F.when(F.col("atraso_dias") > 0, 1).otherwise(0)).alias("pedidos_atrasados"),
        F.round(F.avg("nota_avaliacao"), 2).alias("media_nota"),
    )
    .orderBy("ano_mes")
)

agg_sazonal.write.mode("overwrite").parquet(GOLD_PATH + "agg_sazonalidade_mensal/")
print(f"[ETL] gold/agg_sazonalidade_mensal gravado: {agg_sazonal.count()} linhas")

# ---------------------------------------------------------------------------
# Finalização
# ---------------------------------------------------------------------------
job.commit()
print("[ETL] Job concluído com sucesso.")
