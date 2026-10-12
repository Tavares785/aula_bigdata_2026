"""Testes locais do Job_ML (`job/ml_job.py`).

Tarefa 8.1 — Teste de PROPRIEDADE para `build_feature_vector`.

Property 1 (design.md > "Correctness Properties"):
    "Montagem do vetor de features preserva linhas e dimensao"
    Para QUALQUER DataFrame contendo as colunas meses_ativo, gasto_mensal,
    chamados_suporte e atraso_pagamento, aplicar `build_feature_vector` produz um
    DataFrame com a coluna `features` cujo vetor tem dimensao 4 e cuja contagem de
    linhas e identica a do DataFrame de entrada.

**Validates: Requirements 8.1, 1.2**

Framework: pytest + hypothesis (estrategia de testes do design).

Estado TODO e verificabilidade:
    O `job/ml_job.py` de exercicio mantem `build_feature_vector` como TODO
    (levanta `NotImplementedError`). Para que esta propriedade seja EXECUTAVEL e
    PASSE agora — comprovando que o proprio teste esta correto — usamos uma
    implementacao VERIFICAVEL resolvida por `_resolver_build_feature_vector()`:
      * se o aluno ja implementou `ml_job.build_feature_vector`, o teste roda
        sobre a implementacao dele;
      * enquanto estiver no estado TODO, cai para a implementacao de REFERENCIA
        do modulo `ml_reference.py` (gabarito esperado).
    O arquivo de exercicio `job/ml_job.py` permanece INALTERADO.
"""

import os
import sys

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from pyspark.sql.types import StructType, StructField, DoubleType

# Garante que `job/ml_job.py` seja importavel mesmo quando este modulo e
# coletado antes do conftest (ordem de import do pytest).
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "job"))
)

import ml_job  # noqa: E402  (depende do ajuste de sys.path acima)
# Implementacao de REFERENCIA compartilhada (modulo dedicado, import inequivoco).
from ml_reference import ref_build_feature_vector as _reference_build_feature_vector  # noqa: E402

# Dimensao esperada do vetor de features (4 colunas em ml_job.FEATURES).
EXPECTED_DIM = 4


def _resolver_build_feature_vector():
    """Retorna uma versao VERIFICAVEL de `build_feature_vector`.

    Prefere a implementacao do aluno em `ml_job.build_feature_vector`; se ela
    ainda estiver no estado TODO (`NotImplementedError`), usa a de referencia.
    """
    try:
        # Sonda barata: no estado TODO levanta antes de qualquer trabalho Spark.
        ml_job.build_feature_vector(None)
    except NotImplementedError:
        return _reference_build_feature_vector
    except Exception:
        # Implementada pelo aluno (falhou com `None` por outro motivo); usa a dele.
        return ml_job.build_feature_vector
    return ml_job.build_feature_vector


# Uma "linha" = valores das 4 colunas (meses_ativo, gasto_mensal,
# chamados_suporte, atraso_pagamento). Floats finitos e variados cobrem uma
# ampla faixa do espaco de entrada.
_valor = st.floats(
    allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6
)
_linha = st.tuples(_valor, _valor, _valor, _valor)
# Numero de linhas variavel (inclui DataFrame vazio, borda relevante).
_linhas = st.lists(_linha, min_size=0, max_size=25)


# Esquema explicito (4 colunas DoubleType) para que o DataFrame seja construivel
# mesmo quando vazio (Spark nao consegue inferir esquema de dataset vazio).
_SCHEMA = StructType(
    [StructField(nome, DoubleType(), True) for nome in ml_job.FEATURES]
)


def _vector_dim(value):
    """Dimensao de um valor de coluna vetor do MLlib (DenseVector/SparseVector)."""
    return int(value.size)


@settings(
    max_examples=100,  # minimo de 100 iteracoes exigido pela tarefa 8.1
    deadline=None,  # cada exemplo roda um job Spark; sem deadline por exemplo
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(linhas=_linhas)
def test_build_feature_vector_preserva_linhas_e_dimensao(spark, linhas):
    """Property 1 — preserva contagem de linhas e produz `features` de dimensao 4.

    **Validates: Requirements 8.1, 1.2**
    """
    build_feature_vector = _resolver_build_feature_vector()

    df = spark.createDataFrame(list(linhas), schema=_SCHEMA)

    resultado = build_feature_vector(df)

    # 1. A coluna `features` deve existir.
    assert "features" in resultado.columns, (
        "build_feature_vector deve adicionar a coluna 'features'"
    )

    # 2. A contagem de linhas deve ser preservada.
    assert resultado.count() == len(linhas), (
        "build_feature_vector deve preservar a contagem de linhas de entrada"
    )

    # 3. Toda linha deve ter um vetor `features` de dimensao 4.
    for row in resultado.select("features").collect():
        assert _vector_dim(row["features"]) == EXPECTED_DIM, (
            f"o vetor 'features' deve ter dimensao {EXPECTED_DIM}"
        )
