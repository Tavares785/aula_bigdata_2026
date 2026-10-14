"""
Aula 05 - Demo AO VIVO: fundamentos de RDD no Spark (cluster real).

Submetido via `spark-submit /data/rdd_demo.py` DENTRO do container
spark-master (veja exemplos/demo.sh). Le um log de acesso web real
(/data/acessos_portal.log) e aplica as MESMAS transformacoes de RDD
ensinadas no lab (map/filter/flatMap/reduceByKey/combineByKey), so que
agora rodando distribuido entre master e worker de um cluster Spark.

Cada linha do log:
  DATA HORA STATUS METODO ROTA USUARIO REGIAO
Ex: 2026-01-15 08:01:12 200 GET /home ana sudeste
"""
from pyspark.sql import SparkSession


def main():
    spark = SparkSession.builder.appName("aula05-demo-rdd").getOrCreate()
    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    # RDD base: uma particao por bloco; o Spark distribui entre os executors.
    linhas = sc.textFile("/data/acessos_portal.log")
    # Cada campo separado por espaco (rota = indice 4, status = 2, regiao = 6).
    campos = linhas.map(lambda l: l.split())

    print("\n=== 1) Total de requisicoes (RDD.count) ===")
    print(linhas.count())

    print("\n=== 2) Acessos por ROTA (map -> reduceByKey), ordenado ===")
    por_rota = (
        campos.map(lambda c: (c[4], 1))
        .reduceByKey(lambda a, b: a + b)
        .sortBy(lambda kv: -kv[1])
        .collect()
    )
    for rota, qtd in por_rota:
        print(f"  {rota:<12} {qtd}")

    print("\n=== 3) Apenas ERROS (status >= 400) usando filter ===")
    erros = campos.filter(lambda c: int(c[2]) >= 400)
    print(f"  requisicoes com erro: {erros.count()}")
    por_status = (
        erros.map(lambda c: (c[2], 1)).reduceByKey(lambda a, b: a + b).collect()
    )
    for status, qtd in sorted(por_status):
        print(f"  status {status}: {qtd}")

    print("\n=== 4) Requisicoes por REGIAO (contagem distribuida) ===")
    por_regiao = (
        campos.map(lambda c: (c[6], 1)).reduceByKey(lambda a, b: a + b).collect()
    )
    for regiao, qtd in sorted(por_regiao, key=lambda kv: -kv[1]):
        print(f"  {regiao:<10} {qtd}")

    spark.stop()


if __name__ == "__main__":
    main()
