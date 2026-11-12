# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## O que foi feito nesta etapa

Pipeline completo de ingestão e pré-processamento construído do zero usando Terraform e PySpark na AWS:

**Infraestrutura (Terraform):**
- Bucket S3 criado via AWS CLI (terraform_data + local-exec)
- Upload automático do CSV raw e script PySpark para o S3
- Glue Database (mercadofacil_db) criado
- Glue Job (glueetl, Glue 4.0) configurado com argumentos de entrada/saída
- Dois Glue Crawlers (silver e gold) para catalogar dados processados
- Configuração completa com variáveis, outputs e uso da LabRole

**ETL (PySpark):**
- **Raw (bronze):** CSV original carregado sem modificações
- **Silver:** Dados limpos e padronizados com 13 regras de qualidade aplicadas (datas, valores monetários, textos, CPF, email, deduplicação, anonimização LGPD)
- **Gold:** 4 tabelas analíticas criadas:
  1. `analise_atrasos_avaliacoes` - fatores que explicam atraso e relação com notas
  2. `analise_cancelamentos_devolucoes` - taxa de cancelamento/devolução por categoria, canal, estado
  3. `analise_sazonalidade` - análise mês a mês (Black Friday, Natal)
  4. `fato_pedidos` - tabela de fatos granular para análises customizadas
- **Quarentena:** Registros com problemas críticos isolados com motivo documentado

**Documentação:**
- REGRAS_SILVER.md com 13 problemas de qualidade identificados e regras aplicadas
- README.md completo com guia de uso, exemplos de queries Athena
- Scripts auxiliares (setup.sh, run_pipeline.sh)

**Status:** Pipeline pronto para execução no AWS Academy Learner Lab. Terraform fmt/validate passam. Todos os requisitos estruturais do CI atendidos.

## Ferramentas efetivamente usadas

1. **Terraform (IaC):** Provisionar toda a infraestrutura na AWS de forma declarativa e reproduzível
2. **AWS S3:** Armazenar dados nas 3 camadas (raw CSV, silver/gold Parquet, quarentena)
3. **AWS Glue Job (PySpark):** Processar ETL distribuído (limpeza, transformação, agregação)
4. **AWS Glue Catalog:** Database e metadados das tabelas (gerados pelos crawlers)
5. **AWS Glue Crawlers:** Catalogar automaticamente schema dos Parquet silver/gold
6. **Amazon Athena:** Consultar dados catalogados via SQL serverless
7. **AWS CLI:** Criar/destruir bucket S3 via terraform_data (requisito do projeto)
8. **PySpark SQL:** Limpeza de dados, conversão de tipos, deduplicação, agregações
9. **CloudWatch:** Logs do Glue Job (output e error streams)

## Dificuldades encontradas

**1. Qualidade dos dados:** O CSV bruto apresenta múltiplos problemas (13 categorias identificadas) que exigiram lógica de limpeza robusta:
- Datas em 3 formatos diferentes → solução: `coalesce()` com múltiplos `to_date()`
- Valores monetários com/sem R$, vírgula/ponto → solução: `regexp_replace()` + cast
- Status em português/inglês, maiúsculas/minúsculas → solução: mapeamento de normalização
- Nulos representados de 5 formas (N/A, null, NULL, -, vazio) → solução: conversão de tipos com cast que normaliza para null Spark

**2. Requisitos específicos do Terraform:** 
- Bucket S3 via AWS CLI (não via aws_s3_bucket) → solução: terraform_data com provisioner local-exec
- Destroy deve esvaziar bucket antes → solução: provisioner when=destroy com aws s3 rb --force
- Upload de arquivos condicionais → solução: triggers_replace com filemd5() para detectar mudanças

**3. Anonimização LGPD:** Decidir o que fazer com dados pessoais (nome, email, CPF, comentários) → solução: hash SHA-256 mantendo capacidade de análise agregada por cliente, remoção completa dos originais

**4. Quarentena vs descarte:** Registros inválidos não podem ser descartados silenciosamente → solução: dataframe separado com campo motivo_quarentena, salvo em pasta dedicada para revisão

**5. Deduplicação:** Identificar critério correto (item_id) e estratégia de desempate (data_pedido mais antiga) → solução: window function com row_number()

## Próxima etapa (Aula 13)

A partir da camada gold, o grupo planeja:

1. **Análise Exploratória:** Queries Athena para entender padrões nos dados (distribuição geográfica de atrasos, sazonalidade, correlações)

2. **Visualização:** Conectar Athena a ferramenta de BI (QuickSight, Metabase ou similar) para criar dashboards executivos

3. **Modelagem Preditiva:** Considerar modelos de ML para:
   - Prever risco de atraso (regressão ou classificação)
   - Identificar fatores de cancelamento/devolução (classificação)
   - Segmentação de clientes por comportamento de compra (clustering)

4. **Recomendações de Negócio:** Baseado nas análises, propor ações concretas:
   - Reforçar logística em regiões/épocas críticas
   - Ajustar prazos estimados por transportadora/região
   - Identificar categorias/canais problemáticos para intervenção

5. **Otimização do Pipeline:** Se houver tempo, considerar:
   - Particionamento das tabelas gold por ano/mês para melhor performance
   - Incremental load (job-bookmark) para processar apenas dados novos
   - Testes automatizados de qualidade de dados (Great Expectations ou similar)
