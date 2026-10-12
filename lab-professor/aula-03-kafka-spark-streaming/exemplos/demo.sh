#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 03: Apache Kafka + Spark Structured Streaming
# =============================================================================
# Roda comandos REAIS dentro dos servicos do docker-compose desta aula
# (Zookeeper + Kafka + Spark). Cenario: um fluxo de eventos de e-commerce
# (compras/devolucoes de varias lojas) chegando em tempo real.
#
#   1. Cria um topico Kafka real ("eventos") com particoes
#   2. Produz os eventos do exemplos/data/sample_events.jsonl no topico
#      (kafka-console-producer real)
#   3. Consome com um consumidor de console (mostra as mensagens cruas)
#   4. Roda um job Spark Structured Streaming REAL que agrega receita por
#      janela de tempo e por loja, lendo direto do topico Kafka
#
# Pre-requisito:
#   docker compose up -d      # aguarde zookeeper -> kafka -> spark "healthy"
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

# Nomes de SERVICO do docker-compose (nao os container_name).
# `docker compose exec` espera o nome do servico definido no compose.
KAFKA="kafka"
SPARK="spark"
BOOTSTRAP="localhost:9092"
TOPIC="eventos"

step "0) Conferindo os servicos (zookeeper, kafka, spark)"
run "docker compose ps"

step "1) Kafka: criando o topico '$TOPIC' com 3 particoes (comando real kafka-topics.sh)"
run "docker compose exec -T $KAFKA kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --create --if-not-exists --topic $TOPIC --partitions 3 --replication-factor 1"
run "docker compose exec -T $KAFKA kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --describe --topic $TOPIC"

step "2) Kafka: produzindo os eventos do arquivo no topico (kafka-console-producer.sh real)"
echo "   fonte: exemplos/data/sample_events.jsonl (montado em /data no broker)"
run "docker compose exec -T $KAFKA bash -c \
  'cat /data/sample_events.jsonl | kafka-console-producer.sh --bootstrap-server $BOOTSTRAP --topic $TOPIC'"

step "3) Kafka: lendo as primeiras mensagens do topico (consumidor de console real)"
run "docker compose exec -T $KAFKA kafka-console-consumer.sh --bootstrap-server $BOOTSTRAP \
  --topic $TOPIC --from-beginning --max-messages 5 --timeout-ms 10000 || true"

step "4) Spark Structured Streaming: agregando receita por janela de tempo e loja EM TEMPO REAL"
echo "   (submete /opt/exemplos/streaming_consumer.py lendo direto do topico Kafka)"
run "docker compose exec -T $SPARK spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  /opt/exemplos/streaming_consumer.py"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET}"
echo "  - Spark master UI ....... http://localhost:8080"
echo "Ao final: docker compose down -v"
