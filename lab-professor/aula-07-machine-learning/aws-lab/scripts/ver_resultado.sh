#!/usr/bin/env bash
# =============================================================================
# ver_resultado.sh — DEMO DO PROFESSOR: mostra os resultados do job de previsão
# de direção de ações gravados no S3.
#
# Le o BUCKET a partir dos outputs do Terraform (../infra) OU da variavel de
# ambiente BUCKET, lista e imprime o conteudo de DOIS prefixos de saida:
#   - output/metrics/      -> metricas dos modelos (modelo,metrica,valor)
#   - output/predictions/  -> amostra de previsoes (features,label,prediction)
#
# Uso (dentro de aws-lab/scripts):
#   ./ver_resultado.sh
# Ou:
#   BUCKET=meu-bucket ./ver_resultado.sh
# =============================================================================
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra"

# Descobre o bucket (Terraform output ou env var).
BUCKET="${BUCKET:-$(terraform -chdir="$INFRA_DIR" output -raw bucket_nome 2>/dev/null || true)}"

if [[ -z "$BUCKET" ]]; then
  echo "ERRO: nao consegui obter o BUCKET." >&2
  echo "      Rode 'terraform apply' em ../infra ou defina BUCKET no ambiente." >&2
  exit 1
fi

echo "BUCKET = $BUCKET"

# Diretorio temporario para baixar os arquivos de saida; limpo ao sair.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# ---------------------------------------------------------------------------
# 1) Metricas dos modelos (comparacao LogisticRegression x RandomForest).
# ---------------------------------------------------------------------------
echo "=== Metricas (modelo,metrica,valor) ==="
echo "\$ aws s3 ls s3://$BUCKET/output/metrics/"
aws s3 ls "s3://$BUCKET/output/metrics/"

echo "\$ aws s3 cp --recursive s3://$BUCKET/output/metrics/ $TMP_DIR/metrics"
aws s3 cp --recursive "s3://$BUCKET/output/metrics/" "$TMP_DIR/metrics"

cat "$TMP_DIR/metrics"/part-* 2>/dev/null || {
  echo "(nenhum arquivo part-* encontrado em output/metrics/ — verifique se o job terminou com SUCCEEDED)" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# 2) Amostra de previsoes (modelo Random Forest).
# ---------------------------------------------------------------------------
echo "=== Amostra de previsoes (features,label,prediction) ==="
echo "\$ aws s3 ls s3://$BUCKET/output/predictions/"
aws s3 ls "s3://$BUCKET/output/predictions/"

echo "\$ aws s3 cp --recursive s3://$BUCKET/output/predictions/ $TMP_DIR/predictions"
aws s3 cp --recursive "s3://$BUCKET/output/predictions/" "$TMP_DIR/predictions"

cat "$TMP_DIR/predictions"/part-* 2>/dev/null || {
  echo "(nenhum arquivo part-* encontrado em output/predictions/ — verifique se o job terminou com SUCCEEDED)" >&2
  exit 1
}
