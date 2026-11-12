#!/bin/bash
# Script para executar o pipeline completo do MercadoFácil

set -e

echo "=========================================="
echo "Pipeline MercadoFácil - AWS Glue + Athena"
echo "=========================================="
echo ""

# Verificar se as variáveis de ambiente AWS estão configuradas
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "ERRO: Credenciais AWS não configuradas."
    echo "Configure as variáveis AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY e AWS_SESSION_TOKEN"
    echo ""
    echo "No Learner Lab, vá em AWS Details → Show e copie as credenciais."
    exit 1
fi

# Ler o nome do job do terraform output
cd ../infra
GLUE_JOB_NAME=$(terraform output -raw glue_job_name 2>/dev/null)
SILVER_CRAWLER_NAME=$(terraform output -raw silver_crawler_name 2>/dev/null)
GOLD_CRAWLER_NAME=$(terraform output -raw gold_crawler_name 2>/dev/null)

if [ -z "$GLUE_JOB_NAME" ]; then
    echo "ERRO: Terraform outputs não encontrados. Execute 'terraform apply' primeiro."
    exit 1
fi

echo "1. Iniciando Glue Job: $GLUE_JOB_NAME"
JOB_RUN_ID=$(aws glue start-job-run --job-name "$GLUE_JOB_NAME" --query 'JobRunId' --output text)
echo "   Job Run ID: $JOB_RUN_ID"
echo ""

echo "2. Aguardando conclusão do job (isso pode levar alguns minutos)..."
while true; do
    STATUS=$(aws glue get-job-run --job-name "$GLUE_JOB_NAME" --run-id "$JOB_RUN_ID" --query 'JobRun.JobRunState' --output text)
    echo "   Status: $STATUS"
    
    if [ "$STATUS" = "SUCCEEDED" ]; then
        echo "   ✓ Job concluído com sucesso!"
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ] || [ "$STATUS" = "TIMEOUT" ]; then
        echo "   ✗ Job falhou com status: $STATUS"
        echo "   Verifique os logs em CloudWatch: /aws-glue/jobs/error e /aws-glue/jobs/output"
        exit 1
    fi
    
    sleep 15
done
echo ""

echo "3. Executando Crawler Silver: $SILVER_CRAWLER_NAME"
aws glue start-crawler --name "$SILVER_CRAWLER_NAME"
echo "   Aguardando crawler..."
sleep 5

while true; do
    CRAWLER_STATE=$(aws glue get-crawler --name "$SILVER_CRAWLER_NAME" --query 'Crawler.State' --output text)
    if [ "$CRAWLER_STATE" = "READY" ]; then
        echo "   ✓ Crawler Silver concluído!"
        break
    fi
    sleep 10
done
echo ""

echo "4. Executando Crawler Gold: $GOLD_CRAWLER_NAME"
aws glue start-crawler --name "$GOLD_CRAWLER_NAME"
echo "   Aguardando crawler..."
sleep 5

while true; do
    CRAWLER_STATE=$(aws glue get-crawler --name "$GOLD_CRAWLER_NAME" --query 'Crawler.State' --output text)
    if [ "$CRAWLER_STATE" = "READY" ]; then
        echo "   ✓ Crawler Gold concluído!"
        break
    fi
    sleep 10
done
echo ""

echo "=========================================="
echo "Pipeline executado com sucesso!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Acesse o console do Athena: https://console.aws.amazon.com/athena/"
echo "2. Selecione o database 'mercadofacil_db'"
echo "3. Execute queries nas tabelas da camada gold:"
echo "   - analise_atrasos_avaliacoes"
echo "   - analise_cancelamentos_devolucoes"
echo "   - analise_sazonalidade"
echo "   - fato_pedidos"
echo ""
echo "Exemplo de query:"
echo "SELECT * FROM analise_atrasos_avaliacoes WHERE taxa_atraso_pct > 50 ORDER BY taxa_atraso_pct DESC LIMIT 10;"
