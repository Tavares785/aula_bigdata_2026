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
        A função `mapper` é chamada uma vez PARA CADA LINHA do arquivo
        de entrada.

        Para cada palavra encontrada:
          - converte para minúsculas
          - ignora palavras presentes em STOPWORDS
          - emite (palavra, 1)
        """

        # Converte a linha para minúsculas e extrai as palavras
        words = WORD_RE.findall(line.lower())

        # Processa cada palavra encontrada
        for word in words:

            # Ignora palavras muito comuns
            if word in STOPWORDS:
                continue

            # Emite a palavra com o valor 1
            yield word, 1

    def combiner(self, word, counts):
        """
        O `combiner` roda LOCALMENTE em cada máquina antes de enviar os
        dados pela rede para os reducers -- é uma otimização clássica do
        Hadoop para reduzir o tráfego de rede (chamada de "mini-reduce").
        Aqui ele já está pronto, pois tem exatamente a mesma lógica do
        reducer neste exemplo.
        """

        yield word, sum(counts)

    def reducer(self, word, counts):
        """
        A função `reducer` recebe TODOS os valores emitidos para uma
        mesma chave (palavra), vindos de todos os mappers/combiners.

        Soma todos os valores e produz o resultado final.
        """

        # Soma todas as ocorrências da palavra
        total = sum(counts)

        # Emite a palavra e sua quantidade total
        yield word, total


if __name__ == "__main__":
    MRWordFrequencyCount.run()