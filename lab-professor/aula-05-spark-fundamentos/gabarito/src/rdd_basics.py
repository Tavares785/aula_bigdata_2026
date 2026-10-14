"""
Aula 05 - Arquitetura e Fundamentos do Spark
Lab: Operacoes basicas com RDDs (Resilient Distributed Datasets).

Contexto
--------
Neste lab voce vai usar diretamente a API de RDDs do Spark (a API mais
"baixo nivel", sobre a qual DataFrames e Spark SQL sao construidos).
Voce recebe um `SparkContext` (`sc`) ja configurado -- na arquitetura do
Spark, o SparkContext roda no DRIVER e e responsavel por coordenar os
EXECUTORS que efetivamente processam os dados, particionados entre eles.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""


def word_count_rdd(sc, lines):
    """
    Receba uma lista de strings `lines` (cada item e uma "linha" de
    texto) e retorne a contagem de palavras usando RDDs, seguindo estes
    passos:
      1. Crie um RDD a partir de `lines` com `sc.parallelize(lines)`
      2. Use `flatMap` para quebrar cada linha em palavras (separadas
         por espaco) JA convertidas para minusculas
      3. Use `map` para transformar cada palavra em uma tupla (palavra, 1)
      4. Use `reduceByKey` para somar as ocorrencias de cada palavra
      5. Retorne o resultado como uma lista de tuplas (palavra, contagem),
         ORDENADA por contagem decrescente e, em caso de empate, por
         ordem alfabetica crescente da palavra.

    Exemplo:
        word_count_rdd(sc, ["gato rato gato", "rato correu gato"])
        -> [("gato", 3), ("rato", 2), ("correu", 1)]
    """
    counts = (
        sc.parallelize(lines)
        .flatMap(lambda line: line.lower().split())
        .map(lambda word: (word, 1))
        .reduceByKey(lambda a, b: a + b)
        .collect()
    )
    return sorted(counts, key=lambda item: (-item[1], item[0]))


def filter_and_square_evens(sc, numbers):
    """
    Receba uma lista de inteiros `numbers` e, usando um RDD:
      1. Filtre apenas os numeros pares (`filter`)
      2. Eleve cada um ao quadrado (`map`)
      3. Retorne o resultado como uma lista ORDENADA crescente

    Exemplo:
        filter_and_square_evens(sc, [1, 2, 3, 4, 5, 6]) -> [4, 16, 36]
    """
    result = (
        sc.parallelize(numbers)
        .filter(lambda n: n % 2 == 0)
        .map(lambda n: n * n)
        .collect()
    )
    return sorted(result)


def average_by_key(sc, pairs):
    """
    Receba uma lista de tuplas (chave, valor) `pairs` e calcule, usando
    um RDD, a MEDIA dos valores para cada chave. Retorne um dicionario
    {chave: media}.

    Dica: `combineByKey` e a ferramenta certa aqui, pois permite calcular
    soma e contagem ao mesmo tempo, em uma unica passada distribuida
    pelos dados -- exatamente o tipo de operacao que o Spark otimiza bem
    em um cluster real.

    Exemplo:
        average_by_key(sc, [("a", 10), ("b", 20), ("a", 30)])
        -> {"a": 20.0, "b": 20.0}
    """
    sums_and_counts = (
        sc.parallelize(pairs)
        .combineByKey(
            lambda value: (value, 1),
            lambda acc, value: (acc[0] + value, acc[1] + 1),
            lambda acc1, acc2: (acc1[0] + acc2[0], acc1[1] + acc2[1]),
        )
        .collect()
    )
    return {key: total / count for key, (total, count) in sums_and_counts}
