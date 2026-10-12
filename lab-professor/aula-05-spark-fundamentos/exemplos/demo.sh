#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 05: Fundamentos do Spark (RDDs) em cluster real
# =============================================================================
# Roda `spark-submit` REAL dentro do cluster Spark (master + worker) do
# docker-compose desta aula. Cenario: analise de um log de acesso web
# (exemplos/data/acessos_portal.log) usando transformacoes de RDD.
#
#   docker compose up -d      # aguarde o master ficar "healthy"
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

MASTER="aula05-spark-master"

step "0) Conferindo o cluster Spark (master + worker)"
run "docker compose ps"

step "1) spark-submit: analise de log com RDDs, distribuida no cluster"
echo "   (map / filter / reduceByKey / sortBy sobre /data/acessos_portal.log)"
run "docker compose exec -T $MASTER spark-submit \
  --master spark://$MASTER:7077 \
  /data/rdd_demo.py"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET}"
echo "  - Spark master UI ....... http://localhost:8080 (veja o app e o worker)"
echo "Ao final: docker compose down -v"
