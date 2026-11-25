output "bucket_nome" {
  description = "Bucket S3 do grupo."
  value       = var.bucket_nome
}

output "athena_workgroup" {
  description = "Selecione este workgroup no console do Athena antes de rodar queries."
  value       = aws_athena_workgroup.aula14.name
}

output "glue_database" {
  description = "Banco no Athena."
  value       = aws_glue_catalog_database.mercadofacil.name
}

output "superset_url" {
  description = "URL do Superset (leva ~8 min apos o apply para ficar pronto)."
  value       = var.criar_superset ? "http://${aws_instance.superset[0].public_ip}:8088" : "Superset desativado (criar_superset = false)"
}

output "superset_usuario" {
  description = "Usuario admin do Superset."
  value       = var.criar_superset ? "admin" : "-"
}
