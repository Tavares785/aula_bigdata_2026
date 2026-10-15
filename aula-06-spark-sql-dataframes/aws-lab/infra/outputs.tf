# outputs.tf - aws-lab (aula-06)

output "bucket_nome" {
  description = "Nome do bucket S3 do lab."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job. Usado no --job-name do aws glue start-job-run."
  value       = aws_glue_job.topn.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job."
  value       = var.labrole_arn
}