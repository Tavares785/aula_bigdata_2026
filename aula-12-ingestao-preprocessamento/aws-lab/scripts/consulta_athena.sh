#!/usr/bin/env bash
# Consulta a gold no Athena via CLI.
# Uso: ./consulta_athena.sh ["SQL"]   (rode depois do crawler)
set -euo pipefail

cd "$(dirname "$0")/../infra"
DB=$(terraform output -raw glue_database_name)
BUCKET=$(terraform output -raw bucket_name)
SQL=${1:-"SELECT faixa_atraso, itens_avaliados, nota_media, pct_nota_baixa FROM nota_por_faixa_atraso ORDER BY faixa_atraso"}

QID=$(aws athena start-query-execution \
  --query-string "$SQL" \
  --query-execution-context "Database=${DB}" \
  --result-configuration "OutputLocation=s3://${BUCKET}/athena-results/" \
  --query QueryExecutionId --output text)

while true; do
  STATE=$(aws athena get-query-execution --query-execution-id "$QID" \
    --query QueryExecution.Status.State --output text)
  case "$STATE" in
    SUCCEEDED) break ;;
    FAILED|CANCELLED)
      aws athena get-query-execution --query-execution-id "$QID" \
        --query QueryExecution.Status.StateChangeReason --output text >&2
      exit 1 ;;
  esac
  sleep 2
done

aws athena get-query-results --query-execution-id "$QID" --output text \
  --query 'ResultSet.Rows[*].Data[*].VarCharValue'
