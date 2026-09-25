"""
Aula 03 - Apache Kafka e Spark Streaming
Lab (parte 2/2): Agregacoes por janela de tempo (windowed aggregations).
"""

from pyspark.sql import functions as F


def windowed_event_counts(events_df, window_duration="10 seconds"):
    """
    Conta os eventos por janela de tempo e categoria.
    """
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
    """
    Soma o valor dos eventos por janela de tempo.
    """
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