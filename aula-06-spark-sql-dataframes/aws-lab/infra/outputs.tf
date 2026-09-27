# outputs.tf — valores usados pelos scripts run_job.sh e ver_resultado.sh

output "bucket_nome" {
  description = "Nome do bucket S3 do lab."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job (usar em aws glue start-job-run)."
  value       = aws_glue_job.topn.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada pelo Glue Job."
  value       = var.labrole_arn
}
