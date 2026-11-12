#!/usr/bin/env bash
# Provisiona, roda o Glue Job e o Crawler, e espera cada etapa terminar.
#
# Esperar importa: `start-job-run` devolve sucesso quando o Glue ACEITA o
# job, nao quando ele termina bem. Sem a espera, um job que falhou
# passaria por execucao bem-sucedida.
set -euo pipefail

cd "$(dirname "$0")/../infra"

echo "==> apply"
terraform init -input=false
terraform apply -auto-approve -input=false

BUCKET=$(terraform output -raw bucket)
JOB=$(terraform output -raw glue_job)
CRAWLER=$(terraform output -raw glue_crawler)

# A escrita do Spark no S3 DUPLICA quando o prefixo ja tem dado de uma
# execucao anterior. Limpar antes e mais barato que descobrir depois.
echo "==> limpando saidas anteriores"
aws s3 rm "s3://${BUCKET}/silver/" --recursive || true
aws s3 rm "s3://${BUCKET}/gold/" --recursive || true
aws s3 rm "s3://${BUCKET}/quarentena/" --recursive || true

echo "==> Glue Job"
RUN=$(aws glue start-job-run --job-name "$JOB" --query JobRunId --output text)
echo "JobRunId: $RUN"

while true; do
  ESTADO=$(aws glue get-job-run --job-name "$JOB" --run-id "$RUN" \
            --query 'JobRun.JobRunState' --output text)
  echo "  $ESTADO"
  case "$ESTADO" in
    SUCCEEDED) break ;;
    FAILED|ERROR|TIMEOUT|STOPPED)
      echo "job terminou em $ESTADO. Logs: /aws-glue/jobs/error no CloudWatch"
      exit 1 ;;
  esac
  sleep 20
done

echo "==> Crawler"
aws glue start-crawler --name "$CRAWLER"

while true; do
  ESTADO=$(aws glue get-crawler --name "$CRAWLER" --query 'Crawler.State' --output text)
  echo "  $ESTADO"
  [ "$ESTADO" = "READY" ] && break
  sleep 20
done

echo "pronto. JobRunId=$RUN"
