"""
ETL Pipeline - MercadoFácil E-commerce
Arquitetura Medalhão: RAW → SILVER → GOLD

Camadas:
- RAW (bronze): CSV original sem modificações
- SILVER: Dados limpos, tipados, deduplicados e anonimizados (LGPD)
- GOLD: Tabelas analíticas agregadas para responder perguntas de negócio
- QUARANTINE: Registros com problemas críticos de qualidade
"""

import sys
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window

# ===========================================================================
# INICIALIZAÇÃO
# ===========================================================================

args = getResolvedOptions(
    sys.argv,
    ['JOB_NAME', 'INPUT_PATH', 'SILVER_PATH', 'GOLD_PATH', 'QUARANTINE_PATH']
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print(f"[INFO] Job iniciado: {args['JOB_NAME']}")
print(f"[INFO] Input: {args['INPUT_PATH']}")
print(f"[INFO] Silver: {args['SILVER_PATH']}")
print(f"[INFO] Gold: {args['GOLD_PATH']}")
print(f"[INFO] Quarantine: {args['QUARANTINE_PATH']}")

# ===========================================================================
# FUNÇÕES AUXILIARES
# ===========================================================================

def parse_date(col_name):
    """
    Tenta converter uma coluna de data em múltiplos formatos.
    Retorna null se nenhum formato funcionar.
    """
    return F.coalesce(
        F.to_date(F.col(col_name), "yyyy-MM-dd"),
        F.to_date(F.col(col_name), "dd/MM/yyyy"),
        F.to_date(F.col(col_name), "yyyy-MM-dd HH:mm:ss")
    )

def clean_money(col_name):
    """
    Remove o prefixo "R$" e converte vírgula para ponto.
    Retorna DecimalType(10,2).
    """
    return F.regexp_replace(
        F.regexp_replace(F.col(col_name), r"R\$\s*", ""),
        ",", "."
    ).cast(DecimalType(10, 2))

def clean_percentage(col_name):
    """Remove o símbolo % e converte para decimal."""
    return F.regexp_replace(F.col(col_name), "%", "").cast(DecimalType(5, 2))

def normalize_estado(col_name):
    """Normaliza estado para siglas uppercase."""
    return F.when(F.upper(F.trim(F.col(col_name))) == "SÃO PAULO", "SP") \
        .when(F.upper(F.trim(F.col(col_name))) == "DISTRITO FEDERAL", "DF") \
        .otherwise(F.upper(F.trim(F.col(col_name))))

def normalize_status(col_name):
    """Normaliza status_pedido para valores padrão em português."""
    return F.when(F.lower(F.trim(F.col(col_name))) == "delivered", "entregue") \
        .when(F.lower(F.trim(F.col(col_name))) == "cancelled", "cancelado") \
        .when(F.lower(F.trim(F.col(col_name))) == "canceled", "cancelado") \
        .otherwise(F.lower(F.trim(F.col(col_name))))

# ===========================================================================
# ETAPA 1: RAW → SILVER (Limpeza e Padronização)
# ===========================================================================

print("\n[ETAPA 1] Carregando dados RAW...")
df_raw = spark.read.csv(
    args['INPUT_PATH'] + "pedidos_mercadofacil.csv",
    header=True,
    inferSchema=False  # Todas as colunas como string por enquanto
)

total_raw = df_raw.count()
print(f"[INFO] Total de registros lidos do RAW: {total_raw}")

# ---------------------------------------------------------------------------
# Limpeza de texto e padronização de case
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.1] Limpando e padronizando campos de texto...")
df_cleaned = df_raw \
    .withColumn("pedido_id", F.trim(F.col("pedido_id"))) \
    .withColumn("item_id", F.trim(F.col("item_id"))) \
    .withColumn("cliente_id", F.trim(F.col("cliente_id"))) \
    .withColumn("cliente_nome", F.trim(F.col("cliente_nome"))) \
    .withColumn("cliente_email", F.lower(F.trim(F.col("cliente_email")))) \
    .withColumn("cliente_cpf", F.regexp_replace(F.col("cliente_cpf"), r"\D", "")) \
    .withColumn("cliente_segmento", F.lower(F.trim(F.col("cliente_segmento")))) \
    .withColumn("estado", normalize_estado("estado")) \
    .withColumn("cidade", F.initcap(F.trim(F.col("cidade")))) \
    .withColumn("canal", F.lower(F.trim(F.col("canal")))) \
    .withColumn("categoria", F.lower(F.trim(F.col("categoria")))) \
    .withColumn("sku", F.trim(F.col("sku"))) \
    .withColumn("produto", F.trim(F.col("produto"))) \
    .withColumn("marca", F.trim(F.col("marca"))) \
    .withColumn("fornecedor", F.trim(F.col("fornecedor"))) \
    .withColumn("forma_pagamento", F.upper(F.trim(F.col("forma_pagamento")))) \
    .withColumn("status_pedido", normalize_status("status_pedido")) \
    .withColumn("transportadora", F.initcap(F.trim(F.col("transportadora")))) \
    .withColumn("centro_distribuicao", F.upper(F.trim(F.col("centro_distribuicao")))) \
    .withColumn("comentario", F.trim(F.col("comentario")))

# ---------------------------------------------------------------------------
# Conversão de tipos (datas, valores monetários, numéricos)
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.2] Convertendo tipos de dados...")
df_typed = df_cleaned \
    .withColumn("data_pedido", parse_date("data_pedido")) \
    .withColumn("data_entrega", parse_date("data_entrega")) \
    .withColumn("cliente_data_cadastro", parse_date("cliente_data_cadastro")) \
    .withColumn("custo_unitario", clean_money("custo_unitario")) \
    .withColumn("preco_unitario", clean_money("preco_unitario")) \
    .withColumn("valor_total", clean_money("valor_total")) \
    .withColumn("desconto_pct", clean_percentage("desconto_pct")) \
    .withColumn("quantidade", F.col("quantidade").cast(IntegerType())) \
    .withColumn("parcelas", F.col("parcelas").cast(IntegerType())) \
    .withColumn("prazo_estimado_dias", F.col("prazo_estimado_dias").cast(IntegerType())) \
    .withColumn("prazo_real_dias", F.col("prazo_real_dias").cast(IntegerType())) \
    .withColumn("atraso_dias", F.col("atraso_dias").cast(IntegerType())) \
    .withColumn("nota_avaliacao", F.col("nota_avaliacao").cast(IntegerType()))

# ---------------------------------------------------------------------------
# Validação de CPF e Email
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.3] Validando CPF e Email...")
df_validated = df_typed \
    .withColumn("cpf_valido", 
        F.when(F.col("cliente_cpf").isNotNull(), F.length(F.col("cliente_cpf")) == 11).otherwise(True)
    ) \
    .withColumn("email_valido",
        F.when(F.col("cliente_email").isNotNull(), F.col("cliente_email").contains("@")).otherwise(True)
    ) \
    .withColumn("data_pedido_valida",
        F.col("data_pedido").isNotNull()
    )

# ---------------------------------------------------------------------------
# Identificar registros para quarentena
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.4] Identificando registros para quarentena...")
df_with_motivo = df_validated.withColumn(
    "motivo_quarentena",
    F.when(F.col("pedido_id").isNull(), "pedido_id nulo")
    .when(~F.col("data_pedido_valida"), "data_pedido inválida")
    .when(F.col("cliente_id").isNull(), "cliente_id nulo")
    .when(~F.col("cpf_valido"), "cpf inválido")
    .when(~F.col("email_valido"), "email inválido")
    .otherwise(None)
)

# Separar registros válidos e inválidos
df_quarantine = df_with_motivo.filter(F.col("motivo_quarentena").isNotNull())
df_valid = df_with_motivo.filter(F.col("motivo_quarentena").isNull())

total_quarantine = df_quarantine.count()
total_valid = df_valid.count()
print(f"[INFO] Registros válidos: {total_valid}")
print(f"[INFO] Registros em quarentena: {total_quarantine}")

# Salvar quarentena
if total_quarantine > 0:
    print("\n[ETAPA 1.5] Salvando registros em quarentena...")
    df_quarantine.write.mode("overwrite").parquet(
        args['QUARANTINE_PATH'] + "pedidos_invalidos/"
    )
    print(f"[INFO] Quarentena salva em: {args['QUARANTINE_PATH']}pedidos_invalidos/")

# ---------------------------------------------------------------------------
# Deduplicação
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.6] Removendo duplicatas...")
window_dedup = Window.partitionBy("item_id").orderBy(F.col("data_pedido").asc())
df_deduped = df_valid \
    .withColumn("row_num", F.row_number().over(window_dedup)) \
    .filter(F.col("row_num") == 1) \
    .drop("row_num")

total_deduped = df_deduped.count()
duplicates_removed = total_valid - total_deduped
print(f"[INFO] Duplicatas removidas: {duplicates_removed}")
print(f"[INFO] Registros após deduplicação: {total_deduped}")

# ---------------------------------------------------------------------------
# Anonimização LGPD (hash SHA-256 dos dados pessoais)
# ---------------------------------------------------------------------------
print("\n[ETAPA 1.7] Anonimizando dados pessoais (LGPD)...")
df_silver = df_deduped \
    .withColumn("cliente_nome_hash", F.sha2(F.col("cliente_nome"), 256)) \
    .withColumn("cliente_email_hash", F.sha2(F.col("cliente_email"), 256)) \
    .withColumn("cliente_cpf_hash", F.sha2(F.col("cliente_cpf"), 256)) \
    .withColumn("data_processamento", F.lit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))) \
    .drop("cliente_nome", "cliente_email", "cliente_cpf", "comentario") \
    .drop("cpf_valido", "email_valido", "data_pedido_valida", "motivo_quarentena")

# Salvar SILVER
print("\n[ETAPA 1.8] Salvando camada SILVER...")
df_silver.write.mode("overwrite").parquet(args['SILVER_PATH'] + "pedidos/")
print(f"[INFO] SILVER salva com {df_silver.count()} registros em: {args['SILVER_PATH']}pedidos/")

# ===========================================================================
# ETAPA 2: SILVER → GOLD (Tabelas Analíticas)
# ===========================================================================

print("\n[ETAPA 2] Criando tabelas GOLD...")

# ---------------------------------------------------------------------------
# GOLD 1: Análise de Atrasos e Avaliações
# ---------------------------------------------------------------------------
print("\n[GOLD 1] Criando tabela analise_atrasos_avaliacoes...")
df_atrasos = df_silver \
    .filter(F.col("status_pedido") == "entregue") \
    .groupBy("estado", "categoria", "transportadora", "centro_distribuicao") \
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum(F.when(F.col("atraso_dias") > 0, 1).otherwise(0)).alias("pedidos_atrasados"),
        F.avg("atraso_dias").alias("atraso_medio_dias"),
        F.max("atraso_dias").alias("atraso_maximo_dias"),
        F.avg("nota_avaliacao").alias("nota_media"),
        F.sum(F.when(F.col("nota_avaliacao") <= 2, 1).otherwise(0)).alias("avaliacoes_baixas"),
        F.avg("prazo_estimado_dias").alias("prazo_estimado_medio"),
        F.avg("prazo_real_dias").alias("prazo_real_medio")
    ) \
    .withColumn("taxa_atraso_pct", 
        (F.col("pedidos_atrasados") / F.col("total_pedidos") * 100).cast(DecimalType(5, 2))
    ) \
    .withColumn("taxa_avaliacao_baixa_pct",
        (F.col("avaliacoes_baixas") / F.col("total_pedidos") * 100).cast(DecimalType(5, 2))
    )

df_atrasos.write.mode("overwrite").parquet(args['GOLD_PATH'] + "analise_atrasos_avaliacoes/")
print(f"[INFO] GOLD 1 salva com {df_atrasos.count()} registros")

# ---------------------------------------------------------------------------
# GOLD 2: Análise de Cancelamentos e Devoluções
# ---------------------------------------------------------------------------
print("\n[GOLD 2] Criando tabela analise_cancelamentos_devolucoes...")
df_cancelamentos = df_silver \
    .groupBy("estado", "categoria", "canal", "forma_pagamento") \
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum(F.when(F.col("status_pedido") == "cancelado", 1).otherwise(0)).alias("total_cancelados"),
        F.sum(F.when(F.col("status_pedido") == "devolvido", 1).otherwise(0)).alias("total_devolvidos"),
        F.sum("valor_total").alias("valor_total_vendas"),
        F.avg("valor_total").alias("ticket_medio"),
        F.countDistinct("cliente_id").alias("clientes_unicos")
    ) \
    .withColumn("taxa_cancelamento_pct",
        (F.col("total_cancelados") / F.col("total_pedidos") * 100).cast(DecimalType(5, 2))
    ) \
    .withColumn("taxa_devolucao_pct",
        (F.col("total_devolvidos") / F.col("total_pedidos") * 100).cast(DecimalType(5, 2))
    ) \
    .withColumn("taxa_perda_pct",
        ((F.col("total_cancelados") + F.col("total_devolvidos")) / F.col("total_pedidos") * 100).cast(DecimalType(5, 2))
    )

df_cancelamentos.write.mode("overwrite").parquet(args['GOLD_PATH'] + "analise_cancelamentos_devolucoes/")
print(f"[INFO] GOLD 2 salva com {df_cancelamentos.count()} registros")

# ---------------------------------------------------------------------------
# GOLD 3: Análise de Sazonalidade
# ---------------------------------------------------------------------------
print("\n[GOLD 3] Criando tabela analise_sazonalidade...")
df_sazonalidade = df_silver \
    .withColumn("ano", F.year("data_pedido")) \
    .withColumn("mes", F.month("data_pedido")) \
    .withColumn("mes_nome", 
        F.when(F.col("mes") == 1, "Janeiro")
        .when(F.col("mes") == 2, "Fevereiro")
        .when(F.col("mes") == 3, "Março")
        .when(F.col("mes") == 4, "Abril")
        .when(F.col("mes") == 5, "Maio")
        .when(F.col("mes") == 6, "Junho")
        .when(F.col("mes") == 7, "Julho")
        .when(F.col("mes") == 8, "Agosto")
        .when(F.col("mes") == 9, "Setembro")
        .when(F.col("mes") == 10, "Outubro")
        .when(F.col("mes") == 11, "Novembro")
        .when(F.col("mes") == 12, "Dezembro")
    ) \
    .groupBy("ano", "mes", "mes_nome", "categoria") \
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum("valor_total").alias("receita_total"),
        F.avg("atraso_dias").alias("atraso_medio_dias"),
        F.sum(F.when(F.col("status_pedido") == "cancelado", 1).otherwise(0)).alias("cancelamentos"),
        F.sum(F.when(F.col("status_pedido") == "devolvido", 1).otherwise(0)).alias("devolucoes"),
        F.avg("nota_avaliacao").alias("nota_media")
    ) \
    .orderBy("ano", "mes", "categoria")

df_sazonalidade.write.mode("overwrite").parquet(args['GOLD_PATH'] + "analise_sazonalidade/")
print(f"[INFO] GOLD 3 salva com {df_sazonalidade.count()} registros")

# ---------------------------------------------------------------------------
# GOLD 4: Fato Pedidos (tabela granular)
# ---------------------------------------------------------------------------
print("\n[GOLD 4] Criando tabela fato_pedidos...")
df_fato = df_silver.select(
    "pedido_id", "item_id", "data_pedido",
    "cliente_id", "cliente_segmento", "cliente_data_cadastro",
    "estado", "cidade", "canal",
    "categoria", "sku", "produto", "marca", "fornecedor",
    "custo_unitario", "preco_unitario", "quantidade", "desconto_pct", "valor_total",
    "forma_pagamento", "parcelas",
    "status_pedido", "transportadora", "centro_distribuicao",
    "prazo_estimado_dias", "prazo_real_dias", "data_entrega", "atraso_dias",
    "nota_avaliacao",
    "cliente_nome_hash", "cliente_email_hash", "cliente_cpf_hash"
)

df_fato.write.mode("overwrite").parquet(args['GOLD_PATH'] + "fato_pedidos/")
print(f"[INFO] GOLD 4 salva com {df_fato.count()} registros")

# ===========================================================================
# FINALIZAÇÃO
# ===========================================================================

print("\n" + "="*80)
print("PIPELINE CONCLUÍDO COM SUCESSO!")
print("="*80)
print(f"Total RAW:          {total_raw}")
print(f"Total Quarentena:   {total_quarantine}")
print(f"Total Válidos:      {total_valid}")
print(f"Duplicatas:         {duplicates_removed}")
print(f"Total SILVER:       {total_deduped}")
print(f"GOLD Tabelas:       4 (atrasos, cancelamentos, sazonalidade, fato_pedidos)")
print("="*80)

job.commit()
