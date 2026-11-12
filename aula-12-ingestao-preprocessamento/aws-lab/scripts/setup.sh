#!/bin/bash
# Script de setup inicial - obter ARN da LabRole e configurar terraform.tfvars

set -e

echo "=========================================="
echo "Setup MercadoFácil AWS Lab"
echo "=========================================="
echo ""

# Verificar credenciais AWS
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "ERRO: Credenciais AWS não configuradas."
    echo ""
    echo "Configure as variáveis de ambiente:"
    echo "  export AWS_ACCESS_KEY_ID=..."
    echo "  export AWS_SECRET_ACCESS_KEY=..."
    echo "  export AWS_SESSION_TOKEN=..."
    echo ""
    echo "No Learner Lab, vá em AWS Details → Show e copie os comandos."
    exit 1
fi

echo "1. Obtendo ARN da LabRole..."
LAB_ROLE_ARN=$(aws iam get-role --role-name LabRole --query 'Role.Arn' --output text)
echo "   LabRole ARN: $LAB_ROLE_ARN"
echo ""

echo "2. Gerando terraform.tfvars..."
cd ../infra

# Solicitar nome do bucket ao usuário
read -p "Digite um nome ÚNICO para o bucket S3 (ex: mercadofacil-bigdata-grupo01): " BUCKET_NAME

cat > terraform.tfvars <<EOF
# Configuração do projeto MercadoFácil
# Gerado automaticamente por setup.sh

bucket_name  = "$BUCKET_NAME"
lab_role_arn = "$LAB_ROLE_ARN"
project_name = "mercadofacil-bigdata"
EOF

echo "   ✓ terraform.tfvars criado!"
echo ""

echo "3. Inicializando Terraform..."
terraform init
echo ""

echo "4. Validando configuração Terraform..."
terraform validate
echo ""

echo "5. Formatando arquivos Terraform..."
terraform fmt
echo ""

echo "=========================================="
echo "Setup concluído!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Execute: terraform plan (revisar as mudanças)"
echo "2. Execute: terraform apply (provisionar infraestrutura)"
echo "3. Execute: ../scripts/run_pipeline.sh (executar ETL)"
