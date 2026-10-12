# outputs.tf — aws-lab (aula-07: Machine Learning com Spark MLlib no AWS Glue)
# Expõe os valores que os scripts em ../scripts consomem via `terraform output -raw`.

output "bucket_nome" {
  description = "Nome do bucket S3 do lab (guarda script de ML, dataset de entrada, saída e logs)."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job de ML. Usado no --job-name do 'aws glue start-job-run'."
  value       = aws_glue_job.ml_churn.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job (informativo; a role já está no Job)."
  value       = var.labrole_arn
}
