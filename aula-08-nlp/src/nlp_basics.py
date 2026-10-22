"""
Aula 08 - NLP com Big Data
Lab: Blocos basicos de um pipeline de NLP (tokenizacao, remocao de
stopwords, stemming simplificado e analise de sentimento por lexico).

Estas funcoes, aqui, rodam sobre uma unica string/lista por vez -- mas
sao exatamente o tipo de logica que, em um cenario real de Big Data,
voce aplicaria em PARALELO sobre milhoes de textos usando Spark
(ex: como uma UDF de DataFrame, ou dentro de um mapper), com Spark NLP
ou Apache OpenNLP por baixo.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
import re

TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)

# Lista fixa de sufixos conhecidos para o stemming simplificado do TODO 3.
# Use esta lista (nao invente outra) para que o resultado seja previsivel.
SUFFIXES = ["mente", "amente", "ando", "endo", "ador", "ação", "cao", "ção"]


def tokenize(text):
    """
    TODO 1:
    Receba uma string `text` e retorne a lista de "palavras" (tokens)
    nela contidas, TODAS em minusculas, ignorando numeros e pontuacao.

    Dica: use `TOKEN_RE.findall(text.lower())`.

    Exemplo:
        tokenize("O Gato correu, rapido!") -> ["o", "gato", "correu", "rapido"]
    """
    # TOKEN_RE so casa letras (inclusive acentuadas), entao numeros e
    # pontuacao ficam de fora sem precisar limpar nada antes.
    return TOKEN_RE.findall(text.lower())


def remove_stopwords(tokens, stopwords):
    """
    TODO 2:
    Receba uma lista de tokens `tokens` e um conjunto (set) de
    `stopwords`, e retorne uma nova lista contendo apenas os tokens que
    NAO estao em `stopwords`, preservando a ordem original.

    Exemplo:
        remove_stopwords(["o", "gato", "e", "o", "rato"], {"o", "e"})
        -> ["gato", "rato"]
    """
    # A ordem original e preservada porque a list comprehension percorre
    # os tokens na sequencia em que vieram.
    return [token for token in tokens if token not in stopwords]


def simple_stem(word):
    """
    TODO 3:
    Implemente um stemmer bem simplificado: se `word` termina com algum
    sufixo da lista `SUFFIXES`, remova esse sufixo -- MAS SOMENTE SE
    sobrarem pelo menos 3 caracteres depois de remover.

    Se MAIS DE UM sufixo da lista combinar com o final da palavra, use o
    sufixo MAIS LONGO (ex: para "rapidamente", prefira remover "amente"
    em vez de "mente", pois "amente" e mais especifico/longo).

    Se nenhum sufixo combinar (ou a palavra ficaria curta demais),
    retorne a palavra sem alteracao.

    Dica: `sorted(SUFFIXES, key=len, reverse=True)` ja te da os sufixos
    do mais longo para o mais curto, na ordem certa para testar.

    Exemplos:
        simple_stem("cantando")    -> "cant"
        simple_stem("rapidamente") -> "rapid"
        simple_stem("flor")        -> "flor"   (nenhum sufixo combina)
        simple_stem("ando")        -> "ando"   (sobraria so 0 caracteres)
    """
    # Do sufixo mais longo para o mais curto: assim "rapidamente" perde
    # "amente" (6) antes de considerar "mente" (5).
    for sufixo in sorted(SUFFIXES, key=len, reverse=True):
        if not word.endswith(sufixo):
            continue

        raiz = word[: len(word) - len(sufixo)]

        # So corta se sobrar raiz suficiente: "ando" viraria string vazia.
        if len(raiz) >= 3:
            return raiz

    return word


def sentiment_score(tokens, positive_words, negative_words):
    """
    TODO 4:
    Receba uma lista de `tokens` e dois conjuntos de palavras,
    `positive_words` e `negative_words`. Calcule um score de sentimento
    simples: (numero de tokens positivos) - (numero de tokens negativos).
    Retorne esse numero inteiro (pode ser negativo, zero ou positivo).

    Exemplo:
        sentiment_score(
            ["otimo", "filme", "adorei"],
            positive_words={"otimo", "adorei"},
            negative_words={"pessimo"},
        ) -> 2
    """
    positivos = sum(1 for token in tokens if token in positive_words)
    negativos = sum(1 for token in tokens if token in negative_words)

    return positivos - negativos
