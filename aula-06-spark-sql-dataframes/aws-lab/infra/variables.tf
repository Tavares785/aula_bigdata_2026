# variables.tf — aws-lab (aula-06)
# ESCRITO PELO ALUNO: nao veio no repositorio do professor. Ver main.tf.
# Os nomes seguem exatamente o terraform.tfvars.example fornecido pelo professor.

variable "regiao" {
  description = "Regiao AWS obrigatoria do lab (Learner Lab)."
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da role LabRole do Learner Lab, usada como IAM role do Glue Job (sem criar roles/policies proprias)."
  type        = string
}

variable "bucket_nome" {
  description = "Nome global unico do bucket S3 do lab (guarda script, dados de entrada e saida do Glue Job)."
  type        = string
}

variable "top_n" {
  description = "Quantos clientes o job deve trazer no ranking de maior gasto."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Tags de custo padronizadas aplicadas a todos os recursos."
  type        = map(string)
  default = {
    Projeto    = "lab-aula-06-spark-sql"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}
