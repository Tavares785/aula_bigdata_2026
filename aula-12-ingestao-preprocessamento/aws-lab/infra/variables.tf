variable "bucket_name" {
  description = "Nome do bucket S3 (deve ser globalmente único)"
  type        = string
}

variable "lab_role_arn" {
  description = "ARN da LabRole (obtido via: aws iam get-role --role-name LabRole --query Role.Arn --output text)"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto (usado como prefixo para recursos)"
  type        = string
  default     = "mercadofacil-bigdata"
}

variable "glue_version" {
  description = "Versão do AWS Glue"
  type        = string
  default     = "4.0"
}
