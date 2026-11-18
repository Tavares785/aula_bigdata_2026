"""
ETL MercadoFacil (Glue 4.0 / PySpark): raw (CSV) -> silver + quarentena -> gold.

Cada linha do raw termina em exatamente um destino (silver ou quarentena), e o
job falha se essa conta nao fechar. As regras estao em aws-lab/REGRAS_SILVER.md.
"""
import sys

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

TOKENS_NULOS = ["", "-", "n/a", "na", "null", "none", "nan"]
COLUNAS_PII = ["cliente_nome", "cliente_email", "cliente_cpf"]

QTD_MIN, QTD_MAX = 1, 4
DESCONTOS_VALIDOS = [0, 5, 10, 15, 20, 30, 40]
# Faixa observada de preco/custo no raw e 1,29-2,37. Um preco derivado do total
# fora desta margem indica total corrompido, entao a linha vai para a quarentena.
PRECO_CUSTO_MIN, PRECO_CUSTO_MAX = 1.2, 2.5
TOLERANCIA_TOTAL = 0.05

CATEGORIAS = {
    "eletronicos": "Eletrônicos", "eletronico": "Eletrônicos",
    "moda": "Moda", "mod": "Moda",
    "casa e cozinha": "Casa e Cozinha", "casa e cozinh": "Casa e Cozinha",
    "esporte": "Esporte", "esport": "Esporte",
    "beleza e saude": "Beleza e Saúde", "beleza e saud": "Beleza e Saúde",
    "livros": "Livros", "livro": "Livros",
    "brinquedos": "Brinquedos", "brinquedo": "Brinquedos",
    "pet": "Pet", "pe": "Pet",
}
STATUS = {
    "entregue": "entregue", "delivered": "entregue",
    "cancelado": "cancelado", "canceled": "cancelado",
    "devolvido": "devolvido", "returned": "devolvido",
}
PAGAMENTOS = {
    "cartao_credito": "cartao_credito", "cartao credito": "cartao_credito",
    "credito": "cartao_credito", "cartao de credito": "cartao_credito",
    "cartao_debito": "cartao_debito", "cartao debito": "cartao_debito",
    "debito": "cartao_debito", "cartao de debito": "cartao_debito",
    "pix": "pix",
    "boleto": "boleto", "boleto bancario": "boleto",
}
TRANSPORTADORAS = {
    "correios": "Correios", "loggi": "Loggi", "jadlog": "Jadlog",
    "entrega propria": "Entrega Própria",
}
CANAIS = {
    "app": "app", "site": "site",
    "marketplace_parceiro": "marketplace_parceiro",
}
SEGMENTOS = {"novo": "novo", "recorrente": "recorrente", "vip": "vip"}
UFS = {
    "sp": "SP", "sao paulo": "SP", "rj": "RJ", "rio de janeiro": "RJ",
    "mg": "MG", "minas gerais": "MG", "rs": "RS", "rio grande do sul": "RS",
    "pr": "PR", "parana": "PR", "pe": "PE", "pernambuco": "PE",
    "ba": "BA", "bahia": "BA", "ce": "CE", "ceara": "CE",
    "df": "DF", "distrito federal": "DF", "am": "AM", "amazonas": "AM",
    "pa": "PA", "para": "PA",
}
REGIOES = {
    "SP": "Sudeste", "RJ": "Sudeste", "MG": "Sudeste", "RS": "Sul", "PR": "Sul",
    "PE": "Nordeste", "BA": "Nordeste", "CE": "Nordeste",
    "DF": "Centro-Oeste", "AM": "Norte", "PA": "Norte",
}
CDS = {
    "SP": "CD-SUDESTE", "RJ": "CD-SUDESTE", "MG": "CD-SUDESTE",
    "RS": "CD-SUL", "PR": "CD-SUL",
    "PE": "CD-NORDESTE", "BA": "CD-NORDESTE", "CE": "CD-NORDESTE",
    "DF": "CD-CENTRO-OESTE", "AM": "CD-NORTE", "PA": "CD-NORTE",
}
CIDADES = {
    nome.lower().translate(str.maketrans("áâãéêíóôõúç", "aaaeeiooouc")): nome
    for nome in [
        "Belo Horizonte", "Belém", "Brasília", "Campinas", "Caxias do Sul",
        "Curitiba", "Feira de Santana", "Fortaleza", "Juiz de Fora", "Londrina",
        "Manaus", "Niterói", "Olinda", "Petrópolis", "Porto Alegre", "Recife",
        "Rio de Janeiro", "Salvador", "Santos", "Sobral", "Sorocaba",
        "São Paulo", "Uberlândia",
    ]
}


def limpar(coluna):
    """Remove espacos das pontas e troca marcadores de ausencia por null."""
    texto = F.regexp_replace(F.col(coluna), r"^\s+|\s+$", "")
    return F.when(~F.lower(texto).isin(TOKENS_NULOS), texto)


def chave(coluna):
    """Chave de comparacao: minuscula e sem acentos."""
    return F.translate(
        F.lower(limpar(coluna)), "áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc"
    )


def mapear(coluna, dominio):
    """Traduz para o valor canonico; fora do dominio vira null."""
    pares = [F.lit(v) for item in dominio.items() for v in item]
    return F.create_map(*pares)[chave(coluna)]


def numero(coluna):
    """Converte '1.234,56', 'R$ 99,90', '15%' e '99.90' para double."""
    texto = F.regexp_replace(limpar(coluna), r"(?i)r\$|%|\s", "")
    normal = F.when(
        texto.contains(","),
        F.regexp_replace(F.regexp_replace(texto, r"\.", ""), ",", "."),
    ).otherwise(texto)
    return F.when(normal.rlike(r"^-?\d+(\.\d+)?$"), normal.cast("double"))


def data(coluna):
    """Aceita yyyy-MM-dd, yyyy-MM-dd HH:mm:ss e dd/MM/yyyy; o resto vira null."""
    texto = limpar(coluna)
    return F.coalesce(
        F.when(
            texto.rlike(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$"),
            F.to_date(F.substring(texto, 1, 10), "yyyy-MM-dd"),
        ),
        F.when(texto.rlike(r"^\d{2}/\d{2}/\d{4}$"), F.to_date(texto, "dd/MM/yyyy")),
    )


def separar_duplicados(raw: DataFrame):
    """Mantem a primeira ocorrencia de cada item_id e devolve as demais a parte."""
    janela = Window.partitionBy("item_id").orderBy("_ordem")
    marcado = (
        raw.withColumn("_ordem", F.monotonically_increasing_id())
        .withColumn("_ocorrencia", F.row_number().over(janela))
        .drop("_ordem")
        .cache()
    )
    unicos = marcado.filter("_ocorrencia = 1").drop("_ocorrencia")
    duplicados = (
        marcado.filter("_ocorrencia > 1")
        .drop("_ocorrencia")
        .withColumn("motivo_quarentena", F.lit("duplicado_item_id"))
    )
    return unicos, duplicados


def padronizar(df: DataFrame) -> DataFrame:
    """Tipa e padroniza cada coluna, preservando o raw em colunas originais."""
    pedido = Window.partitionBy("pedido_id")
    sku = Window.partitionBy("sku")
    cliente = Window.partitionBy("cliente_id")

    produto = limpar("produto")
    return (
        df.withColumn("data_pedido_t", data("data_pedido"))
        .withColumn(
            "data_pedido_t",
            F.coalesce(
                F.col("data_pedido_t"),
                F.first("data_pedido_t", ignorenulls=True).over(pedido),
            ),
        )
        .withColumn("data_cadastro_t", data("cliente_data_cadastro"))
        .withColumn("data_entrega_lida", data("data_entrega"))
        .withColumn("status_t", mapear("status_pedido", STATUS))
        .withColumn("canal_t", mapear("canal", CANAIS))
        .withColumn("categoria_t", mapear("categoria", CATEGORIAS))
        .withColumn("pagamento_t", mapear("forma_pagamento", PAGAMENTOS))
        .withColumn("transportadora_t", mapear("transportadora", TRANSPORTADORAS))
        .withColumn("estado_t", mapear("estado", UFS))
        .withColumn("cidade_t", mapear("cidade", CIDADES))
        .withColumn("regiao", F.create_map(*[F.lit(v) for i in REGIOES.items() for v in i])[F.col("estado_t")])
        .withColumn(
            "centro_distribuicao_t",
            F.coalesce(
                limpar("centro_distribuicao"),
                F.create_map(*[F.lit(v) for i in CDS.items() for v in i])[F.col("estado_t")],
            ),
        )
        .withColumn("segmento_lido", mapear("cliente_segmento", SEGMENTOS))
        .withColumn(
            "segmento_t",
            F.coalesce(
                F.first("segmento_lido", ignorenulls=True).over(cliente),
                F.lit("nao_informado"),
            ),
        )
        .withColumn(
            "produto_t",
            F.coalesce(
                F.first(F.when(produto != F.upper(produto), produto), ignorenulls=True).over(sku),
                produto,
            ),
        )
        .withColumn("marca_t", F.first(limpar("marca"), ignorenulls=True).over(sku))
        .withColumn("fornecedor_t", F.first(limpar("fornecedor"), ignorenulls=True).over(sku))
        .withColumn("custo_t", numero("custo_unitario"))
        .withColumn("preco_lido", numero("preco_unitario"))
        .withColumn("qtd_lida", numero("quantidade"))
        .withColumn("desconto_lido", numero("desconto_pct"))
        .withColumn("total_lido", numero("valor_total"))
        .withColumn("parcelas_lida", numero("parcelas").cast("int"))
        .withColumn(
            "parcelas_t",
            F.coalesce(
                F.col("parcelas_lida"),
                F.first("parcelas_lida", ignorenulls=True).over(pedido),
                F.when(F.col("pagamento_t") != "cartao_credito", F.lit(1)),
            ),
        )
        .withColumn("prazo_estimado_t", numero("prazo_estimado_dias").cast("int"))
        .withColumn("prazo_real_lido", numero("prazo_real_dias").cast("int"))
        .withColumn("atraso_lido", numero("atraso_dias").cast("int"))
        .withColumn("nota_lida", numero("nota_avaliacao").cast("int"))
        .withColumn("comentario_t", limpar("comentario"))
    )


def reconstruir_valores(df: DataFrame) -> DataFrame:
    """Recupera preco, quantidade e desconto a partir dos demais campos do item."""
    qtd_ok = F.col("qtd_lida").between(QTD_MIN, QTD_MAX) & (F.col("qtd_lida") % 1 == 0)
    desconto_ok = F.col("desconto_lido").isin(DESCONTOS_VALIDOS)
    total = F.abs(F.col("total_lido"))

    return (
        df.withColumn("qtd_base", F.when(qtd_ok, F.col("qtd_lida")))
        .withColumn("desconto_base", F.when(desconto_ok, F.col("desconto_lido")))
        .withColumn(
            "preco_calc",
            F.round(total / (F.col("qtd_base") * (1 - F.col("desconto_base") / 100)), 2),
        )
        .withColumn(
            "preco_t",
            F.coalesce(
                F.col("preco_lido"),
                F.when(
                    F.col("preco_calc").between(
                        F.col("custo_t") * PRECO_CUSTO_MIN, F.col("custo_t") * PRECO_CUSTO_MAX
                    ),
                    F.col("preco_calc"),
                ),
            ),
        )
        .withColumn("qtd_calc", total / (F.col("preco_t") * (1 - F.col("desconto_base") / 100)))
        .withColumn(
            "qtd_t",
            F.coalesce(
                F.col("qtd_base"),
                F.when(
                    (F.abs(F.col("qtd_calc") - F.round("qtd_calc")) <= 0.01)
                    & F.round("qtd_calc").between(QTD_MIN, QTD_MAX),
                    F.round("qtd_calc"),
                ),
            ).cast("int"),
        )
        .withColumn("desconto_calc", (1 - total / (F.col("preco_t") * F.col("qtd_t"))) * 100)
        .withColumn(
            "desconto_t",
            F.coalesce(
                F.col("desconto_base"),
                F.when(
                    (F.abs(F.col("desconto_calc") - F.round("desconto_calc")) <= 0.1)
                    & F.round("desconto_calc").isin(DESCONTOS_VALIDOS),
                    F.round("desconto_calc"),
                ),
            ),
        )
        .withColumn(
            "total_t",
            F.round(F.col("preco_t") * F.col("qtd_t") * (1 - F.col("desconto_t") / 100), 2),
        )
    )


def reconstruir_logistica(df: DataFrame) -> DataFrame:
    """Reconcilia data de entrega, prazo real e atraso; cancelado nao tem entrega."""
    ativo = F.col("status_t") != "cancelado"
    entrega_valida = F.when(
        F.col("data_entrega_lida") >= F.col("data_pedido_t"), F.col("data_entrega_lida")
    )
    prazo_valido = F.when(F.col("prazo_real_lido") >= 0, F.col("prazo_real_lido"))

    return (
        df.withColumn(
            "prazo_real_t",
            F.when(
                ativo,
                F.coalesce(prazo_valido, F.datediff(entrega_valida, F.col("data_pedido_t"))),
            ),
        )
        .withColumn(
            "data_entrega_t",
            F.when(
                ativo,
                F.coalesce(entrega_valida, F.expr("date_add(data_pedido_t, prazo_real_t)")),
            ),
        )
        .withColumn(
            "atraso_t",
            F.when(
                F.col("prazo_real_t").isNotNull(),
                F.greatest(F.col("prazo_real_t") - F.col("prazo_estimado_t"), F.lit(0)),
            ),
        )
        .withColumn("nota_t", F.when(F.col("nota_lida").between(1, 5), F.col("nota_lida")))
    )


def motivos_quarentena(df: DataFrame) -> DataFrame:
    """Lista todos os motivos que impedem o aproveitamento da linha."""
    regras = {
        "data_pedido_invalida": "data_pedido_t",
        "status_desconhecido": "status_t",
        "canal_desconhecido": "canal_t",
        "categoria_desconhecida": "categoria_t",
        "pagamento_desconhecido": "pagamento_t",
        "transportadora_desconhecida": "transportadora_t",
        "estado_desconhecido": "estado_t",
        "cidade_desconhecida": "cidade_t",
        "preco_irrecuperavel": "preco_t",
        "quantidade_irrecuperavel": "qtd_t",
        "desconto_irrecuperavel": "desconto_t",
    }
    motivos = [F.when(F.col(c).isNull(), F.lit(m)) for m, c in regras.items()]
    return df.withColumn("motivo_quarentena", F.concat_ws(";", *motivos))


def flags_qualidade(df: DataFrame) -> DataFrame:
    """Registra na silver quais campos foram corrigidos ou derivados."""
    flags = {
        "preco_derivado": F.col("preco_lido").isNull(),
        "quantidade_derivada": F.col("qtd_base").isNull(),
        "desconto_derivado": F.col("desconto_base").isNull(),
        "valor_total_recalculado": F.col("total_lido").isNull()
        | (F.abs(F.col("total_lido") - F.col("total_t")) > TOLERANCIA_TOTAL),
        "atraso_recalculado": F.col("atraso_t").isNotNull()
        & (F.col("atraso_lido").isNull() | (F.col("atraso_lido") != F.col("atraso_t"))),
        "nota_invalida_removida": F.col("nota_lida").isNotNull() & F.col("nota_t").isNull(),
        "logistica_incompleta": (F.col("status_t") != "cancelado") & F.col("prazo_real_t").isNull(),
    }
    return df.withColumn(
        "qualidade_flags",
        F.concat_ws(",", *[F.when(cond, F.lit(nome)) for nome, cond in flags.items()]),
    )


def montar_silver(df: DataFrame, salt: str) -> DataFrame:
    """Seleciona o schema final, sem dados pessoais diretos (LGPD)."""
    dinheiro = "decimal(12,2)"
    return df.select(
        "item_id",
        "pedido_id",
        F.col("data_pedido_t").alias("data_pedido"),
        F.date_format("data_pedido_t", "yyyy-MM").alias("ano_mes"),
        F.col("status_t").alias("status_pedido"),
        F.col("canal_t").alias("canal"),
        F.sha2(F.concat(F.lit(salt), F.col("cliente_id")), 256).alias("cliente_hash"),
        F.col("segmento_t").alias("cliente_segmento"),
        F.col("data_cadastro_t").alias("cliente_data_cadastro"),
        F.col("estado_t").alias("estado"),
        "regiao",
        F.col("cidade_t").alias("cidade"),
        F.col("categoria_t").alias("categoria"),
        "sku",
        F.col("produto_t").alias("produto"),
        F.col("marca_t").alias("marca"),
        F.col("fornecedor_t").alias("fornecedor"),
        F.col("custo_t").cast(dinheiro).alias("custo_unitario"),
        F.col("preco_t").cast(dinheiro).alias("preco_unitario"),
        F.col("qtd_t").alias("quantidade"),
        F.col("desconto_t").cast("int").alias("desconto_pct"),
        F.col("total_t").cast(dinheiro).alias("valor_total"),
        F.col("pagamento_t").alias("forma_pagamento"),
        F.col("parcelas_t").alias("parcelas"),
        F.col("transportadora_t").alias("transportadora"),
        F.col("centro_distribuicao_t").alias("centro_distribuicao"),
        F.col("prazo_estimado_t").alias("prazo_estimado_dias"),
        F.col("prazo_real_t").alias("prazo_real_dias"),
        F.col("data_entrega_t").alias("data_entrega"),
        F.col("atraso_t").alias("atraso_dias"),
        (F.col("atraso_t") > 0).alias("entrega_atrasada"),
        F.col("nota_t").alias("nota_avaliacao"),
        F.col("comentario_t").alias("comentario"),
        "qualidade_flags",
    )


def montar_quarentena(df: DataFrame, colunas_raw, salt: str) -> DataFrame:
    """Guarda a linha original com o motivo, pseudonimizando o cliente."""
    colunas = [c for c in colunas_raw if c not in COLUNAS_PII + ["cliente_id"]]
    return df.select(
        F.sha2(F.concat(F.lit(salt), F.col("cliente_id")), 256).alias("cliente_hash"),
        *colunas,
        "motivo_quarentena",
    )


def pct(condicao, base="true"):
    """Percentual de linhas que atendem a condicao, dentro da base informada."""
    return F.round(
        100 * F.sum(F.when(F.expr(condicao), 1).otherwise(0))
        / F.sum(F.when(F.expr(base), 1).otherwise(0)),
        2,
    )


def gold_atraso_estado_mes(silver: DataFrame) -> DataFrame:
    """Onde e quando os atrasos acontecem."""
    return (
        silver.filter("atraso_dias IS NOT NULL")
        .groupBy("regiao", "estado", "ano_mes")
        .agg(
            F.countDistinct("pedido_id").alias("pedidos"),
            F.count("*").alias("itens"),
            pct("entrega_atrasada").alias("pct_itens_atrasados"),
            F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
            F.round(F.avg(F.when(F.col("entrega_atrasada"), F.col("atraso_dias"))), 2).alias(
                "atraso_medio_quando_atrasa"
            ),
            F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
        )
    )


def gold_atraso_vs_avaliacao(silver: DataFrame) -> DataFrame:
    """Relacao entre o tamanho do atraso, a nota e a devolucao."""
    faixa = (
        F.when(F.col("atraso_dias") == 0, "1. no prazo")
        .when(F.col("atraso_dias") <= 3, "2. 1 a 3 dias")
        .when(F.col("atraso_dias") <= 7, "3. 4 a 7 dias")
        .otherwise("4. 8 dias ou mais")
    )
    return (
        silver.filter("atraso_dias IS NOT NULL")
        .withColumn("faixa_atraso", faixa)
        .groupBy("faixa_atraso")
        .agg(
            F.count("*").alias("itens"),
            F.count("nota_avaliacao").alias("itens_avaliados"),
            F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
            pct("nota_avaliacao <= 2", "nota_avaliacao IS NOT NULL").alias("pct_notas_baixas"),
            pct("status_pedido = 'devolvido'").alias("pct_devolvidos"),
        )
    )


def gold_cancelamento_devolucao(silver: DataFrame) -> DataFrame:
    """Cancelamentos e devolucoes por categoria, canal e estado."""
    return silver.groupBy("categoria", "canal", "regiao", "estado").agg(
        F.count("*").alias("itens"),
        F.sum(F.when(F.col("status_pedido") == "cancelado", 1).otherwise(0)).alias("itens_cancelados"),
        F.sum(F.when(F.col("status_pedido") == "devolvido", 1).otherwise(0)).alias("itens_devolvidos"),
        pct("status_pedido = 'cancelado'").alias("pct_cancelados"),
        pct("status_pedido = 'devolvido'").alias("pct_devolvidos"),
        F.sum(
            F.when(F.col("status_pedido") != "entregue", F.col("valor_total")).otherwise(0)
        ).alias("valor_perdido"),
    )


def gold_vendas_sazonalidade(silver: DataFrame) -> DataFrame:
    """Vendas e logistica por mes e periodo comercial (Black Friday e Natal)."""
    periodo = (
        F.when(F.col("data_pedido").between("2025-11-21", "2025-11-30"), "black_friday")
        .when(F.col("data_pedido").between("2025-12-01", "2025-12-24"), "natal")
        .otherwise("regular")
    )
    entregue = F.col("status_pedido") == "entregue"
    return (
        silver.withColumn("periodo_comercial", periodo)
        .groupBy("ano_mes", "periodo_comercial")
        .agg(
            F.countDistinct("pedido_id").alias("pedidos"),
            F.count("*").alias("itens"),
            F.sum(F.when(entregue, F.col("valor_total")).otherwise(0)).alias("receita_entregue"),
            F.sum(
                F.when(
                    entregue,
                    F.col("valor_total") - F.col("custo_unitario") * F.col("quantidade"),
                ).otherwise(0)
            ).alias("margem_bruta"),
            pct("entrega_atrasada", "atraso_dias IS NOT NULL").alias("pct_itens_atrasados"),
            F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
        )
    )


def executar(spark, raw_path, silver_path, gold_path, quarentena_path, salt):
    """Roda o pipeline completo e devolve as contagens de reconciliacao."""
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")

    raw = spark.read.option("header", True).option("inferSchema", False).csv(raw_path)
    colunas_raw = raw.columns
    unicos, duplicados = separar_duplicados(raw)

    tratado = motivos_quarentena(
        reconstruir_logistica(reconstruir_valores(padronizar(unicos)))
    ).cache()

    aprovados = flags_qualidade(tratado.filter("motivo_quarentena = ''"))
    silver = montar_silver(aprovados, salt)
    rejeitados = tratado.filter("motivo_quarentena <> ''").select(
        *colunas_raw, "motivo_quarentena"
    )
    quarentena = montar_quarentena(
        rejeitados.unionByName(duplicados), colunas_raw, salt
    )

    silver_saida = f"{silver_path.rstrip('/')}/itens_pedido"
    quarentena_saida = f"{quarentena_path.rstrip('/')}/itens_rejeitados"
    silver.coalesce(1).write.mode("overwrite").parquet(silver_saida)
    quarentena.coalesce(1).write.mode("overwrite").parquet(quarentena_saida)

    silver_lida = spark.read.parquet(silver_saida)
    tabelas_gold = {
        "atraso_estado_mes": gold_atraso_estado_mes(silver_lida),
        "atraso_vs_avaliacao": gold_atraso_vs_avaliacao(silver_lida),
        "cancelamento_devolucao": gold_cancelamento_devolucao(silver_lida),
        "vendas_sazonalidade": gold_vendas_sazonalidade(silver_lida),
    }
    for nome, tabela in tabelas_gold.items():
        tabela.coalesce(1).write.mode("overwrite").parquet(f"{gold_path.rstrip('/')}/{nome}")

    contagens = {
        "raw": raw.count(),
        "silver": silver_lida.count(),
        "quarentena": spark.read.parquet(quarentena_saida).count(),
    }
    print(f"[reconciliacao] {contagens}")
    if contagens["raw"] != contagens["silver"] + contagens["quarentena"]:
        raise RuntimeError(f"Reconciliacao falhou: {contagens}")
    return contagens


def main():
    from awsglue.context import GlueContext
    from awsglue.job import Job
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext

    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "RAW_PATH", "SILVER_PATH", "GOLD_PATH", "QUARANTINE_PATH", "LGPD_SALT"],
    )
    glue_context = GlueContext(SparkContext.getOrCreate())
    spark: SparkSession = glue_context.spark_session
    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)
    executar(
        spark,
        args["RAW_PATH"],
        args["SILVER_PATH"],
        args["GOLD_PATH"],
        args["QUARANTINE_PATH"],
        args["LGPD_SALT"],
    )
    job.commit()


if __name__ == "__main__":
    main()
