# variables.tf — aws-lab (aula-06: Spark SQL/DataFrames no AWS Glue)
# PRONTO — não precisa alterar (preencha os valores em terraform.tfvars).
#
# Variáveis de entrada da infra que o aluno provisiona (S3 + AWS Glue Job).

# Região obrigatória do AWS Academy Learner Lab.
variable "regiao" {
  description = "Região AWS obrigatória do lab (Learner Lab)."
  type        = string
  default     = "us-east-1"
}

# ARN da role pré-provisionada LabRole. No Learner Lab NÃO é permitido criar
# roles/policies próprias: o Glue Job usa esta role por ARN (é ela quem
# lê/escreve no S3 e escreve os logs durante a execução do job).
variable "labrole_arn" {
  description = "ARN da role LabRole do Learner Lab, usada como IAM role do Glue Job (sem criar roles/policies próprias)."
  type        = string
}

# Nome global único do bucket S3 do lab (guarda script, os 2 CSVs de entrada,
# a saída do TOP-N de clientes e logs do Glue Job).
variable "bucket_nome" {
  description = "Nome global único do bucket S3 do lab (guarda script, dados de entrada, saída e logs do Glue Job)."
  type        = string
}
