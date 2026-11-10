"""
Execucao LOCAL do job da aula-05 (sem AWS Glue).

Usado como evidencia alternativa porque o acesso ao AWS Academy Learner Lab
expirou. Reaproveita as funcoes do aluno em job/rdd_job.py (word_count_rdd e
top_n_palavras) com um SparkContext local (driver + executors na mesma
maquina, master local[2]), e grava o resultado no mesmo formato do Glue
(uma linha "palavra,contagem" via saveAsTextFile).

Uso (a partir de aws-lab/):
    python evidencias/6325231/executar_local.py data/sample_lines.txt /tmp/output/wordcount
"""
import os
import sys

from pyspark import SparkContext

AWS_LAB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(AWS_LAB, "job"))

from rdd_job import top_n_palavras, word_count_rdd  # noqa: E402


def main():
    entrada, saida = sys.argv[1], sys.argv[2]
    sc = SparkContext("local[2]", "aula05-wordcount-local")
    sc.setLogLevel("ERROR")

    # Mesmo fluxo do main() do Glue: le as linhas, conta e grava.
    with open(entrada, encoding="utf-8") as f:
        linhas = [linha.rstrip("\n") for linha in f]

    resultado = word_count_rdd(sc, linhas)

    print("=== Word count (palavra,contagem) ===")
    for palavra, contagem in resultado:
        print(f"{palavra},{contagem}")

    sc.parallelize(resultado).map(lambda t: f"{t[0]},{t[1]}").saveAsTextFile(saida)
    print(f"Resultado gravado em: {saida}")

    print("=== TOP 5 ===")
    for palavra, contagem in top_n_palavras(sc, linhas, 5):
        print(f"{palavra},{contagem}")

    sc.stop()


if __name__ == "__main__":
    main()
