"""
Aula 12 - Verifica o checkpoint (PROGRESS.md), o ETL PySpark e a
documentacao das regras da camada silver (REGRAS_SILVER.md).
Checagem estrutural: o conteudo e avaliado pelo professor.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from _structure_checks import assert_section_filled, read_text  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROGRESS_PATH = os.path.join(ROOT, "PROGRESS.md")
REGRAS_PATH = os.path.join(ROOT, "aws-lab", "REGRAS_SILVER.md")
JOB_GLOB = os.path.join(ROOT, "aws-lab", "job", "*.py")

REQUIRED_PROGRESS_SECTIONS = [
    "## O que foi feito nesta etapa",
    "## Ferramentas efetivamente usadas",
    "## Dificuldades encontradas",
    "## Próxima etapa (Aula 13)",
]


def test_progress_doc_exists_and_sections_present():
    content = read_text(PROGRESS_PATH)
    for header in REQUIRED_PROGRESS_SECTIONS:
        assert header in content, f"Secao obrigatoria ausente no PROGRESS.md: '{header}'"


def test_progress_doc_sections_filled():
    content = read_text(PROGRESS_PATH)
    for header in REQUIRED_PROGRESS_SECTIONS:
        assert_section_filled(content, header)


def test_etl_job_is_a_real_pyspark_pipeline():
    files = glob.glob(JOB_GLOB)
    assert files, "Crie o script PySpark do Glue em aws-lab/job/*.py."
    src = "\n".join(open(f, encoding="utf-8").read() for f in files)
    assert "pyspark" in src, "O ETL deve usar PySpark."
    assert re.search(r"\.csv\(", src), "O ETL deve ler o CSV da camada raw."
    assert src.count(".parquet(") >= 2, (
        "O ETL deve gravar Parquet em pelo menos duas camadas (silver e gold)."
    )
    for camada in ("silver", "gold"):
        assert camada in src.lower(), f"O ETL deve referenciar a camada '{camada}'."
    assert "dropDuplicates" in src or "row_number" in src, (
        "Trate duplicados (dropDuplicates ou window + row_number)."
    )


def test_regras_silver_documented():
    content = read_text(REGRAS_PATH)
    assert "<PREENCHER" not in content.upper()
    itens = [ln for ln in content.splitlines() if re.match(r"\s*([-*]|\d+\.|\|)", ln)]
    assert len(itens) >= 6, (
        "REGRAS_SILVER.md deve listar pelo menos 6 problemas de qualidade "
        "encontrados no raw e a regra aplicada em cada um (lista ou tabela)."
    )
    assert len(content) >= 400
