output "bucket_nome" {
  description = "Nome do bucket S3 do laboratorio."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job usado para iniciar a execucao."
  value       = aws_glue_job.dataframes.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada pelo Glue Job."
  value       = var.labrole_arn
}