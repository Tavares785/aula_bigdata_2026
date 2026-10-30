# outputs.tf — aws-lab (aula-09: Data Warehousing com Spark SQL no AWS Glue)
# Expõe os valores que os scripts em ../scripts consomem via `terraform output -raw`.

output "bucket_nome" {
  description = "Nome do bucket S3 do lab."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job do warehouse. Usado no --job-name do 'aws glue start-job-run'."
  value       = aws_glue_job.warehouse.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job."
  value       = var.labrole_arn
}
