output "bucket_nome" {
  description = "Bucket S3 do pipeline."
  value       = terraform_data.bucket.output
}

output "glue_job_nome" {
  description = "Nome do Glue Job de ETL."
  value       = aws_glue_job.etl.name
}

output "glue_crawler_nome" {
  description = "Nome do Glue Crawler das camadas."
  value       = aws_glue_crawler.camadas.name
}

output "glue_database_nome" {
  description = "Database do Glue Catalog consultado no Athena."
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "athena_resultados_uri" {
  description = "Prefixo S3 para os resultados das consultas no Athena."
  value       = "s3://${var.bucket_nome}/athena-results/"
}
