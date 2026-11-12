output "bucket_name" {
  description = "Nome do bucket S3 criado"
  value       = var.bucket_name
}

output "glue_job_name" {
  description = "Nome do Glue Job para executar o ETL"
  value       = aws_glue_job.etl_mercadofacil.name
}

output "glue_database_name" {
  description = "Nome do database no Glue Catalog"
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "silver_crawler_name" {
  description = "Nome do Crawler para a camada silver"
  value       = aws_glue_crawler.mercadofacil_silver.name
}

output "gold_crawler_name" {
  description = "Nome do Crawler para a camada gold"
  value       = aws_glue_crawler.mercadofacil_gold.name
}

output "raw_data_path" {
  description = "Caminho S3 dos dados brutos (raw)"
  value       = "s3://${var.bucket_name}/raw/"
}

output "silver_data_path" {
  description = "Caminho S3 dos dados limpos (silver)"
  value       = "s3://${var.bucket_name}/silver/"
}

output "gold_data_path" {
  description = "Caminho S3 das tabelas de negócio (gold)"
  value       = "s3://${var.bucket_name}/gold/"
}
