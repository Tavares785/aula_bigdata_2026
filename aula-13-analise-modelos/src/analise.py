"""
Aula 13 - Analise e Construcao de Modelos em Larga Escala
Etapa do projeto: implemente aqui a analise, o modelo de Machine
Learning ou o pipeline de NLP do seu grupo, usando os dados ja
pre-processados na Aula 12.

Assim como no arquivo da Aula 12, o CI verifica apenas se as funcoes
abaixo foram implementadas (estrutura), nao se os RESULTADOS estao
corretos -- isso depende do dataset e do problema escolhidos pelo seu
grupo, e e avaliado pelo professor na revisao da PR.

-------------------------------------------------------------------------
Projeto MercadoFacil (RA 6325226)

Entrada: a camada silver gerada na Aula 12 (`silver/pedidos_itens`,
Parquet, 1 linha = 1 item de pedido, sem PII). A analise roda em Spark
3.3 (mesma versao do Glue 4.0), localmente ou como Glue Job:

    python src/analise.py --SILVER_PATH <.../silver/pedidos_itens> \
                          --OUTPUT_PATH <pasta de saida>

Quatro analises respondem a pergunta "por que os pedidos atrasam e
quanto isso custa?":

  A. Modelo de risco de atraso (Spark MLlib): regressao logistica e
     random forest, 1 linha = 1 pedido entregue, so com variaveis
     conhecidas NA HORA DA COMPRA (sem vazamento de prazo real/nota).
  B. Impacto do atraso na nota e na devolucao, controlando por
     categoria e canal (regressao linear e logistica no nivel do item).
  C. NLP dos comentarios: tema (entrega / produto / atendimento) e
     sentimento por lexico, com RegexTokenizer + StopWordsRemover.
  D. Capacidade e cenario: volume x atraso por CD/mes e simulacao do
     efeito de aumentar o prazo estimado no Norte/Nordeste.
"""
import argparse
import json
import os
import sys

from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import (
    OneHotEncoder,
    RegexTokenizer,
    StopWordsRemover,
    StringIndexer,
    VectorAssembler,
)
from pyspark.ml.regression import LinearRegression
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

SEED = 42
K_FOLDS = 5

# Variaveis do modelo de atraso: todas conhecidas no momento da compra.
CAT_FEATURES = [
    "regiao", "centro_distribuicao", "transportadora", "canal",
    "categoria_principal", "forma_pagamento", "cliente_segmento", "mes",
]
NUM_FEATURES = ["prazo_estimado_dias", "itens", "valor_pedido"]

# Lexicos do NLP (tokens ja em minusculas e sem acento).
TEMAS = {
    "entrega": ["entrega", "atrasou", "atrasada", "demorou", "prazo", "chegou", "rapida"],
    "produto": ["produto", "qualidade", "defeito", "quebrado", "embalagem",
                "embalado", "danificada", "diferente", "anunciado"],
    "atendimento": ["atendimento", "satisfacao", "resolveu", "reembolso"],
}
POSITIVAS = ["adorei", "excelente", "recomendo", "otimo", "rapida", "perfeitamente",
             "bom", "acima", "voltarei", "atendeu", "cumpre", "antes"]
NEGATIVAS = ["pessimo", "horrivel", "decepcionado", "defeito", "quebrado", "danificada",
             "ruim", "atrasou", "atrasada", "demorou", "reembolso", "ninguem"]
# "nao recomendo" inverte o sentido de "recomendo": tratado como token unico.
NEGACOES = {"nao recomendo": "nao_recomendo"}
NEGATIVAS.append("nao_recomendo")

ACENTOS = "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
SEM_ACENTOS = "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC"


# =============================================================================
# Preparacao dos dados
# =============================================================================
def pedidos_entregues(silver: DataFrame) -> DataFrame:
    """1 linha = 1 pedido com entrega conhecida (cancelados ficam de fora).
    A logistica e do pedido; a categoria principal e a de maior valor."""
    w = Window.partitionBy("pedido_id").orderBy(F.desc("valor_total"), F.asc("item_id"))
    principal = (
        silver.withColumn("_rn", F.row_number().over(w))
        .where("_rn = 1")
        .select("pedido_id", F.col("categoria").alias("categoria_principal"))
    )
    pedidos = (
        silver.where(F.col("atraso_dias").isNotNull())
        .groupBy("pedido_id")
        .agg(
            F.first("data_pedido").alias("data_pedido"),
            F.first("regiao").alias("regiao"),
            F.first("estado").alias("estado"),
            F.first("centro_distribuicao", ignorenulls=True).alias("centro_distribuicao"),
            F.first("transportadora", ignorenulls=True).alias("transportadora"),
            F.first("canal", ignorenulls=True).alias("canal"),
            F.first("forma_pagamento", ignorenulls=True).alias("forma_pagamento"),
            F.first("cliente_segmento").alias("cliente_segmento"),
            F.max("prazo_estimado_dias").alias("prazo_estimado_dias"),
            F.max("prazo_real_dias").alias("prazo_real_dias"),
            F.max("atraso_dias").alias("atraso_dias"),
            F.count("*").alias("itens"),
            F.sum("valor_total").alias("valor_pedido"),
        )
        .join(principal, "pedido_id", "left")
        .withColumn("mes", F.format_string("%02d", F.month("data_pedido")))
        .withColumn("label", (F.col("atraso_dias") > 0).cast("double"))
    )
    # Pesos de classe: o atraso e a classe minoritaria (~22%).
    pos = pedidos.agg(F.avg("label")).first()[0]
    return pedidos.withColumn(
        "peso", F.when(F.col("label") == 1, 0.5 / pos).otherwise(0.5 / (1 - pos))
    )


def feature_stages(cat_cols, num_cols, prefix=""):
    """StringIndexer + OneHotEncoder + VectorAssembler.
    handleInvalid='keep' cria um balde para categorias novas/nulas."""
    idx = [
        StringIndexer(inputCol=c, outputCol=f"{prefix}{c}_idx", handleInvalid="keep")
        for c in cat_cols
    ]
    ohe = OneHotEncoder(
        inputCols=[f"{prefix}{c}_idx" for c in cat_cols],
        outputCols=[f"{prefix}{c}_ohe" for c in cat_cols],
        handleInvalid="keep",
    )
    asm = VectorAssembler(
        inputCols=[f"{prefix}{c}_ohe" for c in cat_cols] + num_cols,
        outputCol="features",
        handleInvalid="keep",
    )
    return idx + [ohe, asm]


def feature_names(df: DataFrame, col="features"):
    """Nome de cada posicao do vetor (ex.: 'regiao_ohe_Nordeste')."""
    attrs = df.schema[col].metadata["ml_attr"]["attrs"]
    names = {}
    for group in attrs.values():
        for a in group:
            names[a["idx"]] = a["name"]
    return [names[i] for i in range(len(names))]


def variavel_de(nome):
    """'regiao_ohe_Nordeste' -> ('regiao', 'Nordeste'); numericas sem nivel."""
    if "_ohe_" in nome:
        var, nivel = nome.split("_ohe_", 1)
        return var, nivel
    return nome, None


# =============================================================================
# A. Modelo de risco de atraso
# =============================================================================
def metricas_binarias(pred: DataFrame):
    auc_roc = BinaryClassificationEvaluator(metricName="areaUnderROC").evaluate(pred)
    auc_pr = BinaryClassificationEvaluator(metricName="areaUnderPR").evaluate(pred)
    m = pred.agg(
        F.sum(((F.col("prediction") == 1) & (F.col("label") == 1)).cast("int")).alias("tp"),
        F.sum(((F.col("prediction") == 1) & (F.col("label") == 0)).cast("int")).alias("fp"),
        F.sum(((F.col("prediction") == 0) & (F.col("label") == 1)).cast("int")).alias("fn"),
        F.sum(((F.col("prediction") == 0) & (F.col("label") == 0)).cast("int")).alias("tn"),
    ).first()
    tp, fp, fn, tn = m["tp"], m["fp"], m["fn"], m["tn"]
    precisao = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
    return {
        "auc_roc": round(auc_roc, 4),
        "auc_pr": round(auc_pr, 4),
        "acuracia": round((tp + tn) / (tp + fp + fn + tn), 4),
        "precisao_atraso": round(precisao, 4),
        "recall_atraso": round(recall, 4),
        "f1_atraso": round(f1, 4),
        "matriz_confusao": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def top_k_lift(pred: DataFrame, frac=0.2):
    """Dos 20% de pedidos com maior risco previsto, quantos atrasaram?"""
    from pyspark.ml.functions import vector_to_array

    scored = pred.withColumn("_p", vector_to_array("probability")[1])
    n = scored.count()
    k = max(1, int(n * frac))
    taxa_top = scored.orderBy(F.desc("_p")).limit(k).agg(F.avg("label")).first()[0]
    taxa_base = scored.agg(F.avg("label")).first()[0]
    return {
        "fracao": frac,
        "taxa_atraso_top": round(taxa_top, 4),
        "taxa_atraso_geral": round(taxa_base, 4),
        "lift": round(taxa_top / taxa_base, 2),
    }


def validacao_cruzada(pedidos: DataFrame, est):
    """AUC-ROC em K folds (cada fold e teste uma vez): media, desvio e valores."""
    import statistics

    ev = BinaryClassificationEvaluator(metricName="areaUnderROC")
    aucs = []
    for k in range(K_FOLDS):
        pipe = Pipeline(stages=feature_stages(CAT_FEATURES, NUM_FEATURES) + [est])
        modelo = pipe.fit(pedidos.where(F.col("fold") != k))
        aucs.append(ev.evaluate(modelo.transform(pedidos.where(F.col("fold") == k))))
    return {
        "media": round(statistics.mean(aucs), 4),
        "desvio": round(statistics.stdev(aucs), 4),
        "folds": [round(a, 4) for a in aucs],
    }


def modelo_atraso(silver: DataFrame):
    # Fold deterministico pelo hash do pedido_id: randomSplit depende da
    # ordem das linhas depois do shuffle e mudava o teste a cada execucao.
    pedidos = pedidos_entregues(silver).withColumn(
        "fold", F.expr(f"pmod(xxhash64(pedido_id), {K_FOLDS})")
    ).cache()
    treino = pedidos.where(F.col("fold") != 0).cache()
    teste = pedidos.where(F.col("fold") == 0).cache()

    lr = LogisticRegression(
        featuresCol="features", labelCol="label", weightCol="peso",
        regParam=0.01, elasticNetParam=0.0, maxIter=100,
    )
    rf = RandomForestClassifier(
        featuresCol="features", labelCol="label", weightCol="peso",
        numTrees=60, maxDepth=6, minInstancesPerNode=10, seed=SEED,
    )
    modelos, metricas, previsoes = {}, {}, {}
    for nome, est in [("regressao_logistica", lr), ("random_forest", rf)]:
        pipe = Pipeline(stages=feature_stages(CAT_FEATURES, NUM_FEATURES) + [est])
        modelo = pipe.fit(treino)
        pred = modelo.transform(teste).cache()
        metricas[nome] = metricas_binarias(pred)
        metricas[nome]["top20"] = top_k_lift(pred)
        modelos[nome], previsoes[nome] = modelo, pred
        metricas[nome]["cv_auc_roc"] = validacao_cruzada(pedidos, est)

    # Baseline ingenuo: "nunca atrasa" (classe majoritaria).
    taxa_teste = teste.agg(F.avg("label")).first()[0]
    metricas["baseline_nunca_atrasa"] = {
        "auc_roc": 0.5,
        "acuracia": round(1 - taxa_teste, 4),
        "recall_atraso": 0.0,
    }

    nomes = feature_names(previsoes["random_forest"])

    # Importancia do RF somada por variavel original.
    imp = modelos["random_forest"].stages[-1].featureImportances.toArray()
    por_var = {}
    for nome, v in zip(nomes, imp):
        var, _ = variavel_de(nome)
        por_var[var] = por_var.get(var, 0.0) + float(v)
    importancia = sorted(
        ({"variavel": k, "importancia": round(v, 4)} for k, v in por_var.items()),
        key=lambda d: -d["importancia"],
    )

    # Odds ratio da regressao logistica por nivel (exp do coeficiente).
    import math

    coefs = modelos["regressao_logistica"].stages[-1].coefficients.toArray()
    odds = [
        {"variavel": variavel_de(n)[0], "nivel": variavel_de(n)[1], "odds_ratio": round(math.exp(c), 3)}
        for n, c in zip(nomes, coefs)
        if variavel_de(n)[1] not in (None, "__unknown")
    ]
    odds_num = [
        {"variavel": n, "odds_ratio_por_unidade": round(math.exp(c), 4)}
        for n, c in zip(nomes, coefs)
        if variavel_de(n)[1] is None
    ]
    odds.sort(key=lambda d: -d["odds_ratio"])

    return {
        "pedidos_modelados": pedidos.count(),
        "treino": treino.count(),
        "teste": teste.count(),
        "taxa_atraso_teste": round(taxa_teste, 4),
        "metricas": metricas,
        "importancia_rf": importancia,
        "odds_ratio_lr_maiores": odds[:8],
        "odds_ratio_lr_menores": odds[-5:],
        "odds_ratio_lr_numericas": odds_num,
        "_modelos": modelos,
        "_previsoes": previsoes,
    }


# =============================================================================
# B. Impacto do atraso na nota e na devolucao (nivel do item)
# =============================================================================
def impacto_atraso(silver: DataFrame):
    base = silver.where(F.col("atraso_dias").isNotNull()).withColumn(
        "atraso_dias_d", F.col("atraso_dias").cast("double")
    )
    controles = ["categoria", "canal"]

    # Nota (1..5) ~ atraso_dias + categoria + canal
    avaliados = base.where(F.col("nota_avaliacao").isNotNull()).withColumn(
        "nota", F.col("nota_avaliacao").cast("double")
    )
    pipe_nota = Pipeline(
        stages=feature_stages(controles, ["atraso_dias_d"], prefix="n_")
        + [LinearRegression(featuresCol="features", labelCol="nota", regParam=0.0)]
    )
    m_nota = pipe_nota.fit(avaliados)
    nomes = feature_names(m_nota.transform(avaliados.limit(1)))
    lin = m_nota.stages[-1]
    coef_atraso = float(lin.coefficients[nomes.index("atraso_dias_d")])

    # Devolucao ~ atraso_dias + categoria + canal (sem pesos: interesse e o coeficiente)
    dev = base.withColumn("label", (F.col("status_pedido") == "devolvido").cast("double"))
    pipe_dev = Pipeline(
        stages=feature_stages(controles, ["atraso_dias_d"], prefix="d_")
        + [LogisticRegression(featuresCol="features", labelCol="label", regParam=0.0, maxIter=100)]
    )
    m_dev = pipe_dev.fit(dev)
    nomes_d = feature_names(m_dev.transform(dev.limit(1)))
    coef_dev = float(m_dev.stages[-1].coefficients[nomes_d.index("atraso_dias_d")])

    import math

    por_faixa = (
        avaliados.withColumn(
            "faixa",
            F.when(F.col("atraso_dias") == 0, "0 no prazo")
            .when(F.col("atraso_dias") <= 3, "1-3 dias")
            .when(F.col("atraso_dias") <= 7, "4-7 dias")
            .otherwise("8+ dias"),
        )
        .groupBy("faixa")
        .agg(F.count("*").alias("itens"), F.round(F.avg("nota"), 2).alias("nota_media"))
        .orderBy("faixa")
    )
    return {
        "itens_avaliados": avaliados.count(),
        "nota_pontos_por_dia_de_atraso": round(coef_atraso, 4),
        "nota_r2": round(lin.summary.r2, 4),
        "devolucao_odds_ratio_por_dia": round(math.exp(coef_dev), 4),
        "nota_por_faixa": [r.asDict() for r in por_faixa.collect()],
    }


# =============================================================================
# C. NLP dos comentarios
# =============================================================================
def nlp_comentarios(silver: DataFrame):
    txt = F.lower(F.translate(F.col("comentario"), ACENTOS, SEM_ACENTOS))
    for frase, token in NEGACOES.items():
        txt = F.regexp_replace(txt, frase, token)
    base = silver.where(F.col("comentario").isNotNull()).withColumn("texto", txt)

    tok = RegexTokenizer(inputCol="texto", outputCol="tokens_brutos", pattern=r"[^a-z_]+")
    sw = StopWordsRemover(
        inputCol="tokens_brutos", outputCol="tokens",
        stopWords=StopWordsRemover.loadDefaultStopWords("portuguese") + ["e", "a", "o"],
    )
    df = Pipeline(stages=[tok, sw]).fit(base).transform(base)

    def conta(lista):
        arr = F.array(*[F.lit(t) for t in lista])
        return F.size(F.array_intersect(F.col("tokens"), arr))

    df = df.withColumn("score", conta(POSITIVAS) - conta(NEGATIVAS)).withColumn(
        "sentimento",
        F.when(F.col("score") > 0, "positivo").when(F.col("score") < 0, "negativo").otherwise("neutro"),
    )
    for tema, palavras in TEMAS.items():
        df = df.withColumn(f"tema_{tema}", conta(palavras) > 0)

    # Validacao do lexico contra a nota dada pelo proprio cliente.
    validacao = (
        df.where(F.col("nota_avaliacao").isNotNull())
        .groupBy("sentimento")
        .agg(F.count("*").alias("comentarios"), F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"))
        .orderBy("sentimento")
    )
    neg = df.where(F.col("sentimento") == "negativo")
    temas_neg = neg.agg(
        F.count("*").alias("negativos"),
        *[F.sum(F.col(f"tema_{t}").cast("int")).alias(t) for t in TEMAS],
    ).first().asDict()

    # Reclamacao de entrega x atraso real: o cliente reclama do que aconteceu?
    reclama = (
        neg.where(F.col("atraso_dias").isNotNull())
        .groupBy(F.col("entregue_com_atraso").alias("atrasou"))
        .agg(
            F.count("*").alias("negativos"),
            F.round(100 * F.avg(F.col("tema_entrega").cast("int")), 1).alias("pct_cita_entrega"),
        )
        .orderBy("atrasou")
    )
    top_tokens = (
        df.select(F.explode("tokens").alias("token"))
        .groupBy("token").count().orderBy(F.desc("count"), "token").limit(10)
    )
    return {
        "comentarios": df.count(),
        "sentimento_x_nota": [r.asDict() for r in validacao.collect()],
        "temas_nos_negativos": temas_neg,
        "negativos_entrega_x_atraso": [r.asDict() for r in reclama.collect()],
        "top_tokens": [(r["token"], r["count"]) for r in top_tokens.collect()],
    }


# =============================================================================
# D. Capacidade (volume x atraso) e cenario de prazo
# =============================================================================
def capacidade_e_cenario(silver: DataFrame, dias_extra=2):
    pedidos = pedidos_entregues(silver)
    cd_mes = pedidos.groupBy("centro_distribuicao", "mes").agg(
        F.count("*").alias("pedidos"), F.avg("label").alias("taxa_atraso")
    )
    correl = (
        cd_mes.groupBy("centro_distribuicao")
        .agg(F.round(F.corr("pedidos", "taxa_atraso"), 3).alias("corr_volume_atraso"))
        .orderBy("centro_distribuicao")
    )
    correl_geral = cd_mes.agg(F.corr("pedidos", "taxa_atraso")).first()[0]

    # Cenario: +N dias no prazo PROMETIDO para Norte/Nordeste. O prazo real
    # nao muda; muda a promessa (o que o cliente percebe como atraso).
    alvo = F.col("regiao").isin("Norte", "Nordeste")
    novo_prazo = F.when(alvo, F.col("prazo_estimado_dias") + dias_extra).otherwise(F.col("prazo_estimado_dias"))
    sim = pedidos.withColumn(
        "atrasa_cenario", (F.col("prazo_real_dias") > novo_prazo).cast("double")
    )
    por_regiao = (
        sim.groupBy("regiao")
        .agg(
            F.count("*").alias("pedidos"),
            F.round(100 * F.avg("label"), 1).alias("pct_atraso_atual"),
            F.round(100 * F.avg("atrasa_cenario"), 1).alias("pct_atraso_cenario"),
        )
        .orderBy("regiao")
    )
    tot = sim.agg(
        F.round(100 * F.avg("label"), 1).alias("atual"),
        F.round(100 * F.avg("atrasa_cenario"), 1).alias("cenario"),
    ).first()
    return {
        "corr_volume_atraso_por_cd": [r.asDict() for r in correl.collect()],
        "corr_volume_atraso_geral": round(correl_geral, 3),
        "cenario_dias_extra_norte_nordeste": dias_extra,
        "cenario_por_regiao": [r.asDict() for r in por_regiao.collect()],
        "pct_atraso_total_atual": tot["atual"],
        "pct_atraso_total_cenario": tot["cenario"],
    }


# =============================================================================
# Funcoes exigidas pelo CI
# =============================================================================
def build_model_or_analysis(preprocessed_data):
    """
    Implemente aqui a analise principal do seu projeto: pode ser o
    treinamento de um modelo de classificacao/clustering/regressao com
    Spark MLlib, um pipeline de NLP (analise de sentimento, topicos),
    ou outra tecnica de analise de dados em larga escala vista no
    curso.

    Retorne o resultado da analise (ex: um modelo treinado, um
    DataFrame com os resultados, etc.) -- o formato fica a criterio do
    seu grupo, desde que `summarize_results` (abaixo) saiba lidar com
    ele.

    MercadoFacil: `preprocessed_data` e o DataFrame Spark da silver
    `pedidos_itens` (Aula 12). Retorna um dicionario com as quatro
    analises (A-D); as chaves que comecam com '_' guardam os modelos
    treinados e as previsoes (objetos Spark).
    """
    silver = preprocessed_data.cache()
    return {
        "linhas_silver": silver.count(),
        "modelo_atraso": modelo_atraso(silver),
        "impacto_atraso": impacto_atraso(silver),
        "nlp_comentarios": nlp_comentarios(silver),
        "capacidade_cenario": capacidade_e_cenario(silver),
    }


def _sem_objetos_spark(d):
    if isinstance(d, dict):
        return {k: _sem_objetos_spark(v) for k, v in d.items() if not str(k).startswith("_")}
    if isinstance(d, (list, tuple)):
        return [_sem_objetos_spark(v) for v in d]
    return d


def summarize_results(analysis_output):
    """
    Receba o resultado de `build_model_or_analysis` e produza um
    resumo dos resultados (ex: metricas do modelo, principais insights
    encontrados, tabela de topicos mais frequentes, etc.) em um formato
    legivel -- pode ser uma string, um dicionario ou um DataFrame
    pequeno com os resultados finais.

    MercadoFacil: retorna {"resultados": <dict serializavel em JSON>,
    "texto": <resumo em texto>}.
    """
    r = _sem_objetos_spark(analysis_output)
    a, b, c, d = (r["modelo_atraso"], r["impacto_atraso"], r["nlp_comentarios"], r["capacidade_cenario"])
    lr, rf = a["metricas"]["regressao_logistica"], a["metricas"]["random_forest"]

    linhas = [
        "== MercadoFacil - Aula 13 ==",
        f"Silver: {r['linhas_silver']} itens | pedidos entregues modelados: {a['pedidos_modelados']} "
        f"(treino {a['treino']}, teste {a['teste']}, atraso no teste {100 * a['taxa_atraso_teste']:.1f}%)",
        "",
        "[A] Risco de atraso (teste)",
        f"  modelo              AUC-ROC  AUC-PR  acur.  prec.  recall  F1    top20%",
    ]
    for nome, m in [("regressao_logistica", lr), ("random_forest", rf)]:
        linhas.append(
            f"  {nome:<19} {m['auc_roc']:.3f}    {m['auc_pr']:.3f}   {m['acuracia']:.3f}  "
            f"{m['precisao_atraso']:.3f}  {m['recall_atraso']:.3f}   {m['f1_atraso']:.3f} "
            f"{100 * m['top20']['taxa_atraso_top']:.1f}% (lift {m['top20']['lift']})"
        )
        cv = m["cv_auc_roc"]
        linhas.append(f"  {'':<19} matriz: {m['matriz_confusao']}")
        linhas.append(f"  {'':<19} AUC-ROC {len(cv['folds'])}-fold: {cv['media']:.3f} +/- {cv['desvio']:.3f} {cv['folds']}")
    bl = a["metricas"]["baseline_nunca_atrasa"]
    linhas.append(f"  baseline 'nunca atrasa': acuracia {bl['acuracia']:.3f}, recall 0")
    linhas.append("  importancia RF: " + ", ".join(f"{x['variavel']}={x['importancia']:.3f}" for x in a["importancia_rf"]))
    linhas.append("  maiores odds ratio (LR): " + ", ".join(
        f"{x['variavel']}={x['nivel']}:{x['odds_ratio']}" for x in a["odds_ratio_lr_maiores"]))
    linhas.append("  numericas (LR, por unidade): " + ", ".join(
        f"{x['variavel']}:{x['odds_ratio_por_unidade']}" for x in a["odds_ratio_lr_numericas"]))
    linhas += [
        "",
        "[B] Impacto do atraso (controlando categoria e canal)",
        f"  nota: {b['nota_pontos_por_dia_de_atraso']:+.3f} ponto por dia de atraso (R2={b['nota_r2']}, "
        f"{b['itens_avaliados']} itens avaliados)",
        f"  devolucao: odds ratio {b['devolucao_odds_ratio_por_dia']} por dia de atraso",
        "  nota por faixa: " + ", ".join(f"{x['faixa']}={x['nota_media']} (n={x['itens']})" for x in b["nota_por_faixa"]),
        "",
        "[C] NLP dos comentarios",
        f"  {c['comentarios']} comentarios; sentimento x nota: " + ", ".join(
            f"{x['sentimento']}={x['nota_media']} (n={x['comentarios']})" for x in c["sentimento_x_nota"]),
        f"  temas nos negativos: {c['temas_nos_negativos']}",
        "  negativos que citam entrega: " + ", ".join(
            f"atrasou={x['atrasou']}: {x['pct_cita_entrega']}% de {x['negativos']}" for x in c["negativos_entrega_x_atraso"]),
        f"  top tokens: {c['top_tokens']}",
        "",
        "[D] Capacidade e cenario",
        f"  corr(volume, taxa de atraso) por CD/mes: geral {d['corr_volume_atraso_geral']}; " + ", ".join(
            f"{x['centro_distribuicao']}={x['corr_volume_atraso']}" for x in d["corr_volume_atraso_por_cd"]),
        f"  +{d['cenario_dias_extra_norte_nordeste']} dias de prazo no Norte/Nordeste: atraso total "
        f"{d['pct_atraso_total_atual']}% -> {d['pct_atraso_total_cenario']}%",
    ]
    for x in d["cenario_por_regiao"]:
        linhas.append(f"    {x['regiao']:<13} {x['pct_atraso_atual']:>5}% -> {x['pct_atraso_cenario']:>5}%  (n={x['pedidos']})")
    return {"resultados": r, "texto": "\n".join(linhas)}


# =============================================================================
# Execucao (local ou Glue)
# =============================================================================
def main(argv=None):
    p = argparse.ArgumentParser(description="Analise MercadoFacil (Aula 13)")
    p.add_argument("--SILVER_PATH", required=True, help=".../silver/pedidos_itens (Parquet)")
    p.add_argument("--OUTPUT_PATH", required=True, help="pasta local para resultados.json/.txt")
    args, _ = p.parse_known_args(argv)

    spark = (
        SparkSession.builder.appName("analise-mercadofacil")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.session.timeZone", "America/Sao_Paulo")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    saida = build_model_or_analysis(spark.read.parquet(args.SILVER_PATH))
    resumo = summarize_results(saida)
    print(resumo["texto"])

    os.makedirs(args.OUTPUT_PATH, exist_ok=True)
    with open(os.path.join(args.OUTPUT_PATH, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(resumo["resultados"], f, ensure_ascii=False, indent=2, default=str)
    with open(os.path.join(args.OUTPUT_PATH, "resultados.txt"), "w", encoding="utf-8") as f:
        f.write(resumo["texto"] + "\n")
    spark.stop()


if __name__ == "__main__":
    main(sys.argv[1:])
