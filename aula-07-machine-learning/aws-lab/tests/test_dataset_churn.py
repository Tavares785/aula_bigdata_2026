"""Testes de validacao do Dataset_TF (`data/churn.csv`).

Tarefa 8.6 (opcional) — valida o CSV de churn do Trabalho Final.

Estes testes sao PURO PYTHON (modulo `csv` da stdlib); nao dependem de Spark
nem de pacotes externos. Validam que o dataset entregue respeita o contrato
descrito nos requisitos:

  * cabecalho/colunas exatos (Requirement 10.2);
  * contagem de registros entre 30 e 50 inclusive (Requirement 10.3);
  * coluna `churn` binaria com ambas as classes presentes (Requirement 10.4);
  * tipos das colunas parseaveis (extra: reforca a qualidade do dado).

**Validates: Requirements 10.2, 10.3, 10.4**
"""

import csv
from pathlib import Path

import pytest

# Caminho do dataset relativo a este arquivo de teste (tests/ -> aws-lab/data).
CSV_PATH = Path(__file__).parent.parent / "data" / "churn.csv"

# Cabecalho EXATO esperado (ordem e nomes das colunas).
CABECALHO_ESPERADO = [
    "meses_ativo",
    "gasto_mensal",
    "chamados_suporte",
    "atraso_pagamento",
    "churn",
]


def _ler_csv():
    """Le o `churn.csv` e retorna (cabecalho, linhas_de_dados)."""
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        linhas = [linha for linha in csv.reader(f) if linha]
    assert linhas, "o arquivo churn.csv nao deve estar vazio"
    return linhas[0], linhas[1:]


def test_arquivo_existe():
    """O Dataset_TF deve existir no caminho esperado (`data/churn.csv`)."""
    assert CSV_PATH.is_file(), f"dataset nao encontrado em {CSV_PATH}"


def test_cabecalho_exato():
    """Teste 1 — cabecalho exato (Requirement 10.2)."""
    cabecalho, _ = _ler_csv()
    assert cabecalho == CABECALHO_ESPERADO, (
        "o cabecalho deve ser exatamente "
        f"{','.join(CABECALHO_ESPERADO)}; obtido: {','.join(cabecalho)}"
    )


def test_quantidade_de_registros_entre_30_e_50():
    """Teste 2 — numero de linhas de dados entre 30 e 50 inclusive (Req 10.3)."""
    _, dados = _ler_csv()
    assert 30 <= len(dados) <= 50, (
        f"o dataset deve ter entre 30 e 50 registros; obtido: {len(dados)}"
    )


def test_churn_binario_com_ambas_as_classes():
    """Teste 3 — `churn` so contem '0'/'1' e ambas as classes presentes (Req 10.4)."""
    cabecalho, dados = _ler_csv()
    idx_churn = cabecalho.index("churn")

    valores = {linha[idx_churn] for linha in dados}

    assert valores <= {"0", "1"}, (
        f"a coluna churn deve conter apenas '0' e '1'; obtido: {sorted(valores)}"
    )
    assert valores == {"0", "1"}, (
        "a coluna churn deve conter ambas as classes (0 e 1); "
        f"obtido: {sorted(valores)}"
    )


def test_tipos_das_colunas_parseaveis():
    """Teste 4 (extra) — tipos das colunas sao parseaveis.

    `gasto_mensal` como float; `meses_ativo`, `chamados_suporte`,
    `atraso_pagamento` e `churn` como int.
    """
    cabecalho, dados = _ler_csv()
    i_meses = cabecalho.index("meses_ativo")
    i_gasto = cabecalho.index("gasto_mensal")
    i_chamados = cabecalho.index("chamados_suporte")
    i_atraso = cabecalho.index("atraso_pagamento")
    i_churn = cabecalho.index("churn")

    for n, linha in enumerate(dados, start=2):  # start=2: linha 1 e o cabecalho
        try:
            float(linha[i_gasto])
        except ValueError:
            pytest.fail(f"linha {n}: gasto_mensal nao e float: {linha[i_gasto]!r}")

        for nome, idx in (
            ("meses_ativo", i_meses),
            ("chamados_suporte", i_chamados),
            ("atraso_pagamento", i_atraso),
            ("churn", i_churn),
        ):
            try:
                int(linha[idx])
            except ValueError:
                pytest.fail(f"linha {n}: {nome} nao e int: {linha[idx]!r}")
