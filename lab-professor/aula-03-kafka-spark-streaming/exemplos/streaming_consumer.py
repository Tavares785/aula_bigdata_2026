"""
Aula 03 - Demo AO VIVO: Spark Structured Streaming lendo de um topico Kafka REAL.

Este script e submetido via `spark-submit` dentro do container do Spark
(veja exemplos/demo.sh). Ele conecta no broker Kafka do docker-compose,
consome o topico "eventos", faz o parse do JSON e calcula, EM TEMPO REAL,
a receita por janela de tempo e por loja -- o mesmo padrao de janela
(F.window) ensinado no lab (gabarito/src/stream_aggregation.py), so que
agora sobre um stream de verdade.

Uso (dentro do container spark):
    spark-submit \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
      /opt/exemplos/streaming_consumer.py
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Schema dos eventos que chegam no topico (mesmo formato do sample_events.jsonl).
EVENT_SCHEMA = StructType([
    StructField("event_id", StringType()),
    StructField("event_time", StringType()),
    StructField("category", StringType()),
    StructField("amount", DoubleType()),
    StructField("loja", StringType()),
    StructField("pagamento", StringType()),
])

KAFKA_BOOTSTRAP = "kafka:29092"   # listener interno da rede do compose
TOPIC = "eventos"


def main():
    spark = (
        SparkSession.builder
        .appName("aula03-demo-streaming")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # 1) Fonte de streaming: um topico Kafka de verdade.
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    # 2) O "value" do Kafka vem como bytes -> string -> JSON estruturado.
    eventos = (
        raw.select(F.col("value").cast("string").alias("json"))
        .select(F.from_json("json", EVENT_SCHEMA).alias("e"))
        .select("e.*")
        .withColumn("event_time", F.to_timestamp("event_time"))
        .filter(F.col("category") == "compra")   # so receita de compras
    )

    # 3) Agregacao por JANELA DE TEMPO (10s) e por loja -- padrao central da aula.
    agregado = (
        eventos
        .groupBy(F.window("event_time", "10 seconds"), F.col("loja"))
        .agg(F.round(F.sum("amount"), 2).alias("receita"))
        .select(
            F.col("window.start").alias("inicio"),
            F.col("window.end").alias("fim"),
            F.col("loja"),
            F.col("receita"),
        )
        .orderBy("inicio", "loja")
    )

    # 4) Sink no console: mostra o resultado se atualizando a cada micro-batch.
    query = (
        agregado.writeStream
        .outputMode("complete")
        .format("console")
        .option("truncate", "false")
        .trigger(processingTime="5 seconds")
        .start()
    )

    # Roda por ~40s para a demonstracao e encerra sozinho.
    query.awaitTermination(timeout=40)
    query.stop()
    spark.stop()


if __name__ == "__main__":
    main()
