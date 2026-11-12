#!/usr/bin/env bash
# Consulta a gold no Athena e imprime o resultado.
#
# Uso: ./consultar_athena.sh "SELECT * FROM atraso_por_recorte LIMIT 10"
set -euo pipefail

CONSULTA="${1:-SELECT estado, categoria, taxa_atraso_pct, nota_media FROM atraso_por_recorte ORDER BY taxa_atraso_pct DESC LIMIT 10}"

cd "$(dirname "$0")/../infra"
BUCKET=$(terraform output -raw bucket)
BANCO=$(terraform output -raw glue_database)

ID=$(aws athena start-query-execution \
      --query-string "$CONSULTA" \
      --query-execution-context "Database=${BANCO}" \
      --result-configuration "OutputLocation=s3://${BUCKET}/athena-resultados/" \
      --query QueryExecutionId --output text)

while true; do
  ESTADO=$(aws athena get-query-execution --query-execution-id "$ID" \
            --query 'QueryExecution.Status.State' --output text)
  case "$ESTADO" in
    SUCCEEDED) break ;;
    FAILED|CANCELLED)
      aws athena get-query-execution --query-execution-id "$ID" \
        --query 'QueryExecution.Status.StateChangeReason' --output text
      exit 1 ;;
  esac
  sleep 3
done

aws athena get-query-results --query-execution-id "$ID" \
  --query 'ResultSet.Rows[].Data[].VarCharValue' --output table
