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
    result = (
        events_df
        .groupBy(
            F.window(F.col("event_time"), window_duration),
            F.col("category")
        )
        .count()
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("category"),
            F.col("count")
        )
        .orderBy("window_start", "category")
    )

    return result


def windowed_revenue_sum(events_df, window_duration="10 seconds"):
    result = (
        events_df
        .groupBy(
            F.window(F.col("event_time"), window_duration)
        )
        .agg(
            F.sum("amount").alias("total_amount")
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("total_amount")
        )
        .orderBy("window_start")
    )

    return result
