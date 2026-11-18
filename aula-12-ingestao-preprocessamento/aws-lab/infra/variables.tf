# Variaveis que mudam por aluno/grupo. Nada de segredos aqui (o .gitignore
# da pasta aws-lab protege *.tfvars e estado).

variable "lab_role_arn" {
  description = "ARN da LabRole do AWS Academy Learner Lab (aws iam get-role --role-name LabRole --query Role.Arn --output text)"
  type        = string
}

variable "bucket_name" {
  description = "Nome global do bucket S3 do grupo (inclua um identificador unico)"
  type        = string
}

variable "glue_database_name" {
  description = "Nome do Glue Catalog Database"
  type        = string
  default     = "mercadofacil_db"
}

variable "glue_job_name" {
  description = "Nome do Glue Job do ETL"
  type        = string
  default     = "mercadofacil-etl"
}

variable "glue_crawler_name" {
  description = "Nome do Glue Crawler das camadas silver/gold"
  type        = string
  default     = "mercadofacil-crawler"
}

variable "script_path" {
  description = "Caminho local do script PySpark a ser enviado para o S3"
  type        = string
  default     = "../job/etl_mercadofacil.py"
}

variable "dataset_path" {
  description = "Caminho local do CSV bruto a ser enviado para o S3"
  type        = string
  default     = "../data/pedidos_mercadofacil.csv"
}
