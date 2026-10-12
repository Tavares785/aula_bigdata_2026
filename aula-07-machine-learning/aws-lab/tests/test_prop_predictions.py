"""Property 2 — Previsoes tem uma linha por entrada e coluna `prediction`.

**Property 2: Previsoes tem uma linha por entrada e coluna `prediction`**
**Validates: Requirements 8.2, 1.5, 1.6**

*For any* DataFrame de treino e de teste validos (com colunas `features` e
`label`), o modelo retornado por `train_classifier`, ao transformar o conjunto de
teste, produz um DataFrame com a coluna `prediction` e exatamente uma linha para
cada linha de teste.

A implementacao de REFERENCIA (`ref_build_feature_vector`, `ref_train_classifier`)
vem do modulo `ml_reference.py` compartilhado — assim o teste PASSA agora,
enquanto o `job/ml_job.py` de exercicio permanece com os TODOs
(`NotImplementedError`).

Estrategia (design.md, "Estrategia de Testes"): minimo de 100 casos. O custo de
treinar um modelo Spark por exemplo e alto, entao combinamos o Hypothesis (que
gera DataFrames variados) com um loop interno que acumula casos ate atingir a
semantica de ">= 100 casos" cobertos.
"""

import pytest
from hypothesis import given, settings, HealthCheck, strategies as st

from ml_reference import (
    FEATURES,
    ref_build_feature_vector,
    ref_train_classifier,
)

# Numero minimo de casos exigido pela estrategia de testes do design.
MIN_CASOS = 100

# Contador de casos cobertos ao longo da execucao do teste de propriedade.
# Validamos ao final (via fixture) que atingimos pelo menos MIN_CASOS.
_casos_cobertos = {"total": 0}


def _rows_from(features_rows, labels):
    """Monta linhas (meses_ativo, gasto_mensal, chamados_suporte,
    atraso_pagamento, label) a partir das features geradas e dos rotulos."""
    linhas = []
    for feats, lab in zip(features_rows, labels):
        meses, gasto, chamados, atraso = feats
        linhas.append(
            (
                int(meses),
                float(gasto),
                int(chamados),
                int(atraso),
                float(lab),
            )
        )
    return linhas


# Gera uma unica linha de features dentro de faixas plausiveis do dataset.
_feature_row = st.tuples(
    st.integers(min_value=0, max_value=72),      # meses_ativo
    st.floats(min_value=0.0, max_value=500.0,
              allow_nan=False, allow_infinity=False),  # gasto_mensal
    st.integers(min_value=0, max_value=12),      # chamados_suporte
    st.integers(min_value=0, max_value=5),       # atraso_pagamento
)


@st.composite
def datasets(draw):
    """Gera (linhas_treino, linhas_teste) variados.

    - O treino sempre contem AMBAS as classes (0 e 1), condicao necessaria para
      o LogisticRegression treinar.
    - O teste tem tamanho >= 1 (verificamos "uma linha por entrada").
    """
    n_treino = draw(st.integers(min_value=6, max_value=16))
    n_teste = draw(st.integers(min_value=1, max_value=10))

    feats_treino = draw(st.lists(_feature_row, min_size=n_treino, max_size=n_treino))
    feats_teste = draw(st.lists(_feature_row, min_size=n_teste, max_size=n_teste))

    # Rotulos do treino: garante ambas as classes (primeira metade 0, resto 1),
    # depois embaralha de forma deterministica via Hypothesis.
    metade = n_treino // 2
    labels_treino = [0] * metade + [1] * (n_treino - metade)
    labels_treino = draw(st.permutations(labels_treino))
    # Garante explicitamente a presenca das duas classes.
    assert 0 in labels_treino and 1 in labels_treino

    # Rotulos do teste: quaisquer 0/1 (nao precisam cobrir ambas as classes).
    labels_teste = draw(
        st.lists(st.sampled_from([0, 1]), min_size=n_teste, max_size=n_teste)
    )

    return (
        _rows_from(feats_treino, labels_treino),
        _rows_from(feats_teste, labels_teste),
    )


@given(dados=datasets())
# max_examples >= 100 cobre a exigencia de ">= 100 casos" do design.
# O deadline e desativado porque treinar um modelo Spark por exemplo e lento.
@settings(
    max_examples=MIN_CASOS,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_prop2_previsoes_uma_linha_por_entrada_e_coluna_prediction(spark, dados):
    """Property 2: previsoes tem coluna `prediction` e 1 linha por entrada."""
    linhas_treino, linhas_teste = dados
    colunas = FEATURES + ["label"]

    treino = ref_build_feature_vector(
        spark.createDataFrame(linhas_treino, colunas)
    )
    teste = ref_build_feature_vector(
        spark.createDataFrame(linhas_teste, colunas)
    )

    modelo = ref_train_classifier(treino)
    previsoes = modelo.transform(teste)

    # (1.6) existe a coluna `prediction` no resultado da transformacao.
    assert "prediction" in previsoes.columns

    # (1.5 / 1.6) exatamente uma linha de previsao para cada linha de teste.
    assert previsoes.count() == teste.count()

    _casos_cobertos["total"] += 1


@pytest.fixture(scope="module", autouse=True)
def _verifica_cobertura_minima():
    """Apos a propriedade rodar, confirma que cobrimos >= MIN_CASOS casos."""
    yield
    assert _casos_cobertos["total"] >= MIN_CASOS, (
        f"Esperado >= {MIN_CASOS} casos cobertos, "
        f"mas foram {_casos_cobertos['total']}."
    )
