"""
Aula 10 - Visualizacao e Analise de Dados em Larga Escala
Lab: Preparacao de dados para dashboards (agregacoes que alimentariam,
por exemplo, um painel no Apache Superset ou um notebook Zeppelin).

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
from collections import defaultdict


def aggregate_daily_totals(records):
    """
    TODO 1:
    Receba uma lista de dicionarios `records`, cada um com as chaves
    "date", "category" e "value". Retorne um dicionario {date:
    total_value}, somando "value" por "date" (ignorando a categoria),
    com as datas em ORDEM CRESCENTE.
    """
    totals = defaultdict(float)
    for record in records:
        totals[record["date"]] += record["value"]
    return dict(sorted(totals.items()))


def top_categories(records, n):
    """
    TODO 2:
    Receba uma lista de dicionarios `records` e retorne as `n`
    categorias com MAIOR valor total, como lista de tuplas
    (category, total_value), ordenada do maior para o menor.
    Em empate, ordena pelo nome da categoria em ordem alfabetica.
    """
    totals = defaultdict(float)
    for record in records:
        totals[record["category"]] += record["value"]
    sorted_cats = sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    return sorted_cats[:n]


def compute_moving_average(values, window):
    """
    TODO 3:
    Receba uma lista de numeros `values` e um tamanho de janela
    `window`, e retorne uma lista de mesmo tamanho com a MEDIA MOVEL,
    usando ate `window` elementos anteriores (incluindo o atual).
    Para posicoes iniciais onde nao ha `window` elementos, usa os
    disponiveis. Arredonde cada valor para 4 casas decimais.
    """
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_values = values[start:i + 1]
        result.append(round(sum(window_values) / len(window_values), 4))
    return result
