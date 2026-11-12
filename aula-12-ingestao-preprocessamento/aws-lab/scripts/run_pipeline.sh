#!/bin/bash
# =============================================================================
# Run Pipeline Script - MercadoFácil
# =============================================================================
# Executa o job Glue e os crawlers automaticamente
# =============================================================================

set -e

echo "======================================================================"
echo "  Executando Pipeline - MercadoFácil"
echo "======================================================================"
echo ""

# Verificar credenciais AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Credenciais AWS inválidas. Execute setup.sh primeiro."
    exit 1
fi

cd ../infra

# Verificar se o Terraform foi aplicado
if [ ! -f "terraform.tfstate" ]; then
    echo "❌ Infraestrutura não provisionada. Execute 'terraform apply' primeiro."
    exit 1
fi

# Obter outputs do Terraform
echo "1. Obtendo informações da infraestrutura..."
JOB_NAME=$(terraform output -raw glue_job_name)
SILVER_CRAWLER=$(terraform output -raw silver_crawler_name)
GOLD_CRAWLER=$(terraform output -raw gold_crawler_name)

echo "   Job: $JOB_NAME"
echo "   Silver Crawler: $SILVER_CRAWLER"
echo "   Gold Crawler: $GOLD_CRAWLER"
echo ""

# Iniciar Glue Job
echo "2. Iniciando Glue Job..."
JOB_RUN_ID=$(aws glue start-job-run --job-name "$JOB_NAME" --query 'JobRunId' --output text)
echo "   Job Run ID: $JOB_RUN_ID"
echo ""

# Aguardar conclusão do job
echo "3. Aguardando conclusão do job (pode levar alguns minutos)..."
while true; do
    STATUS=$(aws glue get-job-run --job-name "$JOB_NAME" --run-id "$JOB_RUN_ID" --query 'JobRun.JobRunState' --output text)
    
    if [ "$STATUS" == "SUCCEEDED" ]; then
        echo "   ✅ Job concluído com sucesso!"
        break
    elif [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "STOPPED" ] || [ "$STATUS" == "ERROR" ]; then
        echo "   ❌ Job falhou com status: $STATUS"
        echo ""
        echo "Verifique os logs no CloudWatch:"
        echo "  - /aws-glue/jobs/output"
        echo "  - /aws-glue/jobs/error"
        exit 1
    else
        echo "   Status: $STATUS (aguardando...)"
        sleep 30
    fi
done
echo ""

# Executar crawler silver
echo "4. Executando Crawler Silver..."
aws glue start-crawler --name "$SILVER_CRAWLER" || true
echo "   Crawler iniciado"
echo ""

# Aguardar conclusão do crawler silver
echo "5. Aguardando conclusão do Crawler Silver..."
sleep 10
while true; do
    STATUS=$(aws glue get-crawler --name "$SILVER_CRAWLER" --query 'Crawler.State' --output text)
    
    if [ "$STATUS" == "READY" ]; then
        echo "   ✅ Crawler Silver concluído!"
        break
    else
        echo "   Status: $STATUS (aguardando...)"
        sleep 10
    fi
done
echo ""

# Executar crawler gold
echo "6. Executando Crawler Gold..."
aws glue start-crawler --name "$GOLD_CRAWLER" || true
echo "   Crawler iniciado"
echo ""

# Aguardar conclusão do crawler gold
echo "7. Aguardando conclusão do Crawler Gold..."
sleep 10
while true; do
    STATUS=$(aws glue get-crawler --name "$GOLD_CRAWLER" --query 'Crawler.State' --output text)
    
    if [ "$STATUS" == "READY" ]; then
        echo "   ✅ Crawler Gold concluído!"
        break
    else
        echo "   Status: $STATUS (aguardando...)"
        sleep 10
    fi
done
echo ""

echo "======================================================================"
echo "  ✅ PIPELINE EXECUTADO COM SUCESSO!"
echo "======================================================================"
echo ""
echo "As tabelas estão catalogadas no Glue Database: mercadofacil_db"
echo ""
echo "Próximo passo: Consultar dados no Athena"
echo ""
echo "Exemplos de queries:"
echo ""
echo "  -- Análise de atrasos por região"
echo "  SELECT estado, ROUND(AVG(taxa_atraso_pct), 2) AS taxa_atraso"
echo "  FROM mercadofacil_db.analise_atrasos_avaliacoes"
echo "  GROUP BY estado"
echo "  ORDER BY taxa_atraso DESC;"
echo ""
echo "  -- Sazonalidade (Black Friday e Natal)"
echo "  SELECT mes_nome, SUM(total_pedidos) AS pedidos"
echo "  FROM mercadofacil_db.analise_sazonalidade"
echo "  WHERE mes IN (11, 12)"
echo "  GROUP BY mes_nome;"
echo ""
echo "======================================================================"
