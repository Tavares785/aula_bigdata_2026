variable "lab_role_arn" {
  description = "ARN da LabRole (aws iam get-role --role-name LabRole --query Role.Arn --output text)."
  type        = string
}

variable "bucket_name" {
  description = "Nome globalmente unico do bucket S3 (inclua o identificador do grupo)."
  type        = string
}

variable "glue_database" {
  description = "Nome do banco no Glue Data Catalog."
  type        = string
  default     = "mercadofacil_db"
}

variable "glue_job_name" {
  description = "Nome do Glue Job do ETL."
  type        = string
  default     = "mercadofacil-etl-medalhao"
}

variable "glue_crawler_name" {
  description = "Nome do Glue Crawler."
  type        = string
  default     = "mercadofacil-crawler"
}
