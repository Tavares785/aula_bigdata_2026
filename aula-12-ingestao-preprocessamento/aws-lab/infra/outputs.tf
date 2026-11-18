output "bucket_nome" {
  description = "Nome do bucket S3 do pipeline"
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job de ETL"
  value       = aws_glue_job.etl.name
}

output "glue_crawler_nome" {
  description = "Nome do Glue Crawler"
  value       = aws_glue_crawler.silver_gold.name
}

output "glue_database_nome" {
  description = "Nome do Glue Catalog Database"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "labrole_arn" {
  description = "ARN da LabRole utilizada"
  value       = var.labrole_arn
}
