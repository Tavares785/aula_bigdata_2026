output "bucket_name" {
  description = "Nome do bucket S3 criado"
  value       = var.bucket_name
}

output "glue_job_name" {
  description = "Nome do Glue Job"
  value       = aws_glue_job.etl.name
}

output "glue_database_name" {
  description = "Nome do banco no Glue Catalog"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "glue_crawler_name" {
  description = "Nome do Glue Crawler"
  value       = aws_glue_crawler.mercadofacil.name
}

output "raw_s3_path" {
  description = "Caminho S3 da camada raw"
  value       = "s3://${var.bucket_name}/raw/"
}

output "silver_s3_path" {
  description = "Caminho S3 da camada silver"
  value       = "s3://${var.bucket_name}/silver/"
}

output "gold_s3_path" {
  description = "Caminho S3 da camada gold"
  value       = "s3://${var.bucket_name}/gold/"
}
