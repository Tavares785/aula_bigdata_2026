# Outputs uteis para o console do Learner Lab e para os prints do professor.

output "bucket_name" {
  description = "Bucket S3 do data lake (raw/silver/gold)"
  value       = var.bucket_name
}

output "glue_database" {
  description = "Database do Glue Catalog para consultas no Athena"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "glue_job" {
  description = "Job Glue do ETL (aguardar SUCCEEDED e registrar o JobRunId)"
  value       = aws_glue_job.etl_mercadofacil.name
}

output "glue_crawler" {
  description = "Crawler que cataloga silver/gold"
  value       = aws_glue_crawler.mercadofacil.name
}

output "athena_workgroup_hint" {
  description = "Prefixo de consulta sugerido para o Athena"
  value       = "SELECT * FROM ${aws_glue_catalog_database.mercadofacil.name}.fato_entregas LIMIT 10"
}
