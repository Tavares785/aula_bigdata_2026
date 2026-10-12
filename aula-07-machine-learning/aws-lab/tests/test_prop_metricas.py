"""Teste de propriedade — intervalo das metricas de avaliacao.

Property 3: Metricas de avaliacao ficam no intervalo [0, 1]
Validates: Requirements 8.3, 2.1, 2.2, 2.3

*For any* DataFrame de previsoes valido (com `label` e `prediction`/`probability`),
a acuracia (`evaluate_accuracy`), a F1 (MulticlassClassificationEvaluator,
metricName="f1") e a AUC-ROC (BinaryClassificationEvaluator, areaUnderROC) sao
valores reais no intervalo fechado [0, 1].

Arquivo PROPRIO (nao `test_ml_job.py`) para evitar colisao com outras tasks.
Importa as implementacoes de referencia e a fixture `spark` do conftest.py
compartilhado — o `ml_job.py` de exercicio NAO e alterado (segue com os TODOs).
"""

from hypothesis import given, settings, strategies as st
from pyspark.ml.evaluation import (
    MulticlassClassificationEvaluator,
    BinaryClassificationEvaluator,
)

from conftest import (
    FEATURES,
    build_feature_vector,
    train_classifier,
    evaluate_accuracy,
)

# Tolerancia para erros de ponto flutuante nas bordas do intervalo.
_EPS = 1e-9


def _no_intervalo(valor):
    """True se `valor` for um float real dentro de [0, 1] (com tolerancia)."""
    return isinstance(valor, float) and (-_EPS <= valor <= 1.0 + _EPS)


# ---------------------------------------------------------------------------
# Geradores (hypothesis) de linhas (label, prediction) binarias 0/1.
# ---------------------------------------------------------------------------
# Uma linha de previsao: label e prediction em {0, 1}.
_linha = st.tuples(st.integers(min_value=0, max_value=1),
                   st.integers(min_value=0, max_value=1))

# Lista de linhas com AMBAS as classes garantidas em `label`, para que os
# evaluators binarios/multiclasse tenham dois rotulos para avaliar.
_previsoes = st.lists(_linha, min_size=1, max_size=40)


@settings(max_examples=100, deadline=None)
@given(linhas=_previsoes)
def test_acuracia_e_f1_no_intervalo(spark, linhas):
    """Acuracia e F1 ficam em [0, 1] para previsoes binarias variadas."""
    # Garante ao menos uma linha de cada classe em `label` para que o
    # evaluator multiclasse tenha os dois rotulos presentes.
    rows = [(int(lbl), float(pred)) for lbl, pred in linhas]
    rows.append((0, 0.0))
    rows.append((1, 1.0))

    df = spark.createDataFrame(rows, ["label", "prediction"])

    acc = evaluate_accuracy(df)
    f1 = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="f1"
    ).evaluate(df)

    assert _no_intervalo(acc), f"acuracia fora de [0,1]: {acc}"
    assert _no_intervalo(f1), f"f1 fora de [0,1]: {f1}"


@settings(max_examples=100, deadline=None)
@given(
    labels=st.lists(
        st.integers(min_value=0, max_value=1), min_size=6, max_size=30
    ),
    seeds=st.lists(
        st.integers(min_value=0, max_value=50), min_size=6, max_size=30
    ),
)
def test_auc_roc_no_intervalo(spark, labels, seeds):
    """AUC-ROC fica em [0, 1] usando previsoes reais (coluna probability).

    Para AUC precisamos de uma coluna `rawPrediction`/`probability` valida.
    Em vez de fabrica-la a mao, treinamos um LogisticRegression real sobre
    features derivadas, que gera `probability` corretamente. Garantimos ambas
    as classes em `label` para o BinaryClassificationEvaluator funcionar.
    """
    # Garante ambas as classes presentes.
    labels = list(labels) + [0, 1]

    # Deriva valores de features correlacionados ao label (sinal didatico),
    # com ruido via `seeds`, mantendo variacao entre os exemplos gerados.
    rows = []
    for i, lbl in enumerate(labels):
        s = seeds[i % len(seeds)] if seeds else 0
        meses = (30 - lbl * 25) + (s % 7)
        gasto = 120.0 - lbl * 60.0 + float(s)
        chamados = lbl * 5 + (s % 3)
        atraso = lbl + (s % 2)
        rows.append((meses, gasto, chamados, atraso, int(lbl)))

    df = spark.createDataFrame(rows, FEATURES + ["label"])

    dados = build_feature_vector(df)
    modelo = train_classifier(dados)
    previsoes = modelo.transform(dados)

    auc = BinaryClassificationEvaluator(
        labelCol="label", metricName="areaUnderROC"
    ).evaluate(previsoes)

    assert _no_intervalo(auc), f"AUC-ROC fora de [0,1]: {auc}"
