output "bucket_name" {
  description = "Bucket S3 do pipeline."
  value       = var.bucket_name
}

output "glue_job_name" {
  description = "Glue Job do ETL (aws glue start-job-run --job-name ...)."
  value       = aws_glue_job.etl.name
}

output "glue_crawler_name" {
  description = "Glue Crawler (aws glue start-crawler --name ...)."
  value       = aws_glue_crawler.this.name
}

output "glue_database_name" {
  description = "Banco do Glue Catalog, consultado no Athena."
  value       = aws_glue_catalog_database.this.name
}

output "gold_path" {
  description = "Prefixo S3 da camada gold."
  value       = "s3://${var.bucket_name}/${local.gold_prefix}/"
}
