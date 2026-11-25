"""
Aula 13 - Analise e Construcao de Modelos em Larga Escala

Projeto MercadoFacil: usa a camada silver gerada na Aula 12 (Parquet,
`pedidos_itens`) para:

1. Prever se uma entrega vai ATRASAR (classificacao binaria, Spark MLlib),
   usando so informacao conhecida na hora do pedido (sem vazamento: nao usa
   prazo_real_dias, atraso_dias nem a nota).
2. Medir a relacao entre atraso e nota de avaliacao.
3. Mostrar a sazonalidade do atraso por mes.

Uso local:
    python src/analise.py --silver_path <pasta>/silver/pedidos_itens
No Glue/EMR basta passar o mesmo caminho em s3://.

Os imports do Spark ficam dentro das funcoes: o CI so instala pytest e apenas
le a estrutura deste arquivo.
"""
import argparse
import json

CATEGORICAS = [
    "estado",
    "transportadora",
    "centro_distribuicao",
    "categoria",
    "canal",
    "cliente_segmento",
    "forma_pagamento",
]
NUMERICAS = [
    "prazo_estimado_dias",
    "quantidade",
    "valor_total",
    "desconto_pct",
    "mes_pedido",
]
SEED = 42


def _prepare(df):
    """Itens entregues/devolvidos com atraso conhecido; cria label e mes."""
    from pyspark.sql import functions as F

    return (
        df.where(F.col("status_pedido").isin("entregue", "devolvido"))
        .where(F.col("atrasado").isNotNull())
        .withColumn("label", F.col("atrasado").cast("double"))
        .withColumn("mes_pedido", F.month("data_pedido").cast("double"))
        .withColumn("centro_distribuicao", F.coalesce("centro_distribuicao", F.lit("nao_informado")))
        .withColumn("forma_pagamento", F.coalesce("forma_pagamento", F.lit("nao_informado")))
        .fillna({"prazo_estimado_dias": 0, "desconto_pct": 0.0})
    )


def _feature_names(predictions):
    """Nomes das colunas do vetor de features (a partir dos metadados do Spark)."""
    attrs = predictions.schema["features"].metadata["ml_attr"]["attrs"]
    ordered = sorted(
        (a for group in attrs.values() for a in group), key=lambda a: a["idx"]
    )
    return [a["name"] for a in ordered]


def build_model_or_analysis(preprocessed_data):
    """
    Recebe o DataFrame da silver (Aula 12) e devolve um dicionario com:
    modelo treinado, metricas (teste), baseline, importancia das variaveis e
    duas analises descritivas (atraso x nota e atraso por mes).
    """
    from pyspark.ml import Pipeline
    from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator
    from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
    from pyspark.sql import functions as F

    data = _prepare(preprocessed_data).cache()
    total = data.count()
    pos = data.where("label = 1").count()
    peso_pos = (total - pos) / pos  # balanceia a classe rara (atrasado)
    data = data.withColumn(
        "peso", F.when(F.col("label") == 1, F.lit(peso_pos)).otherwise(F.lit(1.0))
    )

    train, test = data.randomSplit([0.8, 0.2], seed=SEED)

    indexers = [
        StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
        for c in CATEGORICAS
    ]
    encoder = OneHotEncoder(
        inputCols=[f"{c}_idx" for c in CATEGORICAS],
        outputCols=[f"{c}_oh" for c in CATEGORICAS],
        handleInvalid="keep",
    )
    assembler = VectorAssembler(
        inputCols=[f"{c}_oh" for c in CATEGORICAS] + NUMERICAS,
        outputCol="features",
        handleInvalid="keep",
    )
    prep = [*indexers, encoder, assembler]

    rf = RandomForestClassifier(
        labelCol="label", featuresCol="features", weightCol="peso",
        numTrees=100, maxDepth=8, seed=SEED,
    )
    lr = LogisticRegression(
        labelCol="label", featuresCol="features", weightCol="peso", maxIter=50
    )
    model_rf = Pipeline(stages=[*prep, rf]).fit(train)
    model_lr = Pipeline(stages=[*prep, lr]).fit(train)

    auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")

    def avaliar(model):
        pred = model.transform(test)
        tp = pred.where("label = 1 AND prediction = 1").count()
        fp = pred.where("label = 0 AND prediction = 1").count()
        fn = pred.where("label = 1 AND prediction = 0").count()
        tn = pred.where("label = 0 AND prediction = 0").count()
        n = tp + fp + fn + tn
        precisao = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) else 0.0
        return {
            "auc": round(auc.evaluate(pred), 4),
            "acuracia": round((tp + tn) / n, 4),
            "precisao_atraso": round(precisao, 4),
            "recall_atraso": round(recall, 4),
            "f1_atraso": round(f1, 4),
            "matriz": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        }

    metricas_rf = avaliar(model_rf)
    metricas_lr = avaliar(model_lr)
    base_acc = test.where("label = 0").count() / test.count()

    pred_rf = model_rf.transform(test)
    nomes = _feature_names(pred_rf)
    imp = model_rf.stages[-1].featureImportances.toArray()
    importancias = sorted(zip(nomes, imp), key=lambda x: -x[1])[:10]

    nota_por_atraso = [
        r.asDict()
        for r in data.where(F.col("nota_avaliacao").isNotNull())
        .groupBy("atrasado")
        .agg(
            F.count("*").alias("itens"),
            F.round(F.avg("nota_avaliacao"), 2).alias("nota_media"),
            F.round(F.avg((F.col("nota_avaliacao") <= 2).cast("int")) * 100, 2).alias("pct_nota_baixa"),
        )
        .orderBy("atrasado")
        .collect()
    ]
    corr = data.where(F.col("nota_avaliacao").isNotNull()).stat.corr("atraso_dias", "nota_avaliacao")

    atraso_por_mes = [
        r.asDict()
        for r in data.groupBy("mes_pedido")
        .agg(
            F.count("*").alias("itens"),
            F.round(F.avg("label") * 100, 2).alias("pct_atraso"),
        )
        .orderBy("mes_pedido")
        .collect()
    ]

    return {
        "modelo": model_rf,
        "linhas_modelagem": total,
        "pct_atraso": round(pos / total * 100, 2),
        "baseline_acuracia": round(base_acc, 4),
        "random_forest": metricas_rf,
        "regressao_logistica": metricas_lr,
        "importancias": [(n, round(float(v), 4)) for n, v in importancias],
        "nota_por_atraso": nota_por_atraso,
        "correlacao_atraso_nota": round(corr, 4),
        "atraso_por_mes": atraso_por_mes,
    }


def summarize_results(analysis_output):
    """Resume o resultado em um dicionario simples (sem objetos do Spark)."""
    rf = analysis_output["random_forest"]
    lr = analysis_output["regressao_logistica"]
    melhor = "random_forest" if rf["auc"] >= lr["auc"] else "regressao_logistica"
    meses = analysis_output["atraso_por_mes"]
    pior_mes = max(meses, key=lambda m: m["pct_atraso"])
    return {
        "linhas_modelagem": analysis_output["linhas_modelagem"],
        "pct_atraso": analysis_output["pct_atraso"],
        "baseline_acuracia_sempre_no_prazo": analysis_output["baseline_acuracia"],
        "melhor_modelo_por_auc": melhor,
        "random_forest": rf,
        "regressao_logistica": lr,
        "top_variaveis": analysis_output["importancias"][:5],
        "nota_por_atraso": analysis_output["nota_por_atraso"],
        "correlacao_atraso_nota": analysis_output["correlacao_atraso_nota"],
        "mes_com_mais_atraso": {
            "mes": int(pior_mes["mes_pedido"]),
            "pct_atraso": pior_mes["pct_atraso"],
        },
        "atraso_por_mes": meses,
    }


def main():
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--silver_path", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("analise-atraso-mercadofacil").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    silver = spark.read.parquet(args.silver_path)
    resultado = summarize_results(build_model_or_analysis(silver))
    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
    spark.stop()


if __name__ == "__main__":
    main()
