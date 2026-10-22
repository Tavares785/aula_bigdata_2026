# outputs.tf — aws-lab (aula-06)
# ESCRITO PELO ALUNO: nao veio no repositorio do professor. Ver main.tf.
# Os nomes sao exatamente os que scripts/run_job.sh le com `terraform output -raw`.

output "bucket_nome" {
  description = "Nome do bucket S3 do lab."
  value       = var.bucket_nome
}

output "glue_job_nome" {
  description = "Nome do Glue Job (usado no aws glue start-job-run)."
  value       = aws_glue_job.spark_sql.name
}

output "labrole_arn" {
  description = "ARN da LabRole usada como IAM role do Glue Job."
  value       = var.labrole_arn
}
