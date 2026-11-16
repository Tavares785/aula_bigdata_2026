output "bucket" {
  value       = local.bucket
  description = "Bucket do pipeline. Nome global, com o identificador do grupo."
}

output "caminhos" {
  value = {
    raw        = local.raw
    silver     = local.silver
    gold       = local.gold
    quarentena = local.quarentena
  }
  description = "Caminhos das camadas, para os scripts nao os adivinharem."
}

output "glue_job" {
  value       = aws_glue_job.etl.name
  description = "Nome do Glue Job, usado por aws glue start-job-run."
}

output "glue_crawler" {
  value       = aws_glue_crawler.camadas.name
  description = "Nome do Crawler, usado por aws glue start-crawler."
}

output "glue_database" {
  value       = aws_glue_catalog_database.mercadofacil.name
  description = "Banco no Catalog, usado nas consultas do Athena."
}
