"""
ETL MercadoFacil - Aula 12 (Ingestao e Pre-processamento)

Arquitetura medalhao, rodando como Glue Job (PySpark, Glue 4.0 / Spark 3.3):

    raw (CSV como chegou)
      -> silver/pedidos_itens  (Parquet, tipado, padronizado, deduplicado, sem PII)
      -> quarentena/           (Parquet, linhas inaproveitaveis + motivo, sem PII)
      -> gold/<tabela>         (Parquet, tabelas de negocio agregadas)

As regras aplicadas estao documentadas em aws-lab/REGRAS_SILVER.md.

No Glue os caminhos chegam como argumentos do job (--RAW_PATH, --SILVER_PATH,
--GOLD_PATH, --QUARANTINE_PATH). Fora do Glue o script tambem roda com
spark-submit/python usando os mesmos argumentos, o que permite testa-lo
localmente antes de subir para a AWS.
"""
import argparse
import sys

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

ARG_NAMES = ["RAW_PATH", "SILVER_PATH", "GOLD_PATH", "QUARANTINE_PATH"]

# Valores que, depois do trim, significam "sem informacao".
NULL_TOKENS = ["", "null", "n/a", "na", "-", "none", "nan"]

ACENTOS = "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
SEM_ACENTOS = "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC"

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

REGIAO_POR_UF = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

CIDADES = [
    "Belém", "Belo Horizonte", "Brasília", "Campinas", "Caxias do Sul",
    "Curitiba", "Feira de Santana", "Fortaleza", "Juiz de Fora", "Londrina",
    "Manaus", "Niterói", "Olinda", "Petrópolis", "Porto Alegre", "Recife",
    "Rio de Janeiro", "Salvador", "Santos", "São Paulo", "Sobral", "Sorocaba",
    "Uberlândia",
]

CATEGORIAS = [
    "Eletrônicos", "Moda", "Casa e Cozinha", "Esporte", "Beleza e Saúde",
    "Livros", "Brinquedos", "Pet",
]

STATUS = {
    "entregue": "entregue", "delivered": "entregue",
    "cancelado": "cancelado", "canceled": "cancelado", "cancelled": "cancelado",
    "devolvido": "devolvido", "returned": "devolvido",
}

PAGAMENTO = {
    "cartao credito": "cartao_credito", "cartao de credito": "cartao_credito",
    "credito": "cartao_credito",
    "cartao debito": "cartao_debito", "cartao de debito": "cartao_debito",
    "debito": "cartao_debito",
    "pix": "pix",
    "boleto": "boleto", "boleto bancario": "boleto",
}

TRANSPORTADORAS = {
    "correios": "Correios", "loggi": "Loggi", "jadlog": "Jadlog",
    "entrega propria": "Entrega Própria",
}

CANAIS = ["app", "site", "marketplace_parceiro"]
SEGMENTOS = ["novo", "recorrente", "vip"]

PII_COLS = ["cliente_nome", "cliente_email", "cliente_cpf"]


# =============================================================================
# Inicializacao (Glue ou local)
# =============================================================================
def init_job():
    """Retorna (spark, args, job). `job` e None fora do Glue."""
    try:
        from awsglue.context import GlueContext
        from awsglue.job import Job
        from awsglue.utils import getResolvedOptions
        from pyspark.context import SparkContext
    except ImportError:
        parser = argparse.ArgumentParser(description="ETL MercadoFacil (modo local)")
        for name in ARG_NAMES:
            parser.add_argument(f"--{name}", required=True)
        args = vars(parser.parse_args())
        spark = SparkSession.builder.appName("etl-mercadofacil-local").getOrCreate()
        return spark, args, None

    args = getResolvedOptions(sys.argv, ["JOB_NAME"] + ARG_NAMES)
    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)
    return spark, args, job


def join_path(base, *parts):
    return "/".join([base.rstrip("/")] + [p.strip("/") for p in parts]) + "/"


# =============================================================================
# Funcoes de limpeza (expressoes de coluna)
# =============================================================================
def clean_str(col_name):
    """Trim + converte os varios marcadores de nulo (NULL, N/A, -, '') em null."""
    c = F.trim(F.col(col_name))
    return F.when(F.lower(c).isin(NULL_TOKENS), F.lit(None)).otherwise(c)


def norm_key(col_expr):
    """Chave de comparacao: minusculas, sem acento, espacos simples."""
    c = F.lower(F.translate(col_expr, ACENTOS, SEM_ACENTOS))
    return F.trim(F.regexp_replace(c, r"\s+", " "))


def map_values(mapping, key_expr):
    """Procura key_expr num dicionario Python (vira um MapType literal)."""
    pairs = []
    for k, v in mapping.items():
        pairs += [F.lit(k), F.lit(v)]
    return F.create_map(*pairs)[key_expr]


def strip_accents_py(s):
    return s.lower().translate(str.maketrans(ACENTOS.lower(), SEM_ACENTOS.lower()))


def parse_money(col_name):
    """'R$ 1.234,56' | '1234,56' | '1234.56' -> 1234.56 (double)."""
    c = clean_str(col_name)
    c = F.trim(F.regexp_replace(c, r"(?i)R\$", ""))
    c = F.when(
        c.contains(","),
        F.regexp_replace(F.regexp_replace(c, r"\.", ""), ",", "."),
    ).otherwise(c)
    return F.when(c.rlike(r"^-?\d+(\.\d+)?$"), c.cast("double"))


def parse_int(col_expr):
    return F.when(col_expr.rlike(r"^-?\d+$"), col_expr.cast("int"))


def parse_date(col_name):
    """Aceita yyyy-MM-dd, dd/MM/yyyy e yyyy-MM-dd HH:mm:ss.
    Datas impossiveis (2025-13-45, 31/02/2025, 0000-00-00) e textos
    ('ontem') viram null."""
    c = clean_str(col_name)
    return (
        F.when(c.rlike(r"^\d{4}-\d{2}-\d{2}$"), F.to_date(c, "yyyy-MM-dd"))
        .when(c.rlike(r"^\d{2}/\d{2}/\d{4}$"), F.to_date(c, "dd/MM/yyyy"))
        .when(
            c.rlike(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),
            F.to_date(F.substring(c, 1, 10), "yyyy-MM-dd"),
        )
    )


def cpf_formato_valido(col_name):
    """Flag de formato do CPF (11 digitos, com ou sem mascara). So a flag vai
    para a silver; o CPF em si e descartado (LGPD). Os CPFs do dataset sao
    ficticios, por isso nao validamos os digitos verificadores."""
    c = clean_str(col_name)
    return c.rlike(r"^(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})$")


def mode_by(df, key, value_expr, out_name):
    """Valor mais frequente (nao nulo) de value_expr para cada `key`."""
    counts = (
        df.select(F.col(key), value_expr.alias(out_name))
        .where(F.col(key).isNotNull() & F.col(out_name).isNotNull())
        .groupBy(key, out_name)
        .count()
    )
    w = Window.partitionBy(key).orderBy(F.desc("count"), F.asc(out_name))
    return (
        counts.withColumn("_rn", F.row_number().over(w))
        .where("_rn = 1")
        .select(key, out_name)
    )


# =============================================================================
# raw -> silver + quarentena
# =============================================================================
def read_raw(spark, raw_path):
    return (
        spark.read.option("header", True)
        .option("encoding", "UTF-8")
        .option("quote", '"')
        .option("escape", '"')
        .option("inferSchema", False)  # tudo chega como texto
        .csv(raw_path)
        .withColumn("_linha_raw", F.monotonically_increasing_id())
    )


def standardize(raw):
    """Tipagem e padronizacao coluna a coluna (ainda sem filtrar nada)."""
    uf_raw = clean_str("estado")
    uf = F.when(F.length(uf_raw) == 2, F.upper(uf_raw)).otherwise(
        map_values(UF_POR_NOME, norm_key(uf_raw))
    )
    uf = F.when(uf.isin(list(REGIAO_POR_UF)), uf)

    cidade_map = {strip_accents_py(c): c for c in CIDADES}
    cidade_raw = clean_str("cidade")
    cidade = F.coalesce(map_values(cidade_map, norm_key(cidade_raw)), F.initcap(cidade_raw))

    categoria_map = {strip_accents_py(c): c for c in CATEGORIAS}
    canal = F.lower(clean_str("canal"))
    segmento = F.lower(clean_str("cliente_segmento"))
    desconto = parse_int(F.regexp_replace(clean_str("desconto_pct"), "%", ""))
    email = clean_str("cliente_email")

    return raw.select(
        "_linha_raw",
        clean_str("pedido_id").alias("pedido_id"),
        clean_str("item_id").alias("item_id"),
        parse_date("data_pedido").alias("data_pedido"),
        F.when(canal.isin(CANAIS), canal).alias("canal"),
        map_values(STATUS, norm_key(clean_str("status_pedido"))).alias("status_pedido"),
        # cliente (PII so para gerar flags; removida no select final)
        clean_str("cliente_id").alias("cliente_id"),
        F.coalesce(F.when(segmento.isin(SEGMENTOS), segmento), F.lit("nao_informado")).alias("cliente_segmento"),
        parse_date("cliente_data_cadastro").alias("cliente_data_cadastro"),
        email.rlike(r"^[^@\s]+@[^@\s]+\.[^@\s]+$").alias("cliente_email_valido"),
        cpf_formato_valido("cliente_cpf").alias("cliente_cpf_valido"),
        # destino
        uf.alias("estado"),
        map_values(REGIAO_POR_UF, uf).alias("regiao"),
        cidade.alias("cidade"),
        # produto
        F.upper(clean_str("sku")).alias("sku"),
        map_values(categoria_map, norm_key(clean_str("categoria"))).alias("_categoria_informada"),
        clean_str("produto").alias("_produto_informado"),
        clean_str("marca").alias("_marca_informada"),
        clean_str("fornecedor").alias("_fornecedor_informado"),
        parse_money("custo_unitario").alias("custo_unitario"),
        # valores
        parse_money("preco_unitario").alias("_preco_informado"),
        parse_int(clean_str("quantidade")).alias("quantidade"),
        desconto.alias("_desconto_informado"),
        parse_money("valor_total").alias("_valor_total_informado"),
        # pagamento
        map_values(PAGAMENTO, norm_key(F.regexp_replace(clean_str("forma_pagamento"), "_", " "))).alias("forma_pagamento"),
        parse_int(clean_str("parcelas")).alias("_parcelas_informadas"),
        # logistica
        map_values(TRANSPORTADORAS, norm_key(clean_str("transportadora"))).alias("transportadora"),
        F.upper(clean_str("centro_distribuicao")).alias("_cd_informado"),
        parse_int(clean_str("prazo_estimado_dias")).alias("prazo_estimado_dias"),
        parse_int(clean_str("prazo_real_dias")).alias("_prazo_real_informado"),
        parse_date("data_entrega").alias("_data_entrega_informada"),
        parse_int(clean_str("atraso_dias")).alias("_atraso_informado"),
        # avaliacao
        parse_int(clean_str("nota_avaliacao")).alias("_nota_informada"),
        F.regexp_replace(clean_str("comentario"), r"\s+", " ").alias("comentario"),
    )


def enrich_and_fix(std):
    """Regras que dependem de mais de uma coluna ou de outras linhas."""
    # --- Produto: SKU e a chave confiavel. Categoria/produto/marca/fornecedor
    # sao padronizados pelo valor mais frequente de cada SKU (corrige caixa,
    # grafias truncadas como 'Mod'/'Eletrônico' e preenche nulos).
    produto_dim = (
        mode_by(std, "sku", F.col("_categoria_informada"), "categoria")
        .join(mode_by(std, "sku", F.col("_produto_informado"), "produto"), "sku", "left")
        .join(mode_by(std, "sku", F.col("_marca_informada"), "marca"), "sku", "left")
        .join(mode_by(std, "sku", F.col("_fornecedor_informado"), "fornecedor"), "sku", "left")
    )
    # --- Centro de distribuicao: cada UF e atendida por um CD; nulos sao
    # preenchidos com o CD mais frequente da UF de destino.
    cd_por_uf = mode_by(std, "estado", F.col("_cd_informado"), "_cd_da_uf")

    df = std.join(F.broadcast(produto_dim), "sku", "left").join(
        F.broadcast(cd_por_uf), "estado", "left"
    )

    df = df.withColumn("categoria", F.coalesce("categoria", "_categoria_informada"))
    df = df.withColumn("centro_distribuicao", F.coalesce("_cd_informado", "_cd_da_uf"))

    # --- Valores: preco, desconto e total sao recalculados de forma consistente.
    q = F.col("quantidade").cast("double")
    df = df.withColumn(
        "preco_unitario",
        F.round(
            F.coalesce(
                F.col("_preco_informado"),
                F.col("_valor_total_informado") / (q * (1 - F.col("_desconto_informado") / 100.0)),
            ),
            2,
        ),
    )
    desconto_derivado = F.round(
        (1 - F.col("_valor_total_informado") / (F.col("preco_unitario") * q)) * 100
    ).cast("int")
    df = df.withColumn(
        "desconto_imputado",
        F.col("_desconto_informado").isNull(),
    ).withColumn(
        "desconto_pct",
        F.coalesce(
            F.col("_desconto_informado"),
            F.when(desconto_derivado.between(0, 100), desconto_derivado),
            F.lit(0),
        ),
    )
    df = df.withColumn(
        "valor_total",
        F.round(F.col("preco_unitario") * q * (1 - F.col("desconto_pct") / 100.0), 2),
    ).withColumn(
        "valor_total_divergente",
        F.coalesce(F.abs(F.col("valor_total") - F.col("_valor_total_informado")) > 0.05, F.lit(False)),
    )
    df = df.withColumn(
        "margem_bruta",
        F.round(F.col("valor_total") - F.col("custo_unitario") * q, 2),
    )

    # --- Parcelas: pix/boleto/debito sao sempre a vista.
    df = df.withColumn(
        "parcelas",
        F.when(F.col("forma_pagamento").isin("pix", "boleto", "cartao_debito"), F.lit(1))
        .otherwise(F.col("_parcelas_informadas")),
    )

    # --- Logistica. Pedido cancelado nao foi entregue: zera entrega/prazo/atraso.
    cancelado = F.col("status_pedido") == "cancelado"
    df = df.withColumn(
        "entrega_em_pedido_cancelado",
        cancelado & (F.col("_data_entrega_informada").isNotNull() | F.col("_prazo_real_informado").isNotNull()),
    )
    prazo_real = F.coalesce(
        F.col("_prazo_real_informado"),
        F.datediff("_data_entrega_informada", "data_pedido"),
    )
    prazo_real = F.when(prazo_real >= 0, prazo_real)
    # A logistica e do PEDIDO (igual em todos os itens): se um item perdeu o
    # prazo real, herda o valor informado nos outros itens do mesmo pedido.
    prazo_real = F.coalesce(prazo_real, F.max(prazo_real).over(Window.partitionBy("pedido_id")))
    df = df.withColumn("prazo_real_dias", F.when(~cancelado, prazo_real))
    df = df.withColumn(
        "data_entrega",
        F.when(
            ~cancelado,
            F.coalesce(
                F.col("_data_entrega_informada"),
                F.expr("date_add(data_pedido, prazo_real_dias)"),
            ),
        ),
    )
    # greatest() ignora null: sem prazo real o atraso fica desconhecido (null).
    df = df.withColumn(
        "atraso_dias",
        F.when(
            F.col("prazo_real_dias").isNotNull(),
            F.greatest(F.col("prazo_real_dias") - F.col("prazo_estimado_dias"), F.lit(0)),
        ),
    ).withColumn(
        "atraso_divergente",
        F.coalesce(F.col("atraso_dias") != F.col("_atraso_informado"), F.lit(False)),
    ).withColumn(
        "entregue_com_atraso",
        F.col("atraso_dias") > 0,
    )

    # --- Avaliacao: so 1..5 e valido.
    nota = F.col("_nota_informada")
    df = df.withColumn("nota_avaliacao", F.when(nota.between(1, 5), nota)).withColumn(
        "nota_fora_da_faixa", nota.isNotNull() & ~nota.between(1, 5)
    )
    return df


def quarantine_reasons(df):
    """Motivos que impedem a linha de ir para a silver."""
    w = Window.partitionBy("item_id").orderBy("_linha_raw")
    df = df.withColumn("_ordem_item", F.row_number().over(w))
    motivo = F.concat_ws(
        ";",
        F.when(F.col("pedido_id").isNull() | F.col("item_id").isNull(), F.lit("chave_ausente")),
        F.when(F.col("_ordem_item") > 1, F.lit("item_duplicado")),
        F.when(F.col("data_pedido").isNull(), F.lit("data_pedido_invalida")),
        F.when(F.col("status_pedido").isNull(), F.lit("status_desconhecido")),
        F.when(F.col("quantidade").isNull() | (F.col("quantidade") <= 0), F.lit("quantidade_invalida")),
        F.when(F.col("preco_unitario").isNull() | (F.col("preco_unitario") <= 0), F.lit("preco_invalido")),
        F.when(F.col("estado").isNull(), F.lit("estado_desconhecido")),
    )
    return df.withColumn("motivo_quarentena", motivo)


SILVER_COLS = [
    "pedido_id", "item_id", "data_pedido", "status_pedido", "canal",
    "cliente_id", "cliente_segmento", "cliente_data_cadastro",
    "cliente_email_valido", "cliente_cpf_valido",
    "estado", "regiao", "cidade",
    "sku", "categoria", "produto", "marca", "fornecedor",
    "custo_unitario", "preco_unitario", "quantidade", "desconto_pct",
    "desconto_imputado", "valor_total", "valor_total_divergente", "margem_bruta",
    "forma_pagamento", "parcelas",
    "transportadora", "centro_distribuicao", "prazo_estimado_dias",
    "prazo_real_dias", "data_entrega", "atraso_dias", "atraso_divergente",
    "entregue_com_atraso", "entrega_em_pedido_cancelado",
    "nota_avaliacao", "nota_fora_da_faixa", "comentario",
]


def build_silver(raw):
    df = quarantine_reasons(enrich_and_fix(standardize(raw)))
    df = df.cache()

    silver = (
        df.where(F.col("motivo_quarentena") == "")
        .select(*SILVER_COLS)
        .withColumn("ano_mes", F.date_format("data_pedido", "yyyy-MM"))
        .withColumn("dt_processamento", F.current_timestamp())
    )
    # Garantia final de unicidade (a quarentena ja separou as copias).
    silver = silver.dropDuplicates(["item_id"])

    # Quarentena guarda a linha ORIGINAL (texto do raw) + motivo, sem PII.
    quarentena = (
        raw.join(
            df.where(F.col("motivo_quarentena") != "").select("_linha_raw", "motivo_quarentena"),
            "_linha_raw",
        )
        .drop(*PII_COLS)
        .withColumnRenamed("_linha_raw", "id_linha_raw")
        .withColumn("dt_processamento", F.current_timestamp())
    )
    return silver, quarentena


# =============================================================================
# silver -> gold
# =============================================================================
def pct(cond_col, total_col="_total"):
    return F.round(100.0 * F.sum(F.col(cond_col).cast("int")) / F.count(total_col), 2)


def build_pedidos(silver):
    """Visao 1 linha = 1 pedido (pedido, cliente e logistica se repetem nos itens)."""
    return silver.groupBy("pedido_id").agg(
        F.first("data_pedido").alias("data_pedido"),
        F.first("ano_mes").alias("ano_mes"),
        F.first("status_pedido").alias("status_pedido"),
        F.first("canal").alias("canal"),
        F.first("estado").alias("estado"),
        F.first("regiao").alias("regiao"),
        F.first("transportadora", ignorenulls=True).alias("transportadora"),
        F.first("centro_distribuicao", ignorenulls=True).alias("centro_distribuicao"),
        F.max("prazo_estimado_dias").alias("prazo_estimado_dias"),
        F.max("prazo_real_dias").alias("prazo_real_dias"),
        F.max("atraso_dias").alias("atraso_dias"),
        # A nota e por item (produto): no pedido usamos a media.
        F.avg("nota_avaliacao").alias("nota_avaliacao"),
        F.sum("valor_total").alias("valor_pedido"),
        F.count("*").alias("itens"),
    )


def gold_entregas_estado_mes(pedidos):
    entregues = pedidos.where(F.col("atraso_dias").isNotNull()).withColumn(
        "_atrasado", F.col("atraso_dias") > 0
    ).withColumn("_total", F.lit(1))
    return entregues.groupBy("regiao", "estado", "ano_mes").agg(
        F.count("_total").alias("pedidos_entregues"),
        F.sum(F.col("_atrasado").cast("int")).alias("pedidos_atrasados"),
        pct("_atrasado").alias("pct_atrasados"),
        F.round(F.avg(F.when(F.col("_atrasado"), F.col("atraso_dias"))), 2).alias("atraso_medio_dias_quando_atrasa"),
        F.round(F.avg("prazo_estimado_dias"), 2).alias("prazo_estimado_medio"),
        F.round(F.avg("prazo_real_dias"), 2).alias("prazo_real_medio"),
        F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
    )


def gold_atraso_transportadora_cd(pedidos):
    entregues = pedidos.where(F.col("atraso_dias").isNotNull()).withColumn(
        "_atrasado", F.col("atraso_dias") > 0
    ).withColumn("_total", F.lit(1))
    return entregues.groupBy("transportadora", "centro_distribuicao", "regiao").agg(
        F.count("_total").alias("pedidos_entregues"),
        pct("_atrasado").alias("pct_atrasados"),
        F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
        F.round(F.avg("prazo_real_dias") - F.avg("prazo_estimado_dias"), 2).alias("desvio_medio_prazo_dias"),
        F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
    )


def faixa_atraso(col):
    return (
        F.when(col == 0, "0 - no prazo")
        .when(col <= 3, "1 - 1 a 3 dias")
        .when(col <= 7, "2 - 4 a 7 dias")
        .otherwise("3 - 8+ dias")
    )


def gold_atraso_vs_nota(silver):
    """Granularidade de item: a avaliacao (nota) e dada por item/produto."""
    base = (
        silver.where(F.col("atraso_dias").isNotNull())
        .withColumn("faixa_atraso", faixa_atraso(F.col("atraso_dias")))
        .withColumn("_avaliado", F.col("nota_avaliacao").isNotNull())
        .withColumn("_nota_baixa", F.col("nota_avaliacao") <= 2)
        .withColumn("_devolvido", F.col("status_pedido") == "devolvido")
        .withColumn("_total", F.lit(1))
    )
    return base.groupBy("faixa_atraso").agg(
        F.count("_total").alias("itens_entregues"),
        F.countDistinct("pedido_id").alias("pedidos"),
        F.sum(F.col("_avaliado").cast("int")).alias("itens_avaliados"),
        F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
        F.round(
            100.0 * F.sum(F.col("_nota_baixa").cast("int")) / F.sum(F.col("_avaliado").cast("int")), 2
        ).alias("pct_nota_1_ou_2"),
        pct("_devolvido").alias("pct_devolvidos"),
    )


def gold_cancelamento_devolucao(silver):
    base = (
        silver.withColumn("_cancelado", F.col("status_pedido") == "cancelado")
        .withColumn("_devolvido", F.col("status_pedido") == "devolvido")
        .withColumn("_total", F.lit(1))
    )
    return base.groupBy("categoria", "canal", "regiao").agg(
        F.count("_total").alias("itens"),
        F.sum(F.col("_cancelado").cast("int")).alias("itens_cancelados"),
        F.sum(F.col("_devolvido").cast("int")).alias("itens_devolvidos"),
        pct("_cancelado").alias("pct_cancelados"),
        pct("_devolvido").alias("pct_devolvidos"),
        F.round(F.sum(F.when(F.col("_cancelado") | F.col("_devolvido"), F.col("valor_total")).otherwise(0)), 2).alias(
            "receita_perdida"
        ),
    )


def gold_vendas_mensais_categoria(silver):
    base = silver.withColumn("mes", F.month("data_pedido")).withColumn(
        "periodo",
        F.when(F.col("mes") == 11, "black_friday").when(F.col("mes") == 12, "natal").otherwise("regular"),
    ).withColumn("_efetivado", F.col("status_pedido") == "entregue")
    return base.groupBy("ano_mes", "mes", "periodo", "categoria").agg(
        F.countDistinct("pedido_id").alias("pedidos"),
        F.sum("quantidade").alias("unidades"),
        F.round(F.sum("valor_total"), 2).alias("receita_bruta"),
        F.round(F.sum(F.when(F.col("_efetivado"), F.col("valor_total")).otherwise(0)), 2).alias("receita_liquida"),
        F.round(F.sum(F.when(F.col("_efetivado"), F.col("margem_bruta")).otherwise(0)), 2).alias("margem_liquida"),
        F.round(F.sum("valor_total") / F.countDistinct("pedido_id"), 2).alias("ticket_medio"),
        F.round(F.avg("desconto_pct"), 2).alias("desconto_medio_pct"),
        F.round(100.0 * F.avg(F.col("entregue_com_atraso").cast("int")), 2).alias("pct_itens_atrasados"),
    )


# =============================================================================
# Main
# =============================================================================
def write_parquet(df, path, partitions=1):
    df.coalesce(partitions).write.mode("overwrite").parquet(path)


def main():
    spark, args, job = init_job()
    # Datas como '31/02/2025' devem virar null (e nao gerar erro de parser).
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")
    spark.conf.set("spark.sql.session.timeZone", "America/Sao_Paulo")
    # Dataset pequeno (10 mil linhas): 200 particoes de shuffle so geram overhead.
    spark.conf.set("spark.sql.shuffle.partitions", "8")

    raw = read_raw(spark, args["RAW_PATH"]).cache()
    silver, quarentena = build_silver(raw)

    silver_path = join_path(args["SILVER_PATH"], "pedidos_itens")
    silver.coalesce(1).write.mode("overwrite").parquet(silver_path)
    quarentena.coalesce(1).write.mode("overwrite").parquet(args["QUARANTINE_PATH"])

    # A gold le a silver ja gravada (contrato entre camadas).
    silver = spark.read.parquet(silver_path).cache()
    pedidos = build_pedidos(silver).cache()

    gold = {
        "entregas_estado_mes": gold_entregas_estado_mes(pedidos),
        "atraso_transportadora_cd": gold_atraso_transportadora_cd(pedidos),
        "atraso_vs_nota": gold_atraso_vs_nota(silver),
        "cancelamento_devolucao": gold_cancelamento_devolucao(silver),
        "vendas_mensais_categoria": gold_vendas_mensais_categoria(silver),
    }
    for name, df in gold.items():
        write_parquet(df, join_path(args["GOLD_PATH"], name))

    # Resumo de qualidade nos logs (CloudWatch /aws-glue/jobs/output).
    n_raw = raw.count()
    n_silver = silver.count()
    q = spark.read.parquet(args["QUARANTINE_PATH"])
    n_q = q.count()
    print(f"[qualidade] raw={n_raw} silver={n_silver} quarentena={n_q} soma_ok={n_raw == n_silver + n_q}")
    (
        q.withColumn("motivo", F.explode(F.split("motivo_quarentena", ";")))
        .groupBy("motivo")
        .count()
        .orderBy(F.desc("count"))
        .show(truncate=False)
    )
    for name in gold:
        print(f"[gold] {name}: {spark.read.parquet(join_path(args['GOLD_PATH'], name)).count()} linhas")

    if job is not None:
        job.commit()


if __name__ == "__main__":
    main()
