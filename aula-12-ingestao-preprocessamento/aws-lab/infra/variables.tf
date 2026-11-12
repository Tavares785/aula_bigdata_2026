variable "bucket_name" {
  description = "Nome do bucket S3 para armazenar os dados (deve ser globalmente único)"
  type        = string
}

variable "lab_role_arn" {
  description = "ARN da LabRole do AWS Academy Learner Lab"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto (usado em tags e nomes de recursos)"
  type        = string
  default     = "mercadofacil-bigdata"
}

variable "glue_version" {
  description = "Versão do AWS Glue a ser utilizada"
  type        = string
  default     = "4.0"
}
