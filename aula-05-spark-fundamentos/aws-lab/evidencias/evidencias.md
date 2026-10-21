# Evidências — Aula 05: Spark/RDDs no AWS Glue

**RA:** 6325033
**Projeto:** aula-05-spark-fundamentos
**Serviço:** AWS Glue
**Região:** us-east-1

---

## 1. Identidade AWS

A identidade da conta foi validada utilizando:

```bash
aws sts get-caller-identity
```

A `LabRole` utilizada no laboratório foi validada com:

```bash
aws iam get-role --role-name LabRole --query Role.Arn --output text
```

ARN utilizado:

```text
arn:aws:iam::441907008326:role/LabRole
```

---

## 2. Infraestrutura

O Terraform foi inicializado e validado com sucesso:

```bash
terraform init
terraform validate
terraform plan
```

O `terraform plan` indicou:

```text
Plan: 5 to add, 0 to change, 0 to destroy.
```

Recursos planejados:

```text
Bucket: lab-aula05-glue-6325033
Glue Job: job-aula05-wordcount
LabRole:
arn:aws:iam::441907008326:role/LabRole
```

### Observação sobre o Terraform Apply

O `terraform apply` não foi concluído devido a uma restrição do AWS Academy Learner Lab.

O erro retornado foi:

```text
AccessDenied:
User is not authorized to perform:
s3:GetBucketObjectLockConfiguration
```

A mensagem indicou um `explicit deny` proveniente de uma Service Control Policy (SCP).

Por esse motivo, não foi registrado `Apply complete!` como evidência.

---

## 3. Upload dos arquivos para o S3

Os arquivos necessários foram enviados manualmente para o bucket:

```bash
aws s3 cp ..\job\rdd_job.py s3://lab-aula05-glue-6325033/scripts/rdd_job.py

aws s3 cp ..\data\sample_lines.txt s3://lab-aula05-glue-6325033/input/sample_lines.txt
```

Uploads concluídos com sucesso.

Estrutura utilizada:

```text
s3://lab-aula05-glue-6325033/
├── input/
│   └── sample_lines.txt
├── scripts/
│   └── rdd_job.py
└── output/
```

---

## 4. Implementação dos RDDs

A função `word_count_rdd` foi implementada utilizando:

- `sc.parallelize(lines)`
- `flatMap`
- conversão das palavras para minúsculas
- `map`
- `reduceByKey`
- ordenação por contagem decrescente
- ordenação alfabética crescente em caso de empate

A função `top_n_palavras` reutiliza `word_count_rdd` e retorna as primeiras `n` palavras.

---

## 5. AWS Glue Job

O Glue Job foi criado manualmente devido à limitação encontrada no `terraform apply`.

Configuração utilizada:

```text
Nome: job-aula05-wordcount
Glue Version: 4.0
Worker Type: G.1X
Number of Workers: 2
Role: arn:aws:iam::441907008326:role/LabRole
Script:
s3://lab-aula05-glue-6325033/scripts/rdd_job.py
```

A configuração foi validada com:

```bash
aws glue get-job --job-name job-aula05-wordcount
```

---

## 6. Execução do Spark/RDD

O Job foi iniciado com:

```bash
aws glue start-job-run
```

### Job Run ID

```text
jr_0c37af7c63b5c760ccb18079c8931d8566183a2a87a4c59e9063efdc02ed6ca2
```

Durante a execução, o processamento RDD foi realizado pelo Spark e o resultado do `word_count` apareceu no CloudWatch.

Resultado observado:

```text
=== Word count (palavra,contagem) ===
o,60
a,22
e,19
pedido,19
cliente,18
entrega,17
do,16
produto,16
estoque,14
pagamento,11
com,9
de,8
um,7
para,6
cada,5
dia,5
mais,5
que,5
ao,4
foi,4
grande,4
novo,4
pediu,4
da,3
muitos,3
na,3
pedidos,3
pelo,3
```

### Interpretação

O processamento demonstrou a execução da lógica de contagem de palavras utilizando RDDs no ambiente gerenciado do AWS Glue. As palavras com maior frequência no conjunto de dados foram `o`, `a`, `e`, `pedido` e `cliente`, indicando maior ocorrência desses termos no conteúdo analisado.

---

## 7. Resultado final da execução

A execução do Job terminou com:

```text
State: FAILED
```

A falha ocorreu durante a etapa de gravação do resultado no S3, e não durante o cálculo do `word_count`.

Erro registrado:

```text
ClassNotFoundException:
Class org.apache.hadoop.mapred.DirectOutputCommitter not found
```

O erro ocorreu durante:

```text
saveAsTextFile
```

Consequentemente, não foi possível obter o arquivo final no prefixo:

```text
s3://lab-aula05-glue-6325033/output/
```

Portanto, a evidência demonstra que o processamento RDD foi executado, mas a gravação final do resultado no S3 não foi concluída.

---

## 8. Limitações encontradas

Durante a execução foram identificadas duas limitações:

1. O `terraform apply` foi bloqueado por uma `explicit deny` de Service Control Policy do ambiente AWS Academy Learner Lab.
2. A execução do Glue Job apresentou `ClassNotFoundException` para `org.apache.hadoop.mapred.DirectOutputCommitter` durante `saveAsTextFile`.

As limitações foram registradas sem alterar a lógica principal da implementação dos RDDs.

---

## 9. Status da atividade

| Etapa                          | Status            |
| ------------------------------ | ----------------- |
| Identidade AWS                 | Concluída         |
| Terraform init                 | Concluída         |
| Terraform validate             | Concluída         |
| Terraform plan                 | Concluída         |
| Terraform apply                | Bloqueada por SCP |
| Upload do script para S3       | Concluída         |
| Upload dos dados para S3       | Concluída         |
| Implementação `word_count_rdd` | Concluída         |
| Implementação `top_n_palavras` | Concluída         |
| Criação do Glue Job            | Concluída         |
| Execução do Spark/RDD          | Executada         |
| Cálculo do Word Count          | Executado         |
| Gravação do resultado no S3    | Falhou            |
| Job `SUCCEEDED`                | Não obtido        |
| `terraform destroy`            | Não executado     |

---

## 10. Conclusão

A atividade permitiu executar a implementação de RDDs no AWS Glue e verificar o processamento do `word_count` em ambiente Spark gerenciado.

A infraestrutura e a execução apresentaram limitações específicas do ambiente AWS Academy Learner Lab. O cálculo das palavras foi executado e registrado no CloudWatch, porém a etapa final de gravação no S3 apresentou erro relacionado ao `DirectOutputCommitter`, impedindo que o Job fosse concluído com status `SUCCEEDED`.
