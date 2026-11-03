"""
Aula 10 - Visualizacao e Analise de Dados em Larga Escala
Lab: Preparacao de dados para dashboards (agregacoes que alimentariam,
por exemplo, um painel no Apache Superset ou um notebook Zeppelin).

Por que este lab e "so" sobre preparar dados, e nao sobre a visualizacao
em si? Porque ferramentas de BI interativas (Zeppelin, Superset) nao sao
faceis de testar automaticamente -- a parte que PODE (e deve) ser
testada de forma confiavel e a logica de agregacao que alimenta esses
paineis. A parte visual fica como pratica manual (veja o README).

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

    Exemplo:
        records = [
            {"date": "2026-01-01", "category": "livros", "value": 20.0},
            {"date": "2026-01-01", "category": "moveis", "value": 100.0},
        ]
        aggregate_daily_totals(records) -> {"2026-01-01": 120.0}
    """
    raise NotImplementedError("TODO 1: implemente aggregate_daily_totals")


def top_categories(records, n):
    """
    TODO 2:
    Receba uma lista de dicionarios `records` (mesmo formato do TODO 1)
    e retorne as `n` categorias com MAIOR valor total (somando "value"
    por "category"), como uma lista de tuplas (category, total_value),
    ordenada do maior para o menor total. Em caso de empate, ordene pelo
    nome da categoria em ordem alfabetica.
    """
    raise NotImplementedError("TODO 2: implemente top_categories")


def compute_moving_average(values, window):
    """
    TODO 3:
    Receba uma lista de numeros `values` e um tamanho de janela
    `window`, e retorne uma lista de mesmo tamanho com a MEDIA MOVEL
    (moving average) de `values`, usando ate `window` elementos
    anteriores (incluindo o atual) em cada posicao. Para as primeiras
    posicoes, onde ainda nao ha `window` elementos disponiveis, use
    apenas os elementos disponiveis ate ali.

    Arredonde cada valor para 4 casas decimais.

    Exemplo:
        compute_moving_average([1, 2, 3, 4, 5], window=3)
        -> [1.0, 1.5, 2.0, 3.0, 4.0]
        (na posicao 0: media de [1]; na posicao 1: media de [1,2];
         na posicao 2 em diante: media dos ultimos 3 valores)
    """
    raise NotImplementedError("TODO 3: implemente compute_moving_average")
