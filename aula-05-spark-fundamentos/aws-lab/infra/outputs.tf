# outputs.tf - aws-lab (aula-05)

output "bucket_nome" {
  description = "Nome do bucket S3 do lab."
  value       = data.aws_s3_bucket.lab.bucket
}

output "glue_job_nome" {
  description = "Nome do Glue Job."
  value       = aws_glue_job.wordcount.name
}

output "labrole_arn" {
  description = "ARN da LabRole."
  value       = var.labrole_arn
}