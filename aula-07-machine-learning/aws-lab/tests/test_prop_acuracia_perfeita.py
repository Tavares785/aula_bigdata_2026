"""Property 4: Previsao perfeita implica acuracia maxima.

*For any* DataFrame de previsoes em que `prediction` e igual a `label` em todas
as linhas, `evaluate_accuracy` retorna exatamente `1.0`.

**Validates: Requirements 8.3, 2.1**

Usa a implementacao de REFERENCIA `ref_evaluate_accuracy` do `conftest.py`
compartilhado (o `ml_job.py` de exercicio permanece com `NotImplementedError`).
"""

import pytest
from hypothesis import given, settings, strategies as st

from conftest import ref_evaluate_accuracy


# Gera uma sequencia de rotulos binarios (0/1), de tamanho variavel (>= 1).
# Cada rotulo vira uma linha onde prediction == label, garantindo previsao
# perfeita em TODAS as linhas.
labels_strategy = st.lists(st.integers(min_value=0, max_value=1), min_size=1, max_size=60)


@settings(max_examples=100, deadline=None)
@given(labels=labels_strategy)
def test_previsao_perfeita_implica_acuracia_maxima(spark, labels):
    """Quando prediction == label em todas as linhas, a acuracia e exatamente 1.0."""
    # prediction identico a label em cada linha -> previsao perfeita.
    rows = [(float(v), float(v)) for v in labels]
    previsoes = spark.createDataFrame(rows, ["label", "prediction"])

    acuracia = ref_evaluate_accuracy(previsoes)

    assert acuracia == pytest.approx(1.0)
