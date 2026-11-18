# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## O que foi feito nesta etapa

O grupo construiu e validou localmente todo o pipeline da MercadoFácil
para o AWS Academy Learner Lab: infraestrutura com **Terraform**
(provider aws 5.31.0, us-east-1, `terraform fmt -check` e `terraform
validate` passando) que cria o bucket S3 via AWS CLI (`terraform_data`
+ `local-exec`, sem `aws_s3_bucket`), envia o CSV bruto para `raw/` e o
script PySpark para `scripts/`, e declara o `aws_glue_catalog_database`,
o `aws_glue_job` (glueetl, Glue 4.0, LabRole por ARN) e o
`aws_glue_crawler` com `s3_target` para silver/gold. O ETL PySpark
(`aws-lab/job/etl_mercadofacil.py`) implementa a arquitetura medalhão:
lê o CSV raw sem alterações, aplica as regras documentadas em
`REGRAS_SILVER.md` (tipagem de datas/valores, padronização de status e
pagamento, pseudonimização de PII, dedup por `(pedido_id, item_id)`),
grava a silver em Parquet com área de quarentena e produz três tabelas
gold em Parquet (`fato_entregas`, `agregado_atraso_nota`,
`sazonalidade_mensal`). Todos os checks estruturais do CI passam
(`pytest -v`, 11/11). **Pendente:** a execução real (`terraform apply`,
Glue Job, Crawler e Athena) ficou impedida porque o acesso ao Learner
Lab expirou no momento da entrega — a infra e o ETL estão prontos para
serem executados assim que o grupo renovar o acesso.

## Ferramentas efetivamente usadas

- **Terraform (aws provider 5.31.0):** infraestrutura declarada e
  validada localmente (bucket S3 via CLI, uploads, Glue Database,
  Glue Job, Glue Crawler, outputs e variáveis por aluno);
  `terraform init`/`fmt -check`/`validate` executados nesta entrega.
- **PySpark (script do Glue, Glue 4.0):** ETL medalhão raw → silver →
  gold desenvolvido e revisado em `aws-lab/job/etl_mercadofacil.py`
  (execução no Glue Job pendente da renovação do acesso ao Learner Lab).
- **S3:** camadas definidas `raw/` (CSV bruto), `silver/` (Parquet
  tipado), `quarentena/` (linhas rejeitadas com motivo) e `gold/`
  (Parquet de negócio).
- **AWS Glue Job + Glue Crawler + Glue Catalog:** declarados via
  Terraform para executar o ETL e catalogar as tabelas Parquet no
  Athena (execução pendente do acesso).
- **Amazon Athena:** consultas de verificação já preparadas em
  `aws-lab/scripts/consultas_athena.sql` para quando o pipeline rodar.

## Dificuldades encontradas

- **Erro real de validação no Terraform:** o provisioner de destroy não
  pode referenciar variáveis ("Invalid reference from destroy
  provisioner", acusado no `terraform init`/`validate`) — os requisitos
  do README já explicavam COMO criar o bucket via AWS CLI, mas não essa
  limitação do Terraform; resolvido com o atributo `input` +
  `self.input` no `terraform_data`.
- **Acesso à AWS expirado:** as credenciais do Learner Lab não estavam
  mais válidas no momento da entrega, então `apply`, Glue Job, Crawler
  e Athena não puderam ser executados — a renovação do acesso é o
  único passo pendente para rodar o pipeline de ponta a ponta.
- **Tratamento da base suja (trabalho esperado pelo README, mas
  exigiu decisão):** datas em dois formatos (`DD/MM/AAAA` e
  `AAAA-MM-DD`), moedas com `R$` e vírgula decimal, sentinelas
  `-`/`N/A`, `status_pedido` e `forma_pagamento` sem padronização de
  caixa/idioma, dados de pedido/cliente repetidos por item e PII em
  texto puro — cada problema recebeu uma regra documentada em
  `REGRAS_SILVER.md`.
- Mitigações das dicas do README já incorporadas ao design: prefixos
  de saída limpos (`mode("overwrite")`) e `terraform destroy` que
  esvazia o bucket antes de remover.

