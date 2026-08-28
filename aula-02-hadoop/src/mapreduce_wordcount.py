"""
Aula 02 - Hadoop & MapReduce
Lab: Contagem de palavras distribuída simulando um job Hadoop MapReduce.

Instruções gerais
------------------
Complete as funções `mapper` e `reducer` abaixo.

Este job usa a biblioteca `mrjob`, que implementa o MESMO modelo de
programação MapReduce usado pelo Hadoop de verdade (map -> shuffle/sort
-> reduce). Em modo "inline"/"local" (o que os testes automáticos usam),
o mrjob simula um cluster Hadoop na sua própria máquina, sem precisar
instalar um cluster de verdade. O MESMO código, sem nenhuma alteração,
poderia rodar em um cluster Hadoop real trocando o runner (ex: "-r hadoop").

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
from mrjob.job import MRJob
import re


# Palavras muito comuns em português que não agregam valor a uma análise
# de frequência de palavras (artigos, preposições, conjunções, etc.)
STOPWORDS = {
    "a", "o", "os", "as", "de", "da", "do", "das", "dos", "e", "que",
    "em", "um", "uma", "para", "com", "no", "na", "nos", "nas", "se",
    "por", "sua", "seu", "ao", "à", "às",
}


# Regex simples para extrair "palavras" (sequências de letras, incluindo
# acentos) de uma linha de texto.
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


class MRWordFrequencyCount(MRJob):

    def mapper(self, _, line):
        """
        A função `mapper` é chamada uma vez PARA CADA LINHA do arquivo de
        entrada.

        Para cada palavra encontrada:
          - converta a palavra para minúsculas
          - se estiver em STOPWORDS, ignore
          - caso contrário, emita (palavra, 1)
        """
        for word in WORD_RE.findall(line.lower()):
            if word not in STOPWORDS:
                yield word, 1

    def combiner(self, word, counts):
        """
        O `combiner` roda LOCALMENTE em cada máquina antes de enviar os
        dados pela rede para os reducers.
        """
        yield word, sum(counts)

    def reducer(self, word, counts):
        """
        A função `reducer` recebe todos os valores emitidos para uma mesma
        palavra e produz o resultado final agregado.
        """
        yield word, sum(counts)


if __name__ == "__main__":
    MRWordFrequencyCount.run()