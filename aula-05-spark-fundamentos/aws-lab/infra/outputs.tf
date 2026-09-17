# outputs.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)
# Expõe os valores que os scripts em ../scripts consomem via `terraform output`.

output "bucket_nome" {
  description = "Nome do bucket S3 do lab (guarda script, dados de entrada, saída e logs)."
  value       = data.aws_s3_bucket.lab.bucket
}

output "glue_job_nome" {
  description = "Nome do Glue Job. Usado no --job-name do 'aws glue start-job-run'."
  value       = aws_glue_job.wordcount.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job (informativo; a role já está no Job)."
  value       = var.labrole_arn
}
