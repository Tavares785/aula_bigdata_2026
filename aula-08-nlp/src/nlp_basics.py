"""
Aula 08 - NLP com Big Data
Lab: Blocos basicos de um pipeline de NLP (tokenizacao, remocao de
stopwords, stemming simplificado e analise de sentimento por lexico).
"""
import re

TOKEN_RE = re.compile(r"[a-zà-ÿ]+", re.IGNORECASE)

# Lista fixa de sufixos conhecidos para o stemming simplificado.
SUFFIXES = ["mente", "amente", "ando", "endo", "ador", "ação", "cao", "ção"]


def tokenize(text):
    """Retorna as palavras do texto em minusculas, sem numeros ou pontuacao."""
    return TOKEN_RE.findall(text.lower())


def remove_stopwords(tokens, stopwords):
    """Filtra stopwords sem alterar a ordem dos tokens restantes."""
    return [token for token in tokens if token not in stopwords]


def simple_stem(word):
    """Remove o sufixo conhecido mais longo, preservando no minimo 3 letras."""
    for suffix in sorted(SUFFIXES, key=len, reverse=True):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word


def sentiment_score(tokens, positive_words, negative_words):
    """Retorna a contagem positiva menos a contagem negativa dos tokens."""
    positive_count = sum(1 for token in tokens if token in positive_words)
    negative_count = sum(1 for token in tokens if token in negative_words)
    return positive_count - negative_count
