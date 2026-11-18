output "bucket_name" {
  description = "Nome do bucket S3 criado para o pipeline"
  value       = var.bucket_name
}

output "glue_job_name" {
  description = "Nome do Glue Job do ETL"
  value       = aws_glue_job.etl_mercadofacil.name
}

output "glue_crawler_name" {
  description = "Nome do Glue Crawler"
  value       = aws_glue_crawler.mercadofacil.name
}

output "glue_database_name" {
  description = "Nome do banco de dados no Glue Catalog / Athena"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "s3_raw_prefix" {
  description = "Caminho S3 da camada raw (entrada do ETL)"
  value       = "s3://${var.bucket_name}/raw/"
}

output "s3_gold_prefix" {
  description = "Caminho S3 da camada gold (pronta para Athena)"
  value       = "s3://${var.bucket_name}/gold/"
}
