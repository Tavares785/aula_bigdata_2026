"""
Aula 11 - Definicao e Planejamento do Projeto

Este lab NAO tem uma "resposta certa" fixa (cada grupo escolhe seu
proprio problema/dataset) -- por isso a correcao automatica verifica
CONFORMIDADE ESTRUTURAL: se todas as secoes obrigatorias existem e
foram de fato preenchidas (nao deixadas com o texto `<PREENCHER>` do
template, nem vazias/curtas demais).
"""
import os
import re

PROPOSAL_PATH = os.path.join(os.path.dirname(__file__), "..", "PROJECT_PROPOSAL.md")

REQUIRED_SECTIONS = [
    "## Integrantes do Grupo",
    "## Problema",
    "## Objetivos",
    "## Dataset(s) e Fonte",
    "## Ferramentas de Big Data",
    "## Arquitetura do Pipeline",
]

MIN_CHARS_PER_SECTION = 20


def _read_proposal():
    assert os.path.exists(PROPOSAL_PATH), (
        "Arquivo PROJECT_PROPOSAL.md nao encontrado. Ele deve continuar "
        "na raiz da pasta aula-11-planejamento-projeto/."
    )
    with open(PROPOSAL_PATH, encoding="utf-8") as f:
        return f.read()


def _section_body(content, header):
    pattern = re.compile(
        rf"^{re.escape(header)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    assert match, f"Secao '{header}' nao foi encontrada no PROJECT_PROPOSAL.md"
    return match.group(1).strip()


def test_all_required_sections_present():
    content = _read_proposal()
    for header in REQUIRED_SECTIONS:
        assert header in content, f"Secao obrigatoria ausente: '{header}'"


def test_no_placeholder_left_in_any_section():
    content = _read_proposal()
    for header in REQUIRED_SECTIONS:
        body = _section_body(content, header)
        assert "<PREENCHER" not in body.upper(), (
            f"Secao '{header}' ainda contem o placeholder '<PREENCHER...>' "
            "do template -- substitua pelo conteudo real do seu grupo."
        )


def test_sections_have_minimum_content():
    content = _read_proposal()
    for header in REQUIRED_SECTIONS:
        body = _section_body(content, header)
        assert len(body) >= MIN_CHARS_PER_SECTION, (
            f"Secao '{header}' parece vazia ou curta demais "
            f"(minimo de {MIN_CHARS_PER_SECTION} caracteres de conteudo real)."
        )


def test_integrantes_section_lists_names():
    content = _read_proposal()
    body = _section_body(content, "## Integrantes do Grupo")
    # Espera pelo menos um caractere alfabetico (nome), nao so pontuacao
    assert re.search(r"[A-Za-zÀ-ÿ]{2,}", body), (
        "A secao 'Integrantes do Grupo' nao parece conter nomes reais."
    )
