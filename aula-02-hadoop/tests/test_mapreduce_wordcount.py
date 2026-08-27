import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mapreduce_wordcount import MRWordFrequencyCount

SAMPLE_TEXT = (
    "O gato correu atrás do rato. O rato correu para o buraco.\n"
    "O gato ficou triste.\n"
)


def run_job(text):
    """Executa o job MapReduce localmente (runner 'inline') e devolve um dict
    {palavra: contagem} com o resultado final do reducer."""
    job = MRWordFrequencyCount(["-r", "inline", "--no-conf"])
    job.sandbox(stdin=io.BytesIO(text.encode("utf-8")))
    results = {}
    with job.make_runner() as runner:
        runner.run()
        for key, value in job.parse_output(runner.cat_output()):
            results[key] = value
    return results


def test_mapper_ignores_stopwords():
    results = run_job(SAMPLE_TEXT)
    for stopword in ("o", "do", "para"):
        assert stopword not in results, f"'{stopword}' deveria ter sido filtrado pelo mapper"


def test_word_counts_are_correct():
    results = run_job(SAMPLE_TEXT)
    assert results.get("gato") == 2
    assert results.get("correu") == 2
    assert results.get("rato") == 2
    assert results.get("buraco") == 1
    assert results.get("triste") == 1


def test_case_insensitive_counting():
    text = "Dado dado DADO daDO\n"
    results = run_job(text)
    assert results.get("dado") == 4


def test_empty_input_returns_no_words():
    results = run_job("")
    assert results == {}
