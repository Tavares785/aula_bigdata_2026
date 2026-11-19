variable "aws_region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Nome do bucket S3 (único globalmente)"
  type        = string
  default     = "mercadofacil-grupo3"
}

variable "lab_role_arn" {
  description = "ARN da LabRole do AWS Academy (não versionar — passe via tfvars ou variável de ambiente)"
  type        = string
}

variable "glue_database_name" {
  description = "Nome do banco de dados no Glue Catalog"
  type        = string
  default     = "mercadofacil_db"
}

variable "glue_job_name" {
  description = "Nome do Glue Job"
  type        = string
  default     = "mercadofacil-etl"
}

variable "glue_crawler_name" {
  description = "Nome do Glue Crawler"
  type        = string
  default     = "mercadofacil-crawler"
}

variable "raw_csv_local_path" {
  description = "Caminho local do CSV bruto para upload no S3"
  type        = string
  default     = "../../data/pedidos_mercadofacil.csv"
}

variable "etl_script_local_path" {
  description = "Caminho local do script PySpark para upload no S3"
  type        = string
  default     = "../job/etl.py"
}
