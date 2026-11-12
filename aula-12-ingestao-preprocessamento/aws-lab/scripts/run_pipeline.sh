#!/usr/bin/env bash
# Roda o pipeline ja provisionado pelo Terraform:
#   1) limpa silver/, gold/ e quarentena/ (Spark falha/duplica se o prefixo existe)
#   2) executa o Glue Job e espera SUCCEEDED (imprime o JobRunId)
#   3) executa o Crawler e espera terminar
#   4) lista as tabelas do Catalog
#
# Uso (credenciais do Learner Lab ja exportadas no ambiente):
#   ./aws-lab/scripts/run_pipeline.sh
set -euo pipefail

INFRA_DIR="$(cd "$(dirname "$0")/../infra" && pwd)"
tf_out() { terraform -chdir="$INFRA_DIR" output -raw "$1"; }

BUCKET="$(tf_out bucket_name)"
JOB="$(tf_out glue_job_name)"
CRAWLER="$(tf_out glue_crawler_name)"
DB="$(tf_out glue_database_name)"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo ">> Limpando camadas geradas em s3://$BUCKET"
for prefix in silver gold quarentena; do
  aws s3 rm "s3://$BUCKET/$prefix/" --recursive --quiet || true
done

echo ">> Iniciando Glue Job $JOB"
RUN_ID="$(aws glue start-job-run --job-name "$JOB" --query JobRunId --output text)"
echo "   JobRunId: $RUN_ID"

while true; do
  STATE="$(aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
    --query JobRun.JobRunState --output text)"
  echo "   $(date +%H:%M:%S) estado: $STATE"
  case "$STATE" in
    SUCCEEDED) break ;;
    FAILED | ERROR | TIMEOUT | STOPPED)
      aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
        --query JobRun.ErrorMessage --output text
      echo "   Logs: CloudWatch /aws-glue/jobs/error (stream $RUN_ID)"
      exit 1 ;;
  esac
  sleep 20
done

echo ">> Iniciando Crawler $CRAWLER"
aws glue start-crawler --name "$CRAWLER"
sleep 10
while [ "$(aws glue get-crawler --name "$CRAWLER" --query Crawler.State --output text)" != "READY" ]; do
  echo "   $(date +%H:%M:%S) crawler rodando..."
  sleep 15
done
aws glue get-crawler --name "$CRAWLER" \
  --query 'Crawler.LastCrawl.{status:Status,erro:ErrorMessage}' --output table

echo ">> Tabelas no database $DB"
aws glue get-tables --database-name "$DB" --query 'TableList[].Name' --output table

echo ">> Pipeline concluido. JobRunId: $RUN_ID"
