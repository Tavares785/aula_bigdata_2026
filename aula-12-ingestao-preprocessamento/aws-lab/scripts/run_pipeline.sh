#!/usr/bin/env bash
# Executa o Glue Job e o Crawler e espera terminar.
# Uso: ./run_pipeline.sh   (rode dentro de aws-lab/infra depois do terraform apply)
set -euo pipefail

cd "$(dirname "$0")/../infra"
JOB=$(terraform output -raw glue_job_name)
CRAWLER=$(terraform output -raw glue_crawler_name)
BUCKET=$(terraform output -raw bucket_name)

# Spark falha ou duplica se o prefixo de saida ja existe: limpa antes.
for p in silver gold quarantine; do
  aws s3 rm "s3://${BUCKET}/${p}/" --recursive --only-show-errors
done

RUN_ID=$(aws glue start-job-run --job-name "$JOB" --query JobRunId --output text)
echo "JobRunId: ${RUN_ID}"

while true; do
  STATE=$(aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
    --query JobRun.JobRunState --output text)
  echo "Job: ${STATE}"
  case "$STATE" in
    SUCCEEDED) break ;;
    FAILED|ERROR|TIMEOUT|STOPPED)
      echo "Job terminou com ${STATE}. Veja /aws-glue/jobs/error no CloudWatch." >&2
      exit 1 ;;
  esac
  sleep 20
done

aws glue start-crawler --name "$CRAWLER"
while true; do
  STATE=$(aws glue get-crawler --name "$CRAWLER" --query Crawler.State --output text)
  echo "Crawler: ${STATE}"
  [ "$STATE" = "READY" ] && break
  sleep 15
done
echo "Pronto. Tabelas no banco $(terraform output -raw glue_database_name)."
