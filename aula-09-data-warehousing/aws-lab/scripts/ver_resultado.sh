#!/usr/bin/env bash
# =============================================================================
# ver_resultado.sh — Mostra os resultados do Job_DW gravados no S3.
#
# Le o BUCKET dos outputs do Terraform (../infra) OU da env var BUCKET e
# imprime a camada lake (Parquet particionado) e os 3 resultados das queries:
#   - output/revenue_by_region/        -> receita total por regiao
#   - output/top_products/             -> top-N produtos
#   - output/regions_above_threshold/  -> regioes acima do threshold (HAVING)
#
# Uso (dentro de aws-lab/scripts):  ./ver_resultado.sh
# =============================================================================
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra"

BUCKET="${BUCKET:-$(terraform -chdir="$INFRA_DIR" output -raw bucket_nome 2>/dev/null || true)}"

if [[ -z "$BUCKET" ]]; then
  echo "ERRO: nao consegui obter o BUCKET." >&2
  echo "      Rode 'terraform apply' em ../infra ou defina BUCKET no ambiente." >&2
  exit 1
fi

echo "BUCKET = $BUCKET"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "=== Camada lake (Parquet particionado por region) ==="
echo "\$ aws s3 ls --recursive s3://$BUCKET/output/lake/sales/"
aws s3 ls --recursive "s3://$BUCKET/output/lake/sales/" | awk '{print $4}' | grep -v '_SUCCESS'

for consulta in revenue_by_region top_products regions_above_threshold; do
  echo "=== $consulta ==="
  aws s3 cp --recursive --quiet "s3://$BUCKET/output/$consulta/" "$TMP_DIR/$consulta"
  cat "$TMP_DIR/$consulta"/part-* 2>/dev/null || {
    echo "(nenhum part-* em output/$consulta/ — o job terminou com SUCCEEDED?)" >&2
    exit 1
  }
done
