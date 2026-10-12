#!/usr/bin/env bash
# =============================================================================
# Demo AO VIVO - Aula 04: NoSQL com MongoDB (banco orientado a documentos)
# =============================================================================
# Roda comandos REAIS dentro do container do MongoDB provisionado pelo
# docker-compose.yml desta aula (mongoimport + mongosh). Cenario: catalogo de
# produtos de um e-commerce (exemplos/data/produtos.jsonl).
#
# Demonstra o que o lab ensina, mas contra um MongoDB de VERDADE:
#   1. Importa o catalogo (mongoimport)
#   2. CRUD: consultas com filtro/projecao/ordenacao, insert, update ($inc)
#   3. Pipeline de agregacao ($group, $avg, $sort) -- preco medio por categoria
#
# Pre-requisito:
#   docker compose up -d      # aguarde o healthcheck do mongodb ("healthy")
#   ./exemplos/demo.sh
#   docker compose down -v
# =============================================================================
set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${BOLD}${CYAN}==> $*${RESET}"; }
run()  { echo -e "${GREEN}\$ $*${RESET}"; eval "$@"; }

MONGO="mongodb"  # nome do SERVICO no docker-compose (nao o container_name)
DB="loja"
COL="produtos"

step "0) Conferindo o servico do MongoDB"
run "docker compose ps"

step "1) mongoimport: carregando o catalogo de produtos (comando real)"
run "docker compose exec -T $MONGO mongoimport --db $DB --collection $COL \
  --drop --file /data/sample/produtos.jsonl"

step "2) READ: total de documentos e produtos de eletronicos (filtro + projecao + sort)"
run "docker compose exec -T $MONGO mongosh --quiet $DB --eval \
  'db.$COL.countDocuments()'"
run "docker compose exec -T $MONGO mongosh --quiet $DB --eval \
  'db.$COL.find({category: \"eletronicos\"}, {_id:0, nome:1, price:1}).sort({price:1}).toArray()'"

step "3) CREATE: inserindo um novo produto (insertOne real)"
run "docker compose exec -T $MONGO mongosh --quiet $DB --eval \
  'db.$COL.insertOne({product_id:\"p13\", nome:\"SSD 1TB\", category:\"eletronicos\", price:499.90, stock:40, tags:[\"armazenamento\"], avaliacao:4.7})'"

step "4) UPDATE: baixando 5 unidades do estoque do notebook (operador atomico \$inc)"
run "docker compose exec -T $MONGO mongosh --quiet $DB --eval \
  'db.$COL.updateOne({product_id:\"p1\"}, {\$inc:{stock:-5}}); db.$COL.findOne({product_id:\"p1\"}, {_id:0, nome:1, stock:1})'"

step "5) AGGREGATION: preco medio e estoque total por categoria (pipeline \$group real)"
run "docker compose exec -T $MONGO mongosh --quiet $DB --eval \
  'db.$COL.aggregate([{\$group:{_id:\"\$category\", preco_medio:{\$avg:\"\$price\"}, estoque_total:{\$sum:\"\$stock\"}, itens:{\$sum:1}}}, {\$sort:{preco_medio:-1}}]).toArray()'"

echo -e "\n${BOLD}${GREEN}Demo concluida.${RESET} Conecte manualmente com:"
echo "  docker compose exec $MONGO mongosh $DB"
echo "Ao final: docker compose down -v"
