"""
Aula 03 - Apache Kafka e Spark Streaming
Lab (parte 2/2): Agregacoes por janela de tempo (windowed aggregations),
o padrao central do processamento de streaming com Spark.

Contexto
--------
A funcao `F.window(...)` do Spark funciona tanto sobre DataFrames em
lote (batch) quanto sobre DataFrames de streaming (Structured
Streaming) -- por isso os testes conseguem validar sua logica com um
DataFrame estatico, mas o MESMO codigo funcionaria sem alteracao dentro
de um `readStream(...)` lendo de um topico Kafka de verdade (veja o
README para o exercicio pratico com Kafka real via Docker).

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""
from pyspark.sql import functions as F


def windowed_event_counts(events_df, window_duration="10 seconds"):
    """
    TODO 1:
    Receba `events_df`, um DataFrame com colunas ("event_time",
    "category", "amount"), e retorne um DataFrame com a CONTAGEM de
    eventos por JANELA DE TEMPO de tamanho `window_duration` e por
    "category". O resultado deve ter as colunas:
        window_start, window_end, category, count
    ordenado por window_start e depois por category.

    Dica:
        events_df.groupBy(F.window(F.col("event_time"), window_duration), F.col("category"))
                  .count()
        Depois, extraia "window.start" e "window.end" com `.select(...)`
        (a coluna gerada por F.window se chama "window" e e um struct
        com campos "start" e "end").
    """
    return (
        events_df
        # F.window gera uma coluna struct chamada "window", com os campos
        # start e end. Agrupar por ela e por category responde "quantos
        # eventos de cada categoria em cada fatia de tempo".
        .groupBy(
            F.window(F.col("event_time"), window_duration),
            F.col("category"),
        )
        .count()
        # O struct e achatado em duas colunas: manter "window" aninhado
        # obrigaria quem consome o resultado a conhecer a estrutura
        # interna do Spark.
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("category"),
            F.col("count"),
        )
        .orderBy("window_start", "category")
    )


def windowed_revenue_sum(events_df, window_duration="10 seconds"):
    """
    TODO 2:
    Receba `events_df` (mesmo formato do TODO 1) e retorne um DataFrame
    com a SOMA de "amount" por JANELA DE TEMPO de tamanho
    `window_duration` (sem separar por categoria desta vez). O resultado
    deve ter as colunas:
        window_start, window_end, total_amount
    ordenado por window_start.
    """
    return (
        events_df
        # Sem category no groupBy: aqui a pergunta e a receita total da
        # janela, independente do tipo de evento.
        .groupBy(F.window(F.col("event_time"), window_duration))
        # agg + alias em vez de .sum("amount"): o nome automatico sairia
        # como "sum(amount)", que nao e o contrato pedido.
        .agg(F.sum("amount").alias("total_amount"))
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("total_amount"),
        )
        .orderBy("window_start")
    )
