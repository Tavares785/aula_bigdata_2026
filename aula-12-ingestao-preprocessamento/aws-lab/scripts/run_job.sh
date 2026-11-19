#!/bin/bash
# Script para rodar o Glue Job e acompanhar o status

BUCKET="mercadofacil-grupo3"
JOB_NAME="mercadofacil-etl"

echo "=== Iniciando Glue Job: $JOB_NAME ==="
RUN_ID=$(aws glue start-job-run --job-name "$JOB_NAME" --query 'JobRunId' --output text)
echo "JobRunId: $RUN_ID"

echo "=== Aguardando conclusão... ==="
while true; do
  STATUS=$(aws glue get-job-run --job-name "$JOB_NAME" --run-id "$RUN_ID" --query 'JobRun.JobRunState' --output text)
  echo "Status: $STATUS"
  if [[ "$STATUS" == "SUCCEEDED" || "$STATUS" == "FAILED" || "$STATUS" == "STOPPED" ]]; then
    break
  fi
  sleep 30
done

echo "=== Job finalizado com status: $STATUS ==="

if [[ "$STATUS" == "SUCCEEDED" ]]; then
  echo ""
  echo "=== Iniciando Crawler ==="
  aws glue start-crawler --name "mercadofacil-crawler"
  echo "Crawler iniciado. Aguarde ~1 min e consulte no Athena."
fi
