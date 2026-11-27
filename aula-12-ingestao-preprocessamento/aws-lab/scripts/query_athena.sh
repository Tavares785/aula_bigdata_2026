#!/usr/bin/env bash
# Executa no Athena as consultas de aws-lab/scripts/consultas_gold.sql
# (separadas por ';') e imprime o resultado de cada uma em tabela.
#
# Uso: ./aws-lab/scripts/query_athena.sh [arquivo.sql]
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$SCRIPTS_DIR/../infra"
SQL_FILE="${1:-$SCRIPTS_DIR/consultas_gold.sql}"
tf_out() { terraform -chdir="$INFRA_DIR" output -raw "$1"; }

DB="$(tf_out glue_database_name)"
OUTPUT="$(tf_out athena_results_uri)"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

run_query() {
  local sql="$1" qid state
  qid="$(aws athena start-query-execution \
    --query-string "$sql" \
    --query-execution-context "Database=$DB" \
    --result-configuration "OutputLocation=$OUTPUT" \
    --query QueryExecutionId --output text)"
  while true; do
    state="$(aws athena get-query-execution --query-execution-id "$qid" \
      --query QueryExecution.Status.State --output text)"
    case "$state" in
      SUCCEEDED) break ;;
      FAILED | CANCELLED)
        aws athena get-query-execution --query-execution-id "$qid" \
          --query QueryExecution.Status.StateChangeReason --output text
        return 1 ;;
    esac
    sleep 2
  done
  aws athena get-query-results --query-execution-id "$qid" --output json |
    python3 -c '
import json, sys
rows = json.load(sys.stdin)["ResultSet"]["Rows"]
data = [[c.get("VarCharValue", "") for c in r["Data"]] for r in rows]
w = [max(len(r[i]) for r in data) for i in range(len(data[0]))]
for n, r in enumerate(data):
    print(" | ".join(v.ljust(w[i]) for i, v in enumerate(r)))
    if n == 0:
        print("-+-".join("-" * x for x in w))
'
}

# Remove comentarios "--" e quebra o arquivo em consultas por ';'.
python3 - "$SQL_FILE" <<'PY' | while IFS= read -r -d $'\0' q; do
import sys
txt = "\n".join(l for l in open(sys.argv[1], encoding="utf-8").read().splitlines()
                if not l.strip().startswith("--"))
for q in txt.split(";"):
    if q.strip():
        sys.stdout.write(q.strip() + "\0")
PY
  echo
  echo "=== $(echo "$q" | head -1)"
  run_query "$q"
done
