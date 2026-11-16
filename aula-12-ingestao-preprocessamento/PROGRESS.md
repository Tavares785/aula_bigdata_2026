# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

## O que foi feito nesta etapa

Pipeline medalhão completo, provisionado com Terraform no Learner Lab e executado de ponta a ponta:
raw (CSV intacto no S3) → Glue Job PySpark → silver (9.362 linhas, Parquet tipado, sem PII) +
quarentena (638 linhas com motivo) → gold (4 tabelas) → Glue Crawler → consultas no Athena.
Glue Job `SUCCEEDED` (JobRunId `jr_7a047dddba624ffb3f68e5b4b75567054818eb4c0e33c3737d772b384eed890d`),
Crawler `SUCCEEDED` e consultas na gold respondidas. Ao final, `terraform destroy` removeu os 6 recursos.
Nada ficou pendente na etapa; as 15 regras de limpeza estão em `aws-lab/REGRAS_SILVER.md`.

## Ferramentas efetivamente usadas

- **Terraform** (provider aws 5.31.0): bucket via `terraform_data` + AWS CLI, upload do CSV e do ETL, Glue database, Job e Crawler.
- **S3**: camadas raw, silver, quarentena, gold e resultados do Athena.
- **Glue Job (PySpark, Glue 4.0)**: limpeza, tipagem, deduplicação, quarentena e agregações gold.
- **Glue Crawler / Data Catalog**: cataloga silver, quarentena e gold.
- **Athena**: consultas SQL sobre a gold (atraso × nota, cancelamento, vendas mensais).

## Dificuldades encontradas

- A base é suja de propósito (duplicatas, 3 formatos de data, moeda em texto, categorias truncadas, `ontem`, valores incoerentes): analisamos o CSV antes e transformamos cada problema em regra.
- O Learner Lab bloqueia `aws_s3_bucket` e IAM: criamos o bucket por CLI e usamos a LabRole.
- Rede lenta: o download do provider e o upload do CSV demoraram (timeouts), resolvido repetindo o `terraform init`.
- Sem Java local, o PySpark foi validado direto no Glue (passou na primeira execução).

## Próxima etapa (Aula 13)

Usar a gold para investigar os fatores do atraso e prever atraso/cancelamento com modelos de ML
(por exemplo, regressão logística e árvores), medindo F1 e AUC, além de avaliar a relação atraso × nota.
