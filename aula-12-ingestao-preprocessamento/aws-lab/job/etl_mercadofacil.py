"""
ETL MercadoFácil — raw (bronze) -> silver -> gold, em arquitetura medalhão.

Roda no AWS Glue 4.0 (PySpark). Os caminhos chegam como argumento, para
o mesmo script servir a outro bucket sem ser editado.

As regras aplicadas aqui saem de um perfil do CSV real, não de suposição,
e cada uma está justificada em `aws-lab/REGRAS_SILVER.md` com a contagem
do problema que ela trata.

**Nada é descartado em silêncio.** Linha que não pode virar fato vai para
`quarentena/`, com o motivo numa coluna. Um ETL que filtra e segue adiante
esconde exatamente o que precisa ser investigado.
"""

import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import DecimalType, IntegerType

# Os cinco marcadores de ausência que convivem no arquivo. Contados:
# 141 vazios, 129 `null`, 156 `-`, 136 `NULL` e 143 `N/A` só em
# `data_entrega`. Tratar um e esquecer os outros deixa a coluna metade
# limpa — e o erro só aparece na agregação.
MARCADORES_NULOS = ["", "-", "N/A", "NA", "NULL", "null", "none", "None"]

# Domínios canônicos. A chave é a forma já normalizada (minúscula, sem
# acento, sem espaço nas pontas); o valor é como fica na silver.
CATEGORIAS = {
    "eletronicos": "Eletronicos",
    "eletronico": "Eletronicos",
    "casa e cozinha": "Casa e Cozinha",
    "casa e cozinh": "Casa e Cozinha",
    "moda": "Moda",
    "beleza e saude": "Beleza e Saude",
    "beleza e saud": "Beleza e Saude",
    "brinquedos": "Brinquedos",
    "brinquedo": "Brinquedos",
    "esporte": "Esporte",
    "esportes": "Esporte",
}

# `DELIVERED`, `canceled` e `returned` aparecem misturados ao português:
# o dump junta sistemas diferentes.
STATUS = {
    "entregue": "entregue",
    "delivered": "entregue",
    "cancelado": "cancelado",
    "canceled": "cancelado",
    "devolvido": "devolvido",
    "returned": "devolvido",
}

CANAIS = {
    "app": "app",
    "site": "site",
    "marketplace_parceiro": "marketplace_parceiro",
}

# Estados por extenso convivem com a sigla.
ESTADOS = {
    "amazonas": "AM", "bahia": "BA", "ceara": "CE", "distrito federal": "DF",
    "minas gerais": "MG", "para": "PA", "pernambuco": "PE", "parana": "PR",
    "rio de janeiro": "RJ", "rio grande do sul": "RS", "sao paulo": "SP",
    "santa catarina": "SC", "goias": "GO", "espirito santo": "ES",
    "maranhao": "MA", "paraiba": "PB", "rio grande do norte": "RN",
    "alagoas": "AL", "sergipe": "SE", "piaui": "PI", "mato grosso": "MT",
    "mato grosso do sul": "MS", "tocantins": "TO", "rondonia": "RO",
    "acre": "AC", "amapa": "AP", "roraima": "RR",
}


def limpar_texto(coluna):
    """Tira espaço das pontas e converte os marcadores de nulo em NULL."""
    enxuto = F.trim(F.col(coluna))
    return F.when(enxuto.isin(MARCADORES_NULOS), None).otherwise(enxuto)


def chave(coluna):
    """Forma comparável: minúscula, sem acento, sem espaço nas pontas."""
    sem_acento = F.translate(
        F.lower(F.trim(F.col(coluna))),
        "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
        "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
    )
    return sem_acento


def para_decimal(coluna):
    """
    Converte dinheiro em três formatos para número.

    O arquivo tem `R$ 49,24`, `49.24` e `49,24` na MESMA coluna — 2.964,
    6.001 e 934 linhas em `preco_unitario`. A ordem importa: tirar o
    separador de milhar antes de trocar a vírgula decimal, senão
    `1.647,40` vira `1.64740`.
    """
    sem_moeda = F.regexp_replace(F.col(coluna), r"R\$\s*", "")
    sem_espaco = F.trim(sem_moeda)

    # Com vírgula E ponto, o ponto é milhar: 1.647,40
    milhar_e_decimal = F.regexp_replace(
        F.regexp_replace(sem_espaco, r"\.", ""), ",", "."
    )
    # Só com vírgula, ela é o decimal: 49,24
    so_decimal = F.regexp_replace(sem_espaco, ",", ".")

    valor = (
        F.when(sem_espaco.rlike(r"^-?[\d.]+,\d+$"), milhar_e_decimal)
        .when(sem_espaco.contains(","), so_decimal)
        .otherwise(sem_espaco)
    )
    return valor.cast(DecimalType(12, 2))


def para_data(coluna):
    """
    Converte data em três formatos, mais lixo.

    O arquivo traz ISO (`2025-03-07`), brasileiro (`02/03/2025`),
    timestamp (`2025-11-18 00:00:00`) e a palavra `ontem`. O `coalesce`
    tenta na ordem e devolve NULL quando nenhum formato serve — `ontem`
    cai aqui, porque não há data de referência para resolvê-lo e
    inventar uma seria fabricar fato.
    """
    texto = F.trim(F.col(coluna))
    return F.coalesce(
        F.to_date(texto, "yyyy-MM-dd"),
        F.to_date(texto, "dd/MM/yyyy"),
        F.to_date(texto, "dd-MM-yyyy"),
        F.to_date(F.substring(texto, 1, 10), "yyyy-MM-dd"),
    )


def mapear(coluna, dicionario, padrao=None):
    """Traduz para o valor canônico; o que não está no mapa vira `padrao`."""
    expressao = F.lit(padrao)
    for origem, destino in dicionario.items():
        expressao = F.when(chave(coluna) == origem, F.lit(destino)).otherwise(expressao)
    return expressao


def construir_silver(bruto):
    """
    Aplica tipagem, padronização e deduplicação.

    Devolve (silver, quarentena): as linhas aproveitáveis e as que não
    puderam virar fato, com o motivo.
    """
    tipado = (
        bruto
        .withColumn("pedido_id", limpar_texto("pedido_id"))
        .withColumn("item_id", limpar_texto("item_id"))
        .withColumn("cliente_id", limpar_texto("cliente_id"))
        .withColumn("data_pedido", para_data("data_pedido"))
        .withColumn("data_entrega", para_data("data_entrega"))
        .withColumn("cliente_data_cadastro", para_data("cliente_data_cadastro"))
        .withColumn("categoria", mapear("categoria", CATEGORIAS))
        .withColumn("status_pedido", mapear("status_pedido", STATUS))
        .withColumn("canal", mapear("canal", CANAIS))
        .withColumn(
            "estado",
            F.coalesce(mapear("estado", ESTADOS), F.upper(F.trim(F.col("estado")))),
        )
        .withColumn("cidade", limpar_texto("cidade"))
        .withColumn("custo_unitario", para_decimal("custo_unitario"))
        .withColumn("preco_unitario", para_decimal("preco_unitario"))
        .withColumn("valor_total", para_decimal("valor_total"))
        .withColumn("quantidade", limpar_texto("quantidade").cast(IntegerType()))
        .withColumn("parcelas", limpar_texto("parcelas").cast(IntegerType()))
        .withColumn("prazo_estimado_dias", limpar_texto("prazo_estimado_dias").cast(IntegerType()))
        .withColumn("prazo_real_dias", limpar_texto("prazo_real_dias").cast(IntegerType()))
        .withColumn("atraso_dias", limpar_texto("atraso_dias").cast(IntegerType()))
        # `desconto_pct` vem como `10%` em 2.932 linhas e como `10` nas
        # demais. O `%` tem de sair ANTES do cast, senão vira NULL.
        .withColumn(
            "desconto_pct",
            F.regexp_replace(F.coalesce(limpar_texto("desconto_pct"), F.lit("0")), "%", "")
            .cast(DecimalType(5, 2)),
        )
        .withColumn("nota_avaliacao", limpar_texto("nota_avaliacao").cast(IntegerType()))
        .withColumn("comentario", limpar_texto("comentario"))
    )

    # Nota fora de 1..5 (57 linhas: há -1 e 99) vira NULL em vez de
    # derrubar a linha inteira: o pedido continua válido, só a avaliação
    # não serve. Zerar seria pior — entraria na média como nota baixa.
    valido = tipado.withColumn(
        "nota_avaliacao",
        F.when(F.col("nota_avaliacao").between(1, 5), F.col("nota_avaliacao")),
    )

    # LGPD: nome, e-mail e CPF não entram na silver. O que a análise
    # precisa é distinguir clientes, e `cliente_id` já faz isso. O CPF
    # vira hash para permitir contagem de distintos sem guardar o dado
    # pessoal; nome e e-mail são simplesmente descartados.
    anonimo = (
        valido
        .withColumn("cliente_hash", F.sha2(F.coalesce(F.col("cliente_cpf"), F.lit("")), 256))
        .drop("cliente_nome", "cliente_email", "cliente_cpf")
    )

    # Quarentena: o que não pode virar fato.
    motivo = (
        F.when(F.col("item_id").isNull(), "item_id ausente")
        .when(F.col("pedido_id").isNull(), "pedido_id ausente")
        .when(F.col("data_pedido").isNull(), "data_pedido ilegivel")
        .when(F.col("quantidade").isNull(), "quantidade ausente")
        .when(F.col("quantidade") <= 0, "quantidade nao positiva")
        .when(F.col("valor_total").isNull(), "valor_total ausente")
        .when(F.col("valor_total") < 0, "valor_total negativo")
        .when(F.col("categoria").isNull(), "categoria fora do dominio")
        .when(F.col("status_pedido").isNull(), "status fora do dominio")
    )

    marcado = anonimo.withColumn("motivo_quarentena", motivo)

    quarentena = marcado.filter(F.col("motivo_quarentena").isNotNull())
    aproveitavel = marcado.filter(F.col("motivo_quarentena").isNull()).drop("motivo_quarentena")

    # Deduplicação por `item_id`: 200 ids repetidos, 200 linhas extras.
    # `row_number` em vez de `dropDuplicates` porque a escolha de QUAL
    # cópia fica precisa ser determinística — com `dropDuplicates` o
    # Spark fica com uma qualquer, e duas execuções podem divergir.
    # Critério: a linha mais completa (menos nulos nas colunas que
    # importam) e, no empate, a de entrega mais recente.
    completude = (
        F.col("data_entrega").isNotNull().cast("int")
        + F.col("nota_avaliacao").isNotNull().cast("int")
        + F.col("atraso_dias").isNotNull().cast("int")
    )

    janela = Window.partitionBy("item_id").orderBy(
        completude.desc(), F.col("data_entrega").desc_nulls_last()
    )

    silver = (
        aproveitavel
        .withColumn("ordem", F.row_number().over(janela))
        .filter(F.col("ordem") == 1)
        .drop("ordem")
        # `atraso_dias` ausente mas com os dois prazos presentes é
        # recalculável. Recalcular é melhor que guardar NULL: a coluna
        # é derivada, não observada.
        .withColumn(
            "atraso_dias",
            F.coalesce(
                F.col("atraso_dias"),
                F.col("prazo_real_dias") - F.col("prazo_estimado_dias"),
            ),
        )
        .withColumn("atrasou", F.col("atraso_dias") > 0)
        .withColumn("ano_mes", F.date_format(F.col("data_pedido"), "yyyy-MM"))
    )

    return silver, quarentena


def construir_gold(silver):
    """
    Duas tabelas de negócio, cada uma para uma pergunta do cenário.

    Só pedidos `entregue` entram nas métricas de prazo: cancelado e
    devolvido não têm entrega, e incluí-los puxaria a média de atraso
    para baixo com linhas que nunca saíram do centro de distribuição.
    """
    entregues = silver.filter(F.col("status_pedido") == "entregue")

    # "Quais fatores explicam o atraso, e qual a relação entre atraso e
    # nota?" — por estado, categoria e mês.
    atraso_por_recorte = (
        entregues.groupBy("estado", "categoria", "ano_mes")
        .agg(
            F.count("*").alias("itens_entregues"),
            F.sum(F.col("atrasou").cast("int")).alias("itens_atrasados"),
            F.round(F.avg("atraso_dias"), 2).alias("atraso_medio_dias"),
            F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
            F.sum("valor_total").alias("receita"),
        )
        .withColumn(
            "taxa_atraso_pct",
            F.round(100 * F.col("itens_atrasados") / F.col("itens_entregues"), 2),
        )
    )

    # "Quais categorias, canais e estados têm mais cancelamento e
    # devolução?"
    desfecho_por_canal = (
        silver.groupBy("canal", "categoria", "estado")
        .agg(
            F.count("*").alias("itens"),
            F.sum((F.col("status_pedido") == "cancelado").cast("int")).alias("cancelados"),
            F.sum((F.col("status_pedido") == "devolvido").cast("int")).alias("devolvidos"),
            F.sum("valor_total").alias("valor_total"),
        )
        .withColumn(
            "taxa_cancelamento_pct",
            F.round(100 * F.col("cancelados") / F.col("itens"), 2),
        )
        .withColumn(
            "taxa_devolucao_pct",
            F.round(100 * F.col("devolvidos") / F.col("itens"), 2),
        )
    )

    return atraso_por_recorte, desfecho_por_canal


def main():
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "entrada_raw", "saida_silver", "saida_gold", "saida_quarentena"],
    )

    sc = SparkContext()
    glue = GlueContext(sc)
    spark = glue.spark_session
    job = Job(glue)
    job.init(args["JOB_NAME"], args)

    # `inferSchema` fica DESLIGADO de propósito. Toda coluna chega como
    # texto, e deixar o Spark adivinhar tipo num arquivo onde preço vem
    # como `R$ 49,24` produziria string em umas partições e número em
    # outras, conforme o que coube na amostra de inferência.
    bruto = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .option("encoding", "UTF-8")
        .option("multiLine", "true")
        .option("escape", '"')
        .csv(args["entrada_raw"])
    )

    silver, quarentena = construir_silver(bruto)

    # `overwrite` porque a escrita do Spark no S3 DUPLICA quando o
    # prefixo já tem dado de uma execução anterior.
    silver.write.mode("overwrite").partitionBy("ano_mes").parquet(args["saida_silver"])
    quarentena.write.mode("overwrite").parquet(args["saida_quarentena"])

    atraso, desfecho = construir_gold(silver)
    atraso.write.mode("overwrite").parquet(args["saida_gold"].rstrip("/") + "/atraso_por_recorte/")
    desfecho.write.mode("overwrite").parquet(args["saida_gold"].rstrip("/") + "/desfecho_por_canal/")

    # Contagens no log do CloudWatch: é como se confere, depois do run,
    # quanto foi para quarentena sem abrir o Athena.
    print(f"silver: {silver.count()} linhas")
    print(f"quarentena: {quarentena.count()} linhas")

    job.commit()


if __name__ == "__main__":
    main()
