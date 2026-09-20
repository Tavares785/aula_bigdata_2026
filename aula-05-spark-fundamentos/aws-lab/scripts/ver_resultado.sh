#!/usr/bin/env bash
# =============================================================================
# ver_resultado.sh — Mostra o resultado do word count gravado no S3.
#
# Le o BUCKET a partir dos outputs do Terraform (../infra) OU da variavel de
# ambiente BUCKET, lista os arquivos de saida e imprime o conteudo (wordcount).
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

# Lista os arquivos de saida (o Spark grava part-00000, _SUCCESS, etc.).
echo "\$ aws s3 ls s3://$BUCKET/output/wordcount/"
aws s3 ls "s3://$BUCKET/output/wordcount/"

# Imprime o conteudo dos arquivos de saida diretamente no terminal.
# Baixamos para um diretorio temporario e fazemos cat dos "part-*".
echo "=== Conteudo do word count (palavra,contagem) ==="
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "\$ aws s3 cp --recursive s3://$BUCKET/output/wordcount/ $TMP_DIR"
aws s3 cp --recursive "s3://$BUCKET/output/wordcount/" "$TMP_DIR"

# Concatena todos os arquivos de particao (part-*).
cat "$TMP_DIR"/part-* 2>/dev/null || {
  echo "(nenhum arquivo part-* encontrado — verifique se o job terminou com SUCCEEDED)" >&2
  exit 1
}
