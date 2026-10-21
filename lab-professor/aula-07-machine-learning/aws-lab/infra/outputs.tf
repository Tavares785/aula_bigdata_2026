# outputs.tf — aws-lab (aula-07 • DEMO DO PROFESSOR — Previsão de Ações)
# Expõe os valores que os scripts em ../scripts consomem via `terraform output -raw`.

output "bucket_nome" {
  description = "Nome do bucket S3 da demo (guarda script PySpark, dataset de entrada, saída e logs)."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job da demo. Usado no --job-name do 'aws glue start-job-run'."
  value       = aws_glue_job.acoes.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job (informativo; a role já está no Job)."
  value       = var.labrole_arn
}
