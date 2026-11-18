import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from _structure_checks import assert_function_implemented, assert_section_filled, read_text

ANALISE_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "analise.py")
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), "..", "PROGRESS.md")

REQUIRED_PROGRESS_SECTIONS = [
    "## Análise/modelo implementado",
    "## Principais resultados até agora",
    "## Iterações e ajustes feitos",
    "## Próxima etapa (Aula 14)",
]


def test_build_model_or_analysis_is_implemented():
    assert_function_implemented(ANALISE_PATH, "build_model_or_analysis")


def test_summarize_results_is_implemented():
    assert_function_implemented(ANALISE_PATH, "summarize_results")


def test_progress_doc_sections_present():
    content = read_text(PROGRESS_PATH)
    for header in REQUIRED_PROGRESS_SECTIONS:
        assert header in content, f"Secao obrigatoria ausente no PROGRESS.md: '{header}'"


def test_progress_doc_sections_filled():
    content = read_text(PROGRESS_PATH)
    for header in REQUIRED_PROGRESS_SECTIONS:
        assert_section_filled(content, header)
