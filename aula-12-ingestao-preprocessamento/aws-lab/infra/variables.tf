variable "bucket_name" {
  description = "Nome do bucket S3 (global na AWS): inclua o identificador do grupo."
  type        = string
}

variable "lab_role_arn" {
  description = "ARN da LabRole (aws iam get-role --role-name LabRole --query Role.Arn --output text)."
  type        = string
}

variable "database_name" {
  description = "Nome do banco no Glue Data Catalog."
  type        = string
  default     = "mercadofacil_db"
}

variable "job_name" {
  description = "Nome do Glue Job do ETL."
  type        = string
  default     = "mercadofacil-etl-pedidos"
}

variable "crawler_name" {
  description = "Nome do Glue Crawler."
  type        = string
  default     = "mercadofacil-crawler"
}
