#!/usr/bin/env bash
# Roda o Glue Job, depois o Crawler, e consulta a gold no Athena.
# Uso: ./run_pipeline.sh (depois do terraform apply em ../infra)
set -euo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../infra" && pwd)"
SQL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/consultas"
export AWS_DEFAULT_REGION=us-east-1

saida() { terraform -chdir="$INFRA_DIR" output -raw "$1"; }

JOB="$(saida glue_job_nome)"
CRAWLER="$(saida glue_crawler_nome)"
DATABASE="$(saida glue_database_nome)"
RESULTADOS="$(saida athena_resultados_uri)"

RUN_ID="$(aws glue start-job-run --job-name "$JOB" --query JobRunId --output text)"
echo "JobRunId: $RUN_ID"
while :; do
  ESTADO="$(aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
    --query JobRun.JobRunState --output text)"
  echo "Glue Job: $ESTADO"
  case "$ESTADO" in
    SUCCEEDED) break ;;
    FAILED | ERROR | TIMEOUT | STOPPED)
      aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
        --query JobRun.ErrorMessage --output text >&2
      exit 1
      ;;
  esac
  sleep 20
done

aws glue start-crawler --name "$CRAWLER"
while :; do
  ESTADO="$(aws glue get-crawler --name "$CRAWLER" --query Crawler.State --output text)"
  echo "Crawler: $ESTADO"
  [ "$ESTADO" = "READY" ] && break
  sleep 15
done
aws glue get-crawler --name "$CRAWLER" --query Crawler.LastCrawl.Status --output text

for ARQUIVO in "$SQL_DIR"/*.sql; do
  echo; echo "=== $(basename "$ARQUIVO")"
  QUERY_ID="$(aws athena start-query-execution \
    --query-string "$(cat "$ARQUIVO")" \
    --query-execution-context "Database=$DATABASE" \
    --result-configuration "OutputLocation=$RESULTADOS" \
    --query QueryExecutionId --output text)"
  while :; do
    ESTADO="$(aws athena get-query-execution --query-execution-id "$QUERY_ID" \
      --query QueryExecution.Status.State --output text)"
    case "$ESTADO" in
      SUCCEEDED) break ;;
      FAILED | CANCELLED)
        aws athena get-query-execution --query-execution-id "$QUERY_ID" \
          --query QueryExecution.Status.StateChangeReason --output text >&2
        exit 1
        ;;
    esac
    sleep 2
  done
  aws athena get-query-results --query-execution-id "$QUERY_ID" \
    --query 'ResultSet.Rows[].Data[].VarCharValue' --output text
done
