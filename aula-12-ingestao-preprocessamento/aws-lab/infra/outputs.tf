# =============================================================================
# Terraform Outputs
# =============================================================================

output "bucket_name" {
  description = "Nome do bucket S3 criado"
  value       = var.bucket_name
}

output "glue_job_name" {
  description = "Nome do Glue Job"
  value       = aws_glue_job.etl_mercadofacil.name
}

output "glue_database_name" {
  description = "Nome do Glue Catalog Database"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "silver_crawler_name" {
  description = "Nome do Crawler da camada silver"
  value       = aws_glue_crawler.mercadofacil_silver.name
}

output "gold_crawler_name" {
  description = "Nome do Crawler da camada gold"
  value       = aws_glue_crawler.mercadofacil_gold.name
}

output "raw_data_path" {
  description = "Caminho S3 dos dados raw"
  value       = "s3://${var.bucket_name}/raw/"
}

output "silver_data_path" {
  description = "Caminho S3 dos dados silver"
  value       = "s3://${var.bucket_name}/silver/"
}

output "gold_data_path" {
  description = "Caminho S3 dos dados gold"
  value       = "s3://${var.bucket_name}/gold/"
}
