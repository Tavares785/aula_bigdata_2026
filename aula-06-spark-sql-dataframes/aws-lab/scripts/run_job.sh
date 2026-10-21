#!/usr/bin/env bash
# =============================================================================
# run_job.sh — Dispara o Glue Job de DataFrames/Spark SQL (TOP-N de clientes por
# gasto) e acompanha o resultado.
#
# O que este script faz:
#   1. Descobre BUCKET, GLUE_JOB e ROLE_ARN a partir dos outputs do Terraform
#      (../infra) OU das variaveis de ambiente BUCKET/GLUE_JOB/ROLE_ARN.
#   2. RE-ENVIA o script PySpark e os 2 CSVs de entrada para o S3 (para refletir
#      as edicoes do aluno feitas DEPOIS do terraform apply).
#   3. LIMPA a saida anterior (o write no S3 falha/duplica se ja existir).
#   4. Dispara o job (aws glue start-job-run) e captura o JobRunId.
#   5. Faz polling do estado ate SUCCEEDED ou FAILED.
#
# Uso (dentro de aws-lab/scripts):
#   ./run_job.sh
# Ou informando manualmente:
#   BUCKET=meu-bucket GLUE_JOB=job-aula06-topn-clientes ./run_job.sh
#
# Requer: AWS CLI v2 configurado com as credenciais do Learner Lab (us-east-1).
# =============================================================================
set -euo pipefail

# Regiao fixa do Learner Lab.
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# Diretorios (relativos a este script), independente de onde ele foi chamado.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra"
JOB_FILE="$SCRIPT_DIR/../job/dataframe_job.py"
PEDIDOS_FILE="$SCRIPT_DIR/../data/pedidos.csv"
CLIENTES_FILE="$SCRIPT_DIR/../data/clientes.csv"

# Imprime e executa um comando (prefixo "$ " para ficar visivel nos logs).
run() {
  echo "\$ $*"
  "$@"
}

# ---------------------------------------------------------------------------
# 1. Descobrir BUCKET, GLUE_JOB e ROLE_ARN.
#    Preferimos os outputs do Terraform; se falharem, usamos as env vars.
#    (ROLE_ARN NAO e usado no start-job-run do Glue — a role ja esta no Job —
#     mas mostramos no log para conferencia.)
# ---------------------------------------------------------------------------
BUCKET="${BUCKET:-$(terraform -chdir="$INFRA_DIR" output -raw bucket_nome 2>/dev/null || true)}"
GLUE_JOB="${GLUE_JOB:-$(terraform -chdir="$INFRA_DIR" output -raw glue_job_nome 2>/dev/null || true)}"
ROLE_ARN="${ROLE_ARN:-$(terraform -chdir="$INFRA_DIR" output -raw labrole_arn 2>/dev/null || true)}"

if [[ -z "$BUCKET" || -z "$GLUE_JOB" ]]; then
  echo "ERRO: nao consegui obter BUCKET/GLUE_JOB." >&2
  echo "      Rode 'terraform apply' em ../infra ou defina as variaveis de ambiente" >&2
  echo "      BUCKET e GLUE_JOB antes de executar este script." >&2
  exit 1
fi

echo "BUCKET   = $BUCKET"
echo "GLUE_JOB = $GLUE_JOB"
echo "ROLE_ARN = ${ROLE_ARN:-(nao informado — ok, a role ja esta no Job)}"

# ---------------------------------------------------------------------------
# 2. RE-ENVIAR o script PySpark e os 2 CSVs de entrada para o S3.
#    Isso garante que o job rode a versao ATUAL do dataframe_job.py (com os
#    TODOs ja resolvidos pelo aluno), mesmo sem um novo terraform apply.
# ---------------------------------------------------------------------------
run aws s3 cp "$JOB_FILE" "s3://$BUCKET/scripts/dataframe_job.py"
run aws s3 cp "$PEDIDOS_FILE" "s3://$BUCKET/input/pedidos.csv"
run aws s3 cp "$CLIENTES_FILE" "s3://$BUCKET/input/clientes.csv"

# ---------------------------------------------------------------------------
# 3. LIMPAR a saida anterior.
#    A escrita no S3 (write CSV) FALHA/duplica se o prefixo ja existir. Removemos
#    a pasta output/top_clientes antes de rodar de novo (|| true: ok se nao existir).
# ---------------------------------------------------------------------------
run aws s3 rm "s3://$BUCKET/output/top_clientes" --recursive || true

# ---------------------------------------------------------------------------
# 4. Disparar o Glue Job e capturar o JobRunId.
# ---------------------------------------------------------------------------
echo "\$ aws glue start-job-run --job-name $GLUE_JOB ..."
RUN_ID="$(aws glue start-job-run \
  --job-name "$GLUE_JOB" \
  --region us-east-1 \
  --query 'JobRunId' --output text)"

echo "RUN_ID = $RUN_ID"

# ---------------------------------------------------------------------------
# 5. Polling do estado ate terminar.
#    Estados do Glue: STARTING -> RUNNING -> SUCCEEDED / FAILED / TIMEOUT / STOPPED.
# ---------------------------------------------------------------------------
echo "Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)..."
while true; do
  ESTADO="$(aws glue get-job-run \
    --job-name "$GLUE_JOB" \
    --run-id "$RUN_ID" \
    --region us-east-1 \
    --query 'JobRun.JobRunState' --output text)"
  echo "estado: $ESTADO"
  case "$ESTADO" in
    SUCCEEDED)
      echo "Job concluido com SUCESSO."
      echo "Veja o resultado com: ./ver_resultado.sh"
      exit 0
      ;;
    FAILED | TIMEOUT | STOPPED)
      echo "Job terminou com estado: $ESTADO." >&2
      # Mostra a mensagem de erro que o Glue registrou para este run (se houver).
      ERRO_MSG="$(aws glue get-job-run \
        --job-name "$GLUE_JOB" \
        --run-id "$RUN_ID" \
        --region us-east-1 \
        --query 'JobRun.ErrorMessage' --output text 2>/dev/null || true)"
      if [[ -n "$ERRO_MSG" && "$ERRO_MSG" != "None" ]]; then
        echo "ErrorMessage: $ERRO_MSG" >&2
      fi
      echo "Veja os logs do driver no CloudWatch (grupos /aws-glue/jobs/output e" >&2
      echo "/aws-glue/jobs/error) ou os artefatos em: s3://$BUCKET/logs/." >&2
      exit 1
      ;;
    STARTING | RUNNING | WAITING)
      sleep 15
      ;;
    *)
      # Estado inesperado: aguarda mais um pouco antes de reconsultar.
      sleep 15
      ;;
  esac
done
