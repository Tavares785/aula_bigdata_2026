# Aula 09 — Data Warehousing com Spark SQL na AWS (AWS Glue)

Extensão do TF da aula-09: as mesmas queries de `src/warehouse_queries.py`
rodam num Spark gerenciado (**AWS Glue**), provisionado com **Terraform** no
**AWS Academy Learner Lab**. Segue o mesmo padrão do `aws-lab` da aula-07
(bucket via AWS CLI por causa da SCP, Glue Job com a `LabRole`).

## Arquitetura

```
 S3 input/sample_sales.csv  (raw)
        |
        v
 AWS Glue Job (glueetl, 2x G.1X) --extra-py-files warehouse_queries.py
        |  1. grava output/lake/sales/region=<...>/  (Parquet, curated)
        |  2. view "sales" + 3 queries SQL (GROUP BY, LIMIT, HAVING)
        v
 S3 output/revenue_by_region | output/top_products | output/regions_above_threshold
 CloudWatch /aws-glue/jobs/output (prints do driver)
```

## Passo a passo

```bash
aws sts get-caller-identity                     # credenciais do Learner Lab ativas
cd infra
cp terraform.tfvars.example terraform.tfvars    # preencha labrole_arn e bucket_nome
#   aws iam get-role --role-name LabRole --query Role.Arn --output text
terraform init && terraform apply

cd ../scripts
./run_job.sh          # sobe job + queries + CSV, dispara o Glue e faz polling
./ver_resultado.sh    # lista o lake particionado e imprime os 3 resultados

cd ../infra
terraform destroy     # OBRIGATÓRIO ao final
```

Parâmetros do job (em `infra/main.tf`): `--TOP_N` (padrão `2`) e
`--THRESHOLD` (padrão `5000`).

Evidências da execução: [`evidencias/6325226/EVIDENCIAS.md`](evidencias/6325226/EVIDENCIAS.md).
