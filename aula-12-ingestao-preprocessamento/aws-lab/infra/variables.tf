variable "bucket_name" {
  description = "Nome único do bucket S3 (inclua o identificador do grupo, pois é global)"
  type        = string
}

variable "lab_role_arn" {
  description = "ARN da LabRole do AWS Academy (aws iam get-role --role-name LabRole --query Role.Arn --output text)"
  type        = string
}

variable "glue_db_name" {
  description = "Nome do banco de dados no Glue Catalog"
  type        = string
  default     = "mercadofacil_db"
}

variable "glue_job_name" {
  description = "Nome do Glue Job"
  type        = string
  default     = "etl-mercadofacil"
}

variable "glue_crawler_name" {
  description = "Nome do Glue Crawler"
  type        = string
  default     = "crawler-mercadofacil"
}
