"""
ETL Pipeline MercadoFácil - AWS Glue Job
Processa dados raw (CSV) -> silver (Parquet limpo) -> gold (tabelas analíticas)
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

# Argumentos do job
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'INPUT_PATH',
    'SILVER_PATH',
    'GOLD_PATH',
    'QUARANTINE_PATH'
])

# Inicialização do contexto Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print(f"[INFO] Iniciando ETL MercadoFácil")
print(f"[INFO] INPUT_PATH: {args['INPUT_PATH']}")
print(f"[INFO] SILVER_PATH: {args['SILVER_PATH']}")
print(f"[INFO] GOLD_PATH: {args['GOLD_PATH']}")

# ============================================================================
# CAMADA RAW -> SILVER
# ============================================================================

print("[INFO] Lendo dados da camada RAW (CSV)...")
# Lê CSV como texto (todas as colunas como string)
df_raw = spark.read.option("header", "true").option("inferSchema", "false").csv(args['INPUT_PATH'])

print(f"[INFO] Total de registros lidos: {df_raw.count()}")
df_raw.printSchema()

# Lista para armazenar registros com problemas (quarentena)
quarantine_records = []

# 1. Limpeza e padronização básica
print("[INFO] Aplicando limpeza e padronização...")

df_clean = df_raw \
    .withColumn("pedido_id", F.trim(F.col("pedido_id"))) \
    .withColumn("item_id", F.trim(F.col("item_id"))) \
    .withColumn("cliente_id", F.trim(F.col("cliente_id"))) \
    .withColumn("cliente_nome", F.trim(F.col("cliente_nome"))) \
    .withColumn("cliente_email", F.lower(F.trim(F.col("cliente_email")))) \
    .withColumn("cliente_cpf", F.regexp_replace(F.col("cliente_cpf"), "[^0-9]", "")) \
    .withColumn("cliente_segmento", F.lower(F.trim(F.col("cliente_segmento")))) \
    .withColumn("estado", F.upper(F.trim(F.col("estado")))) \
    .withColumn("cidade", F.initcap(F.trim(F.col("cidade")))) \
    .withColumn("canal", F.lower(F.trim(F.col("canal")))) \
    .withColumn("categoria", F.initcap(F.trim(F.col("categoria")))) \
    .withColumn("sku", F.trim(F.col("sku"))) \
    .withColumn("produto", F.trim(F.col("produto"))) \
    .withColumn("marca", F.trim(F.col("marca"))) \
    .withColumn("fornecedor", F.trim(F.col("fornecedor"))) \
    .withColumn("forma_pagamento", F.upper(F.trim(F.col("forma_pagamento")))) \
    .withColumn("status_pedido", F.lower(F.trim(F.col("status_pedido")))) \
    .withColumn("transportadora", F.initcap(F.trim(F.col("transportadora")))) \
    .withColumn("centro_distribuicao", F.upper(F.trim(F.col("centro_distribuicao"))))

# 2. Normalização de estados (alguns vêm por extenso)
estado_map = {
    "SÃO PAULO": "SP",
    "RIO DE JANEIRO": "RJ",
    "MINAS GERAIS": "MG",
    "DISTRITO FEDERAL": "DF",
    "PARA": "PA",
    "PARÁ": "PA"
}

for extenso, sigla in estado_map.items():
    df_clean = df_clean.withColumn("estado", 
        F.when(F.col("estado") == extenso, sigla).otherwise(F.col("estado")))

# 3. Normalização de status_pedido
status_map = {
    "entregue": "entregue",
    "entregue ": "entregue",
    "delivered": "entregue",
    "cancelado": "cancelado",
    "cancelled": "cancelado",
    "devolvido": "devolvido",
    "returned": "devolvido"
}

for original, padrao in status_map.items():
    df_clean = df_clean.withColumn("status_pedido",
        F.when(F.col("status_pedido") == original, padrao).otherwise(F.col("status_pedido")))

# 4. Limpeza de valores monetários e conversão
def clean_money(col_name):
    return F.regexp_replace(
        F.regexp_replace(F.col(col_name), "R\\$\\s*", ""),
        ",", "."
    )

df_clean = df_clean \
    .withColumn("custo_unitario_clean", clean_money("custo_unitario")) \
    .withColumn("preco_unitario_clean", clean_money("preco_unitario")) \
    .withColumn("valor_total_clean", clean_money("valor_total"))

# 5. Limpeza de percentuais
df_clean = df_clean.withColumn("desconto_pct_clean", 
    F.regexp_replace(F.col("desconto_pct"), "%", ""))

# 6. Padronização de datas
def parse_date(col_name):
    """Tenta múltiplos formatos de data"""
    return F.coalesce(
        F.to_date(F.col(col_name), "yyyy-MM-dd"),
        F.to_date(F.col(col_name), "dd/MM/yyyy"),
        F.to_date(F.col(col_name), "yyyy-MM-dd HH:mm:ss")
    )

df_clean = df_clean \
    .withColumn("data_pedido_parsed", parse_date("data_pedido")) \
    .withColumn("data_entrega_parsed", parse_date("data_entrega")) \
    .withColumn("cliente_data_cadastro_parsed", parse_date("cliente_data_cadastro"))

# 7. Conversão de tipos (tipagem forte)
print("[INFO] Convertendo tipos de dados...")

df_typed = df_clean \
    .withColumn("quantidade", F.col("quantidade").cast(IntegerType())) \
    .withColumn("custo_unitario", F.col("custo_unitario_clean").cast(DecimalType(10, 2))) \
    .withColumn("preco_unitario", F.col("preco_unitario_clean").cast(DecimalType(10, 2))) \
    .withColumn("valor_total", F.col("valor_total_clean").cast(DecimalType(10, 2))) \
    .withColumn("desconto_pct", F.col("desconto_pct_clean").cast(DecimalType(5, 2))) \
    .withColumn("parcelas", F.col("parcelas").cast(IntegerType())) \
    .withColumn("prazo_estimado_dias", F.col("prazo_estimado_dias").cast(IntegerType())) \
    .withColumn("prazo_real_dias", F.col("prazo_real_dias").cast(IntegerType())) \
    .withColumn("atraso_dias", F.col("atraso_dias").cast(IntegerType())) \
    .withColumn("nota_avaliacao", F.col("nota_avaliacao").cast(IntegerType())) \
    .withColumn("data_pedido", F.col("data_pedido_parsed")) \
    .withColumn("data_entrega", F.col("data_entrega_parsed")) \
    .withColumn("cliente_data_cadastro", F.col("cliente_data_cadastro_parsed"))

# 8. Validação de CPF (deve ter 11 dígitos)
df_typed = df_typed.withColumn("cpf_valido", 
    F.when(F.length(F.col("cliente_cpf")) == 11, True).otherwise(False))

# 9. Validação de email (deve conter @)
df_typed = df_typed.withColumn("email_valido",
    F.when(F.col("cliente_email").contains("@"), True).otherwise(False))

# 10. Identificar registros inválidos para quarentena
df_typed = df_typed.withColumn("motivo_quarentena",
    F.when(F.col("pedido_id").isNull(), "pedido_id nulo")
    .when(F.col("data_pedido").isNull(), "data_pedido inválida")
    .when(F.col("cliente_id").isNull(), "cliente_id nulo")
    .when(~F.col("cpf_valido") & F.col("cliente_cpf").isNotNull(), "cpf inválido")
    .when(~F.col("email_valido") & F.col("cliente_email").isNotNull(), "email inválido")
    .otherwise(None)
)

# Separar registros válidos e inválidos
df_quarantine = df_typed.filter(F.col("motivo_quarentena").isNotNull())
df_valid = df_typed.filter(F.col("motivo_quarentena").isNull())

print(f"[INFO] Registros válidos: {df_valid.count()}")
print(f"[INFO] Registros em quarentena: {df_quarantine.count()}")

# 11. Deduplicação - Remover duplicatas exatas por item_id (mantém a primeira)
print("[INFO] Removendo duplicatas...")
window_spec = Window.partitionBy("item_id").orderBy("data_pedido")
df_valid = df_valid.withColumn("row_num", F.row_number().over(window_spec))
df_deduplicated = df_valid.filter(F.col("row_num") == 1).drop("row_num")

print(f"[INFO] Registros após deduplicação: {df_deduplicated.count()}")

# 12. Anonimização de dados pessoais (LGPD)
# Mascarar nome, email e CPF
df_silver = df_deduplicated \
    .withColumn("cliente_nome_hash", F.sha2(F.col("cliente_nome"), 256)) \
    .withColumn("cliente_email_hash", F.sha2(F.col("cliente_email"), 256)) \
    .withColumn("cliente_cpf_hash", F.sha2(F.col("cliente_cpf"), 256)) \
    .drop("cliente_nome", "cliente_email", "cliente_cpf", "comentario") \
    .drop("custo_unitario_clean", "preco_unitario_clean", "valor_total_clean", 
          "desconto_pct_clean", "data_pedido_parsed", "data_entrega_parsed",
          "cliente_data_cadastro_parsed", "cpf_valido", "email_valido", "motivo_quarentena")

# 13. Adicionar metadados de processamento
df_silver = df_silver.withColumn("data_processamento", F.lit(datetime.now().isoformat()))

# Salvar camada SILVER
print(f"[INFO] Salvando camada SILVER em {args['SILVER_PATH']}...")
df_silver.write.mode("overwrite").parquet(args['SILVER_PATH'] + "pedidos/")

# Salvar quarentena
if df_quarantine.count() > 0:
    print(f"[INFO] Salvando registros em quarentena em {args['QUARANTINE_PATH']}...")
    df_quarantine.select(
        "pedido_id", "item_id", "cliente_id", "data_pedido", "motivo_quarentena"
    ).write.mode("overwrite").parquet(args['QUARANTINE_PATH'] + "pedidos_invalidos/")

# ============================================================================
# CAMADA SILVER -> GOLD
# ============================================================================

print("[INFO] Processando camada GOLD...")

# Recarregar silver para garantir consistência
df_silver = spark.read.parquet(args['SILVER_PATH'] + "pedidos/")

# ---- GOLD TABLE 1: Análise de Atrasos e Avaliações ----
print("[INFO] Criando tabela gold: analise_atrasos_avaliacoes")

df_atrasos = df_silver.filter(F.col("status_pedido") == "entregue") \
    .withColumn("teve_atraso", F.when(F.col("atraso_dias") > 0, 1).otherwise(0)) \
    .groupBy("estado", "categoria", "transportadora", "centro_distribuicao") \
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum("teve_atraso").alias("pedidos_atrasados"),
        F.avg("atraso_dias").alias("atraso_medio_dias"),
        F.max("atraso_dias").alias("atraso_maximo_dias"),
        F.avg("nota_avaliacao").alias("nota_media"),
        F.sum(F.when(F.col("nota_avaliacao") <= 2, 1).otherwise(0)).alias("avaliacoes_baixas"),
        F.avg("prazo_estimado_dias").alias("prazo_estimado_medio"),
        F.avg("prazo_real_dias").alias("prazo_real_medio")
    ) \
    .withColumn("taxa_atraso_pct", (F.col("pedidos_atrasados") / F.col("total_pedidos")) * 100) \
    .withColumn("taxa_avaliacao_baixa_pct", (F.col("avaliacoes_baixas") / F.col("total_pedidos")) * 100)

df_atrasos.write.mode("overwrite").parquet(args['GOLD_PATH'] + "analise_atrasos_avaliacoes/")
print(f"[INFO] Tabela analise_atrasos_avaliacoes salva: {df_atrasos.count()} registros")

# ---- GOLD TABLE 2: Análise de Cancelamentos e Devoluções ----
print("[INFO] Criando tabela gold: analise_cancelamentos_devolucoes")

df_cancel_dev = df_silver \
    .withColumn("foi_cancelado", F.when(F.col("status_pedido") == "cancelado", 1).otherwise(0)) \
    .withColumn("foi_devolvido", F.when(F.col("status_pedido") == "devolvido", 1).otherwise(0)) \
    .groupBy("estado", "categoria", "canal", "forma_pagamento") \
    .agg(
        F.count("*").alias("total_pedidos"),
        F.sum("foi_cancelado").alias("total_cancelados"),
        F.sum("foi_devolvido").alias("total_devolvidos"),
        F.sum("valor_total").alias("valor_total_vendas"),
        F.avg("valor_total").alias("ticket_medio"),
        F.countDistinct("cliente_id").alias("clientes_unicos")
    ) \
    .withColumn("taxa_cancelamento_pct", (F.col("total_cancelados") / F.col("total_pedidos")) * 100) \
    .withColumn("taxa_devolucao_pct", (F.col("total_devolvidos") / F.col("total_pedidos")) * 100) \
    .withColumn("taxa_perda_pct", 
        ((F.col("total_cancelados") + F.col("total_devolvidos")) / F.col("total_pedidos")) * 100)

df_cancel_dev.write.mode("overwrite").parquet(args['GOLD_PATH'] + "analise_cancelamentos_devolucoes/")
print(f"[INFO] Tabela analise_cancelamentos_devolucoes salva: {df_cancel_dev.count()} registros")

# ---- GOLD TABLE 3: Análise de Sazonalidade (Mês a Mês) ----
print("[INFO] Criando tabela gold: analise_sazonalidade")

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
print(f"[INFO] Tabela analise_sazonalidade salva: {df_sazonalidade.count()} registros")

# ---- GOLD TABLE 4: Visão Consolidada de Pedidos (Fact Table) ----
print("[INFO] Criando tabela gold: fato_pedidos")

df_fato_pedidos = df_silver.select(
    "pedido_id",
    "item_id",
    "data_pedido",
    "cliente_id",
    "cliente_segmento",
    "cliente_data_cadastro",
    "estado",
    "cidade",
    "canal",
    "categoria",
    "sku",
    "produto",
    "marca",
    "fornecedor",
    "quantidade",
    "preco_unitario",
    "valor_total",
    "desconto_pct",
    "forma_pagamento",
    "parcelas",
    "status_pedido",
    "transportadora",
    "centro_distribuicao",
    "prazo_estimado_dias",
    "prazo_real_dias",
    "data_entrega",
    "atraso_dias",
    "nota_avaliacao"
)

df_fato_pedidos.write.mode("overwrite").parquet(args['GOLD_PATH'] + "fato_pedidos/")
print(f"[INFO] Tabela fato_pedidos salva: {df_fato_pedidos.count()} registros")

print("[INFO] ETL concluído com sucesso!")
job.commit()
