import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from _structure_checks import assert_section_filled, read_text

REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "FINAL_REPORT.md")

REQUIRED_TEXT_SECTIONS = [
    "## Resumo dos Resultados",
    "## Visualizações Criadas",
    "## Lições Aprendidas",
    "## Referências",
]

CHECKLIST_HEADER = "## Checklist de Entregáveis"
MIN_CHECKED_ITEMS = 4  # todos os 4 itens do template devem estar marcados


def _checklist_body(content):
    pattern = re.compile(
        rf"^{re.escape(CHECKLIST_HEADER)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    assert match, f"Secao '{CHECKLIST_HEADER}' nao encontrada no FINAL_REPORT.md"
    return match.group(1)


def test_all_text_sections_present():
    content = read_text(REPORT_PATH)
    for header in REQUIRED_TEXT_SECTIONS:
        assert header in content, f"Secao obrigatoria ausente: '{header}'"


def test_all_text_sections_filled():
    content = read_text(REPORT_PATH)
    for header in REQUIRED_TEXT_SECTIONS:
        assert_section_filled(content, header)


def test_checklist_present():
    content = read_text(REPORT_PATH)
    assert CHECKLIST_HEADER in content


def test_checklist_items_all_checked():
    content = read_text(REPORT_PATH)
    body = _checklist_body(content)
    checked = len(re.findall(r"^- \[[xX]\]", body, re.MULTILINE))
    unchecked = len(re.findall(r"^- \[ \]", body, re.MULTILINE))
    assert checked + unchecked >= MIN_CHECKED_ITEMS, (
        "O checklist de entregaveis parece ter sido alterado -- "
        f"esperados pelo menos {MIN_CHECKED_ITEMS} itens."
    )
    assert checked >= MIN_CHECKED_ITEMS, (
        f"Ainda faltam itens do checklist de entregaveis para marcar "
        f"(marcados: {checked}/{MIN_CHECKED_ITEMS}). Troque '[ ]' por "
        "'[x]' conforme cada entregavel for concluido."
    )
