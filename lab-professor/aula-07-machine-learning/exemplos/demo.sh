#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 07: Machine Learning com Spark MLlib em cluster real
# =============================================================================
# Roda `spark-submit` REAL dentro do cluster Spark do docker-compose desta
# aula. Cenario: prever churn (cancelamento) de clientes a partir do
# historico de uso (exemplos/data/churn_clientes.csv).
#
#   docker compose up -d      # aguarde o master ficar "healthy"
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

MASTER="aula07-spark-master"

step "0) Conferindo o cluster Spark (master + worker)"
run "docker compose ps"

step "1) spark-submit: pipeline de classificacao de churn com MLlib"
echo "   (VectorAssembler -> LogisticRegression x RandomForest -> acuracia/F1/AUC-ROC)"
run "docker compose exec -T $MASTER spark-submit \
  --master spark://$MASTER:7077 \
  /data/ml_demo.py"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET}"
echo "  - Spark master UI ....... http://localhost:8080"
echo "Ao final: docker compose down -v"
