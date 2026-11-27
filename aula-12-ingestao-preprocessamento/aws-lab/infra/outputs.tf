output "bucket_name" {
  description = "Bucket S3 do pipeline (raw, silver, gold, quarentena, scripts)."
  value       = terraform_data.bucket.output
}

output "raw_csv_uri" {
  description = "Local do CSV bruto na camada raw."
  value       = "s3://${terraform_data.bucket.output}/${aws_s3_object.raw_csv.key}"
}

output "silver_uri" {
  description = "Prefixo da camada silver."
  value       = "s3://${terraform_data.bucket.output}/${local.silver_prefix}"
}

output "gold_uri" {
  description = "Prefixo da camada gold."
  value       = "s3://${terraform_data.bucket.output}/${local.gold_prefix}"
}

output "quarantine_uri" {
  description = "Prefixo da quarentena (linhas rejeitadas + motivo)."
  value       = "s3://${terraform_data.bucket.output}/${local.quarantine_prefix}"
}

output "glue_job_name" {
  description = "Nome do Glue Job (aws glue start-job-run --job-name ...)."
  value       = aws_glue_job.etl.name
}

output "glue_crawler_name" {
  description = "Nome do Glue Crawler (aws glue start-crawler --name ...)."
  value       = aws_glue_crawler.curated.name
}

output "glue_database_name" {
  description = "Database do Glue Catalog consultado pelo Athena."
  value       = aws_glue_catalog_database.this.name
}

output "athena_results_uri" {
  description = "Onde o Athena grava os resultados das consultas."
  value       = "s3://${terraform_data.bucket.output}/athena-results/"
}

output "athena_tables" {
  description = "Tabelas esperadas no Catalog depois do crawler."
  value       = concat(local.silver_tables, ["quarentena"], local.gold_tables)
}
