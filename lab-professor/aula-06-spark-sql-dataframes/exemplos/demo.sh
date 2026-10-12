#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 06: Spark SQL e DataFrames em cluster real
# =============================================================================
# Roda `spark-submit` REAL dentro do cluster Spark do docker-compose desta
# aula. Cenario: pedidos + clientes de um e-commerce (exemplos/data/*.csv).
# Mostra filter, groupBy/agg, join e a MESMA analise via Spark SQL.
#
#   docker compose up -d      # aguarde o master ficar "healthy"
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

MASTER="aula06-spark-master"

step "0) Conferindo o cluster Spark (master + worker)"
run "docker compose ps"

step "1) spark-submit: DataFrames + Spark SQL sobre pedidos e clientes"
echo "   (filter / groupBy+agg / join / spark.sql sobre /data/*.csv)"
run "docker compose exec -T $MASTER spark-submit \
  --master spark://$MASTER:7077 \
  /data/dataframe_demo.py"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET}"
echo "  - Spark master UI ....... http://localhost:8080"
echo "Ao final: docker compose down -v"
