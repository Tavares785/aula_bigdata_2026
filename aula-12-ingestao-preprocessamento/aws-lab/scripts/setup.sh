#!/bin/bash
# =============================================================================
# Setup Script - MercadoFácil Pipeline
# =============================================================================
# Este script ajuda a configurar as credenciais AWS e gerar o terraform.tfvars
# =============================================================================

set -e

echo "======================================================================"
echo "  Setup - Pipeline MercadoFácil"
echo "======================================================================"
echo ""

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI não encontrado. Instale: https://aws.amazon.com/cli/"
    exit 1
fi

# Verificar credenciais AWS
echo "1. Verificando credenciais AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo ""
    echo "❌ Credenciais AWS inválidas ou não configuradas."
    echo ""
    echo "No AWS Academy Learner Lab:"
    echo "  1. Clique em 'AWS Details'"
    echo "  2. Clique em 'Show' ao lado de AWS CLI"
    echo "  3. Copie e cole os comandos de export"
    echo ""
    echo "Exemplo:"
    echo "  export AWS_ACCESS_KEY_ID=..."
    echo "  export AWS_SECRET_ACCESS_KEY=..."
    echo "  export AWS_SESSION_TOKEN=..."
    echo ""
    exit 1
fi

echo "✅ Credenciais AWS válidas"
echo ""

# Obter ARN da LabRole
echo "2. Obtendo ARN da LabRole..."
LAB_ROLE_ARN=$(aws iam get-role --role-name LabRole --query Role.Arn --output text 2>/dev/null || echo "")

if [ -z "$LAB_ROLE_ARN" ]; then
    echo "❌ Não foi possível obter o ARN da LabRole"
    echo "   Verifique se você está no AWS Academy Learner Lab"
    exit 1
fi

echo "✅ LabRole ARN: $LAB_ROLE_ARN"
echo ""

# Solicitar nome do bucket
echo "3. Configurando nome do bucket S3..."
echo "   Nota: O nome do bucket deve ser globalmente único"
echo "   Sugestão: mercadofacil-bigdata-grupo-<ID>"
echo ""
read -p "Digite o nome do bucket S3: " BUCKET_NAME

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Nome do bucket não pode ser vazio"
    exit 1
fi

echo ""

# Gerar terraform.tfvars
TFVARS_FILE="../infra/terraform.tfvars"

echo "4. Gerando $TFVARS_FILE..."

cat > "$TFVARS_FILE" <<EOF
# =============================================================================
# Terraform Variables - MercadoFácil Pipeline
# =============================================================================
# Gerado automaticamente por setup.sh em $(date)
# =============================================================================

bucket_name   = "$BUCKET_NAME"
lab_role_arn  = "$LAB_ROLE_ARN"
project_name  = "mercadofacil-bigdata"
glue_version  = "4.0"
EOF

echo "✅ Arquivo terraform.tfvars criado"
echo ""

# Inicializar Terraform
echo "5. Inicializando Terraform..."
cd ../infra

if terraform init; then
    echo "✅ Terraform inicializado"
else
    echo "❌ Falha ao inicializar Terraform"
    exit 1
fi

cd ../scripts

echo ""
echo "======================================================================"
echo "  ✅ SETUP CONCLUÍDO COM SUCESSO!"
echo "======================================================================"
echo ""
echo "Próximos passos:"
echo ""
echo "  1. Revisar a infraestrutura:"
echo "     cd ../infra && terraform plan"
echo ""
echo "  2. Provisionar recursos:"
echo "     terraform apply"
echo ""
echo "  3. Executar o pipeline:"
echo "     cd ../scripts && bash run_pipeline.sh"
echo ""
echo "======================================================================"
