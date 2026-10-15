import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nlp_basics import tokenize, remove_stopwords, simple_stem, sentiment_score


def test_tokenize_basic():
    assert tokenize("O Gato correu, rapido!") == ["o", "gato", "correu", "rapido"]


def test_tokenize_ignores_numbers_and_punctuation():
    assert tokenize("Ano 2024: otimo!!!") == ["ano", "otimo"]


def test_tokenize_empty_string():
    assert tokenize("") == []


def test_remove_stopwords_basic():
    tokens = ["o", "gato", "e", "o", "rato"]
    stopwords = {"o", "e"}
    assert remove_stopwords(tokens, stopwords) == ["gato", "rato"]


def test_remove_stopwords_no_stopwords_present():
    tokens = ["gato", "rato"]
    assert remove_stopwords(tokens, {"o", "e"}) == ["gato", "rato"]


def test_simple_stem_ando_suffix():
    assert simple_stem("cantando") == "cant"


def test_simple_stem_endo_suffix():
    assert simple_stem("aprendendo") == "aprend"


def test_simple_stem_amente_suffix_preferred_over_mente():
    assert simple_stem("rapidamente") == "rapid"


def test_simple_stem_mente_suffix():
    assert simple_stem("felizmente") == "feliz"


def test_simple_stem_ador_suffix():
    assert simple_stem("jogador") == "jog"


def test_simple_stem_no_suffix_match():
    assert simple_stem("flor") == "flor"


def test_simple_stem_does_not_strip_below_min_length():
    # "ando" tem exatamente o sufixo "ando"; remover deixaria 0
    # caracteres, o que e menor que o minimo de 3 -- nao deve stemizar.
    assert simple_stem("ando") == "ando"


def test_sentiment_score_positive():
    tokens = ["otimo", "filme", "adorei"]
    positive = {"otimo", "adorei"}
    negative = {"pessimo", "odiei"}
    assert sentiment_score(tokens, positive, negative) == 2


def test_sentiment_score_negative():
    tokens = ["pessimo", "filme", "odiei", "chato"]
    positive = {"bom"}
    negative = {"pessimo", "odiei", "chato"}
    assert sentiment_score(tokens, positive, negative) == -3


def test_sentiment_score_neutral():
    tokens = ["filme", "assisti", "ontem"]
    positive = {"otimo"}
    negative = {"pessimo"}
    assert sentiment_score(tokens, positive, negative) == 0
