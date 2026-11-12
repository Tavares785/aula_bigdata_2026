# AWS Data Pipeline Implementation for MercadoFácil

Complete AWS data pipeline using Terraform and PySpark, implementing medallion architecture (raw → silver → gold) for e-commerce analytics.

**Watch for:** Terraform validation not run (confirmed, environment limitation documented).

**Verdict**: APPROVED

## High-level view

The Terraform infrastructure creates a complete AWS Glue ETL pipeline through seven resources: bucket creation via AWS CLI to avoid Learner Lab SCP restrictions, automatic upload of raw CSV and PySpark script, Glue database for metadata, Glue job configured with LabRole and S3 paths as arguments, and two crawlers targeting silver and gold layers. Eight outputs expose resource names and S3 paths.

The PySpark ETL implements a comprehensive data quality pipeline with 13 transformation rules addressing date formats, monetary values, text normalization, CPF/email validation, deduplication via window functions, and LGPD-compliant anonymization with SHA-256 hashing. Invalid records flow to quarantine with reason tracking, not silent deletion. Four gold tables answer specific business questions: delay analysis correlated with ratings, cancellation/return rates by category and channel, seasonality patterns for Black Friday and Christmas, and a granular fact table.

Documentation in REGRAS_SILVER.md maps each of 13 discovered data quality problems to its transformation rule. PROGRESS.md documents work done, tools used, five specific difficulties encountered (data quality complexity, Terraform CLI requirement, LGPD decisions, quarantine design, deduplication criteria), and next steps for exploratory analysis and predictive modeling.

<details>
<summary>Issues (1)</summary>

1. **Terraform validation not run** — The verification report states terraform fmt and validate were not executed due to Windows environment limitations. The code structure follows provider 5.31.0 patterns, but formal validation is absent from evidence. Since the prompt instructs "não rode novamente" and the coder's verification report explicitly documents this limitation with mitigation reasoning, this is acceptable but flagged for transparency.

</details>

<details><summary>Details</summary>

## Terraform infrastructure meets all CI requirements

The provider configuration pins AWS provider to exactly version 5.31.0 (not a range) with region us-east-1. Variables are defined for bucket name and LabRole ARN, keeping secrets out of version control. No IAM resources are declared; the implementation correctly uses the pre-existing LabRole by ARN reference.

S3 bucket creation uses terraform_data with local-exec provisioner running `aws s3api create-bucket`, not the aws_s3_bucket resource. This is the correct workaround for Learner Lab's SCP policy that blocks GetBucketObjectLockConfiguration. The destroy provisioner runs `aws s3 rb --force` to empty and remove the bucket, satisfying the cleanup requirement. Two upload resources use triggers_replace with filemd5() to detect changes in the CSV and PySpark script, automatically re-uploading when either file changes.

The Glue job resource specifies role_arn (LabRole), command block with name="glueetl", script_location pointing to S3, and glue_version="4.0". Default arguments pass four S3 paths (INPUT_PATH, SILVER_PATH, GOLD_PATH, QUARANTINE_PATH) as job arguments, which the PySpark script reads via getResolvedOptions. CloudWatch logging, Spark UI, and metrics are enabled. Two crawlers target the silver and gold S3 prefixes, both configured with the LabRole and the Glue database name.

Eight outputs expose bucket_name, glue_job_name, glue_database_name, silver_crawler_name, gold_crawler_name, and three S3 paths. This exceeds the requirement of at least three outputs.

## PySpark ETL implements medallion architecture with quarantine

The ETL script uses getResolvedOptions to receive S3 paths from Terraform job arguments. It reads the raw CSV without schema inference (all columns as strings initially), applies 13 data quality rules, and writes silver parquet.

Date parsing uses coalesce with three to_date patterns (yyyy-MM-dd, dd/MM/yyyy, yyyy-MM-dd HH:mm:ss). Monetary values have "R$" removed and commas replaced with dots before casting to DecimalType(10,2). Percentages have "%" removed before casting to DecimalType(5,2). Text fields are normalized with upper/lower/initcap and trimmed. Estado is mapped from full names to abbreviations (São Paulo → SP). Status_pedido is mapped from English to Portuguese (delivered → entregue).

CPF validation removes non-numeric characters and checks for exactly 11 digits. Email validation converts to lowercase and checks for "@" presence. Records with null pedido_id, null cliente_id, invalid data_pedido, invalid CPF, or invalid email are marked with motivo_quarentena and written to a separate quarantine parquet prefix.

Deduplication uses row_number() over a window partitioned by item_id and ordered by data_pedido ascending, keeping only the first occurrence. This is semantically correct: if the same item appears multiple times, keep the earliest record.

LGPD anonymization creates SHA-256 hashes of cliente_nome, cliente_email, and cliente_cpf, then drops the original columns along with comentario. The hash approach maintains the ability to aggregate by customer (same customer always produces same hash) without exposing personal data in analytical layers.

The silver parquet is written with mode="overwrite" to a dedicated prefix. Logging reports total raw records, valid records, quarantine count, duplicates removed, and final silver count.

Four gold tables are created from silver via groupBy and agg:

1. **analise_atrasos_avaliacoes** groups by estado, categoria, transportadora, centro_distribuicao and calculates delay metrics (total orders, orders delayed, average/max delay days, average rating, low ratings count, delay rate percentage, low rating rate percentage). Filters to status_pedido = "entregue" since only delivered orders have delay data.

2. **analise_cancelamentos_devolucoes** groups by estado, categoria, canal, forma_pagamento and calculates cancellation/return metrics (total orders, cancelled count, returned count, total sales value, average ticket, unique customers, cancellation rate percentage, return rate percentage, total loss rate percentage).

3. **analise_sazonalidade** extracts year and month from data_pedido, adds Portuguese month names, groups by ano, mes, mes_nome, categoria, and calculates monthly metrics (total orders, total revenue, average delay, cancellations, returns, average rating). Ordered by year, month, category to make temporal patterns visible.

4. **fato_pedidos** is a granular fact table selecting all non-PII fields from silver (includes hashed PII fields but not originals). This supports ad-hoc queries in Athena without reprocessing silver.

Each gold table is written to its own parquet prefix under gold/ with mode="overwrite". The job commits successfully after printing a summary of processing statistics.

## Documentation is comprehensive and specific

REGRAS_SILVER.md documents 13 data quality problems with problem → regra structure. Each entry explains what was wrong in the raw data and what transformation was applied in silver. The document includes a summary table mapping fields to problems to transformations, explains quarantine criteria with specific motivo values, and documents the LGPD anonymization strategy.

PROGRESS.md fills all four required sections with substantive content. "O que foi feito" describes the complete pipeline (Terraform resources, ETL layers, gold tables, documentation). "Ferramentas usadas" lists nine tools with their purpose (Terraform for IaC, Glue for distributed PySpark, S3 for storage, Athena for queries, CloudWatch for logs, AWS CLI for bucket creation, PySpark SQL for transformations).

"Dificuldades encontradas" documents five specific challenges: data quality complexity (13 problem categories requiring robust logic), Terraform requirements (bucket via CLI not resource, destroy must empty first, conditional uploads), LGPD anonymization decisions (hash to preserve aggregation capability), quarantine design (separate dataframe with reason tracking, not silent discard), and deduplication criteria (item_id with earliest data_pedido tie-breaker).

"Próxima etapa" outlines five concrete next steps: exploratory analysis in Athena, visualization via BI tool connection, predictive modeling for delay risk and cancellation factors, business recommendations (reinforce logistics in critical regions, adjust estimated delivery times), and pipeline optimization (partitioning, incremental load, automated quality tests).

No "<PREENCHER" placeholders remain in either document. REGRAS_SILVER.md documents 13 problems (requirement: 6) with 5,847 characters (requirement: 400). PROGRESS.md fills all 4 required sections.

</details>

<details>
<summary>File map</summary>

**aws-lab/infra/provider.tf** — AWS provider 5.31.0 pinned, region us-east-1  
**aws-lab/infra/variables.tf** — Four variables (bucket name, LabRole ARN, project name, Glue version)  
**aws-lab/infra/s3.tf** — Bucket creation via terraform_data + local-exec, CSV and script uploads with filemd5 triggers, destroy provisioner  
**aws-lab/infra/glue.tf** — Glue database, Glue job (glueetl + role + script location + S3 path arguments), two crawlers (silver/gold)  
**aws-lab/infra/outputs.tf** — Eight outputs (bucket, job, database, crawlers, S3 paths)  
**aws-lab/job/etl_mercadofacil.py** — Complete PySpark ETL: raw CSV read, 13 quality rules, deduplication, LGPD anonymization, quarantine with reason, silver parquet, 4 gold tables  
**aws-lab/REGRAS_SILVER.md** — 13 data quality problems documented with problema → regra structure  
**PROGRESS.md** — Four sections filled: work done, tools used, five specific difficulties, next steps  
**aws-lab/scripts/setup.sh** — AWS credentials setup helper  
**aws-lab/scripts/run_pipeline.sh** — Automated pipeline execution orchestration  

[Full diff available via git show HEAD or git log]

</details>
