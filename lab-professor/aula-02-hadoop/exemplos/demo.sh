#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 02: Hadoop (HDFS + MapReduce/YARN)
# =============================================================================
# Roda comandos REAIS da tecnologia dentro do cluster Hadoop provisionado pelo
# docker-compose.yml desta aula. Nada de simulacao local: sao os mesmos
# binarios (`hdfs dfs`, `hadoop jar`) de um cluster de producao.
#
# Cenario realista: um portal de e-commerce gera um log de acesso web
# (exemplos/data/acessos_portal.log). Vamos:
#   1. Subir o arquivo para o HDFS (armazenamento distribuido em blocos)
#   2. Inspecionar como o HDFS o quebrou em blocos e replicou
#   3. Rodar um job MapReduce REAL (wordcount nativo do Hadoop) para contar
#      a frequencia de termos no log (paginas, status HTTP, regioes...)
#
# Pre-requisito: o cluster precisa estar de pe e saudavel.
#   docker compose up -d      # aguarde ~1-2 min (healthchecks ficam "healthy")
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

# Cores para deixar a demonstracao legivel no projetor.
BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

NN="hadoop-namenode"
RM="hadoop-resourcemanager"
HDFS_INPUT="/portal/input"
HDFS_OUTPUT="/portal/output"
LOCAL_FILE="/demo/data/acessos_portal.log"

step "0) Conferindo que os servicos do cluster estao no ar"
run "docker compose ps"

step "1) HDFS: criando o diretorio de entrada no sistema de arquivos distribuido"
run "docker compose exec -T $NN hdfs dfs -mkdir -p $HDFS_INPUT"

step "2) HDFS: enviando o log do portal para dentro do HDFS (comando real hdfs dfs -put)"
run "docker compose exec -T $NN hdfs dfs -put -f $LOCAL_FILE $HDFS_INPUT/"
run "docker compose exec -T $NN hdfs dfs -ls -h $HDFS_INPUT"

step "3) HDFS: relatorio do cluster + como o arquivo foi dividido em BLOCOS e replicado"
run "docker compose exec -T $NN hdfs dfsadmin -report | head -n 20"
run "docker compose exec -T $NN hdfs fsck $HDFS_INPUT/acessos_portal.log -files -blocks || true"

step "4) MapReduce/YARN: rodando um job REAL de contagem de palavras sobre o log"
echo "   (o mesmo modelo map -> shuffle/sort -> reduce ensinado na aula,"
echo "    executado pelo YARN e distribuido entre os NodeManagers)"
# Localiza o jar de exemplos do Hadoop dentro da imagem (versao pode variar).
JAR=$(docker compose exec -T $RM bash -lc 'ls /opt/hadoop-*/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar | head -n1' | tr -d '\r')
echo "   jar de exemplos encontrado: $JAR"
run "docker compose exec -T $RM hdfs dfs -rm -r -f $HDFS_OUTPUT"
run "docker compose exec -T $RM hadoop jar $JAR wordcount $HDFS_INPUT $HDFS_OUTPUT"

step "5) HDFS: lendo o resultado do job direto do sistema distribuido"
run "docker compose exec -T $RM hdfs dfs -cat $HDFS_OUTPUT/part-r-00000 | sort -k2 -n -r | head -n 20"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET} Abra as UIs no navegador para mostrar o cluster:"
echo "  - NameNode (HDFS) ....... http://localhost:9870"
echo "  - ResourceManager (YARN)  http://localhost:8088   (veja o job que acabou de rodar)"
echo "Ao final: docker compose down -v"
