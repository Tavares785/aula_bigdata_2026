# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## O que foi feito nesta etapa

Construímos o pipeline em Terraform (`aws-lab/infra/`) e o ETL PySpark
(`aws-lab/job/etl_pedidos.py`) em arquitetura medalhão: raw (CSV intacto) →
silver (Parquet limpo) + quarentena (Parquet com motivo) → gold (3 tabelas de
negócio). O Terraform cria o bucket via AWS CLI, envia o CSV e o script, e
declara o Glue database, o Glue Job (Glue 4.0, LabRole) e o Crawler. O
`terraform fmt -check` e o `terraform validate` passam.

Rodamos o ETL localmente com PySpark sobre o CSV completo: 10.000 linhas
viraram 9.509 na silver e 491 na quarentena (97 preço inválido, 52 data
inválida, 149 quantidade inválida e 193 duplicados). As regras estão em
`aws-lab/REGRAS_SILVER.md`. A gold tem `atraso_por_estado_transportadora`,
`nota_por_faixa_atraso` e `vendas_mensais_categoria`. Um resultado já visível:
a nota média cai de 4,12 (no prazo) para 2,20 (atraso de 8 dias ou mais).

Executamos o pipeline no Learner Lab: `terraform apply` criou 6 recursos, o
Glue Job terminou em `SUCCEEDED` (178 s, JobRunId
`jr_aafbaed12aae867e24b50ed914019249d50165e260392d1ab6c98bb6ee9456f0`), o
Crawler catalogou 5 tabelas e a consulta no Athena sobre a gold retornou os
mesmos números do teste local. Os prints estão em `aws-lab/evidencias/`. O
`terraform destroy` encerra a etapa.

## Ferramentas efetivamente usadas

- **Terraform** (provider `aws` 5.31.0): infraestrutura como código.
- **AWS CLI** (`terraform_data` + `local-exec`): cria e remove o bucket S3, já
  que o Learner Lab bloqueia o recurso `aws_s3_bucket`.
- **S3**: camadas raw, silver, gold e quarantine, além do script do ETL.
- **Glue Job (PySpark)**: limpeza, deduplicação e geração das tabelas gold.
- **Glue Crawler e Data Catalog**: catalogam silver, gold e quarentena.
- **Athena**: consulta das tabelas gold.
- **PySpark local (3.3) com JDK 11**: validação do ETL antes de ir para a AWS.

## Dificuldades encontradas

- **Qualidade dos dados**: o CSV tem datas em 3 formatos, valores em `R$`,
  nulos escritos de vários jeitos, categorias truncadas e `valor_total`
  inconsistente. Resolvemos com um perfil prévio dos dados e uma regra
  documentada para cada problema.
- **Nulos no Spark**: um desconto nulo deixava a validação nula e o
  `valor_total` original era ignorado. Corrigimos com `coalesce` e conferimos
  as flags de correção.
- **Learner Lab**: não dá para criar roles IAM nem usar `aws_s3_bucket`, então
  usamos a LabRole por ARN e criamos o bucket pela CLI.
- **Ambiente local**: sem `sudo` no WSL, instalamos um JDK temporário em `/tmp`
  para testar o PySpark.

## Próxima etapa (Aula 13)

Usar a camada gold para analisar as causas do atraso (estado, transportadora,
centro de distribuição, mês) e a relação entre atraso e nota de avaliação.
Também vamos modelar o risco de atraso e de cancelamento ou devolução, e
explorar a sazonalidade de vendas (Black Friday e Natal) por categoria.
