"""Testes de EXEMPLO (nao property-based) do Job_ML (`job/ml_job.py`).

Tarefa 8.5 — Estado inicial (TODO) e importabilidade do modulo.

Cobrem dois aspectos descritos no design/requirements:

1. Estado inicial TODO (Req 8.4):
   As tres funcoes do aluno (`build_feature_vector`, `train_classifier` e
   `evaluate_accuracy`) devem levantar `NotImplementedError` enquanto nao forem
   implementadas (estado de exercicio entregue ao aluno).

2. Importabilidade sem o SDK `awsglue` (Req 8.5):
   `job/ml_job.py` deve ser IMPORTAVEL localmente, mesmo sem o SDK do AWS Glue
   instalado (o modulo encapsula o import do `awsglue` em try/except ImportError).
   Verificamos tambem que a constante `FEATURES` esta correta.

Estes sao testes por EXEMPLO (asserts diretos), complementares aos testes de
propriedade (tarefas 8.1-8.4). NAO sobrescrevem nem alteram `job/ml_job.py`.
"""

import importlib.util
import os
import sys

import pytest

# Mesmo padrao de sys.path dos demais testes: insere `../job` para `import ml_job`.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "job"))
)

import ml_job  # noqa: E402  (depende do ajuste de sys.path acima)


# ---------------------------------------------------------------------------
# 1. Estado inicial TODO (Req 8.4)
# ---------------------------------------------------------------------------
def test_build_feature_vector_estado_todo_levanta_not_implemented():
    """`build_feature_vector` deve levantar NotImplementedError no estado TODO.

    **Validates: Requirements 8.4**
    """
    with pytest.raises(NotImplementedError):
        ml_job.build_feature_vector(None)


def test_train_classifier_estado_todo_levanta_not_implemented():
    """`train_classifier` deve levantar NotImplementedError no estado TODO.

    **Validates: Requirements 8.4**
    """
    with pytest.raises(NotImplementedError):
        ml_job.train_classifier(None)


def test_evaluate_accuracy_estado_todo_levanta_not_implemented():
    """`evaluate_accuracy` deve levantar NotImplementedError no estado TODO.

    **Validates: Requirements 8.4**
    """
    with pytest.raises(NotImplementedError):
        ml_job.evaluate_accuracy(None)


# ---------------------------------------------------------------------------
# 2. Importabilidade sem o SDK awsglue (Req 8.5)
# ---------------------------------------------------------------------------
def test_ml_job_importavel_sem_awsglue():
    """`ml_job` importa localmente e expoe a constante FEATURES esperada.

    O proprio `import ml_job` (no topo deste arquivo) ja comprova que o modulo e
    importavel sem o SDK do Glue, gracas ao try/except ImportError do modulo.

    **Validates: Requirements 8.5**
    """
    # Objeto de modulo valido e com as funcoes esperadas.
    assert ml_job is not None
    assert callable(ml_job.build_feature_vector)
    assert callable(ml_job.train_classifier)
    assert callable(ml_job.evaluate_accuracy)

    # Constante de features exata (Req 1.2 / 8.1 / 8.5).
    assert ml_job.FEATURES == [
        "meses_ativo",
        "gasto_mensal",
        "chamados_suporte",
        "atraso_pagamento",
    ]


def test_awsglue_nao_instalado_no_ambiente_local():
    """Em ambiente local tipico o SDK `awsglue` nao esta instalado.

    Se por acaso o SDK estiver presente (ambiente nao usual), a assercao e
    pulada — o relevante (importabilidade) ja foi coberto acima.

    **Validates: Requirements 8.5**
    """
    if importlib.util.find_spec("awsglue") is not None:
        pytest.skip("awsglue esta instalado neste ambiente; assercao nao se aplica")
    assert importlib.util.find_spec("awsglue") is None
