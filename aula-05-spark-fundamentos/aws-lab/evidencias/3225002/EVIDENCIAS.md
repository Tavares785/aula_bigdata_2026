# Evidências — Lab Aula 05 (Spark RDDs na AWS)

## Identificação

- **Nome:** José Henrique Teixeira Luiz
- **RA:** 3225002
- **Branch:** aula-05-aws-3225002
- **Data:** 16/09/2026

Executado no **AWS Academy Learner Lab** (conta `079673385710`, `us-east-1`),
com a versão **AWS Glue** do lab.

---

## 1. Identidade AWS ativa

**Comando:**
```bash
aws sts get-caller-identity
```

Saída:
```text
{
    "UserId": "AROARFDHHMLXOEH2OYJYH:user5367843=Jos___Henrique_Teixeira_Luiz",
    "Account": "079673385710",
    "Arn": "arn:aws:sts::079673385710:assumed-role/voclabs/user5367843=Jos___Henrique_Teixeira_Luiz"
}
```

---

## 2. `terraform apply` concluído

**Onde:** `cd aws-lab/infra && terraform apply`

```text
$ terraform validate
Success! The configuration is valid.

$ terraform plan
Plan: 5 to add, 0 to change, 0 to destroy.
```

O **primeiro** `apply` falhou ao criar o bucket:

```text
Error: reading S3 Bucket (lab-aula05-glue-3225002) object lock configuration: operation error S3: Ge
tObjectLockConfiguration, https response error StatusCode: 403, RequestID: MRT7AJNHYVTAR04Z, HostID:
 GkfnOmPxKPBSgif7HxbZqlmCzDwyLH95dVn9wONVLWXUflh7CIcJgvSTAZYCP8pjE7tYzSK77mY=, api error AccessDenie
d: User: arn:aws:sts::079673385710:assumed-role/voclabs/user5367843=Jos___Henrique_Teixeira_Luiz is 
not authorized to perform: s3:GetBucketObjectLockConfiguration on resource: "arn:aws:s3:::lab-aula05
-glue-3225002" with an explicit deny in a service control policy: arn:aws:organizations::58413773324
7:policy/o-sj1klpmtnw/service_control_policy/p-2whlmd68
```

A **Service Control Policy** da organização do Academy nega
`s3:GetBucketObjectLockConfiguration`, que o provider AWS v5 lê logo depois de
criar um `aws_s3_bucket`. O bucket é criado, mas fica *tainted* e o apply para.
Contorno, sem alterar o `main.tf`:

```bash
terraform untaint aws_s3_bucket.lab
terraform apply -refresh=false
```

Segundo `apply`:

```text
aws_s3_object.script: Creation complete after 1s [id=scripts/rdd_job.py]
aws_s3_object.input: Creation complete after 1s [id=input/sample_lines.txt]
aws_s3_bucket_public_access_block.lab: Creation complete after 1s [id=lab-aula05-glue-3225002]
aws_glue_job.wordcount: Creation complete after 2s [id=job-aula05-wordcount]
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
```

Outputs:

```text
bucket_nome = "lab-aula05-glue-3225002"
glue_job_nome = "job-aula05-wordcount"
labrole_arn = "arn:aws:iam::079673385710:role/LabRole"
```

---

## 3. Job com estado SUCCEEDED (Glue)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

```text
BUCKET   = lab-aula05-glue-3225002
GLUE_JOB = job-aula05-wordcount
ROLE_ARN = arn:aws:iam::079673385710:role/LabRole
$ aws glue start-job-run --job-name job-aula05-wordcount ...
RUN_ID = jr_7cc273f7f39030fc2f117748de9cfd0c0073cab1def7b0c453e683d6d8eaa2be
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED
Job concluido com SUCESSO.
```

### ⚠️ A primeira execução falhou — e a causa estava no `main()`

```text
estado: FAILED
ErrorMessage: An error occurred while calling o177.saveAsTextFile. java.lang.RuntimeException: java.
lang.ClassNotFoundException: Class org.apache.hadoop.mapred.DirectOutputCommitter not found
```

O runtime do **Glue 4.0** define por padrão
`mapred.output.committer.class = org.apache.hadoop.mapred.DirectOutputCommitter`,
uma classe legada que **não existe** no Hadoop 3 usado pelo próprio Glue 4.0. O
`saveAsTextFile` de RDD usa a API antiga (`mapred`) e lê essa configuração.

**Não é erro nas funções do aluno** — o job passou pelo `word_count_rdd` e só
quebrou na gravação. Correção aplicada no `main()`, antes do `saveAsTextFile`:

```python
sc._jsc.hadoopConfiguration().set(
    "mapred.output.committer.class",
    "org.apache.hadoop.mapred.FileOutputCommitter",
)
```

Com ela, a execução seguinte terminou em `SUCCEEDED` (acima).

---

## 4. Resultado do word count

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Arquivos gravados no S3:

```text
$ aws s3 ls s3://lab-aula05-glue-3225002/output/wordcount/
2026-09-16 21:50:22        311 part-00000
2026-09-16 21:50:22        377 part-00001
2026-09-16 21:50:22        377 part-00002
2026-09-16 21:50:22        394 part-00003
```

**Quatro partições** — uma por núcleo do worker `G.1X` (4 vCPU). No teste local
com `local[2]` foram duas. É a mesma coleção, dividida conforme os recursos do
cluster.

Conteúdo (**167 palavras distintas**, **455 ocorrências** — o
mesmo número de *tokens* do arquivo de entrada):

```text
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
...
```

> Cada `part-*` está ordenado internamente; ao concatenar as quatro, a ordem
> global se perde. A ordenação completa do contrato é a que o driver imprime
> (seção 6), feita **antes** do `parallelize` que redistribui para a escrita.

---

## 5. Top palavras / interpretação

Top 5:
```text
o,60
a,22
e,19
pedido,19
cliente,18
```

**Interpretação:**

> As três primeiras posições são **stopwords** (`o`, `a`, `e`) — artigos e
> conjunções que aparecem em quase toda frase e não dizem nada sobre o assunto,
> porque o contrato do `word_count_rdd` não pede filtragem. Logo abaixo vêm
> `pedido`, `cliente`, `entrega`, `produto` e `estoque`, que revelam o domínio:
> o texto descreve o **ciclo de um pedido de e-commerce**. Filtrar as stopwords
> no `flatMap` seria o passo natural — e, feito ali, antes do `reduceByKey`,
> também reduziria o volume que os *executors* trocam entre si no shuffle.

---

## 6. Logs do driver (bônus)

**Onde:** CloudWatch, grupo `/aws-glue/jobs/output`, stream do run
`jr_7cc273f7f39030fc2f117…`

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
...
Resultado gravado em: s3://lab-aula05-glue-3225002/output/wordcount
```

O `print` sai do **driver**, depois do `collect()` que trouxe o resultado dos
*executors* de volta. Por isso aqui a ordem é a global do contrato — diferente
dos arquivos da seção 4, gravados em paralelo pelos executors.

---

## 7. Limpeza (`terraform destroy`)

**Onde:** `cd aws-lab/infra && terraform destroy`

O bucket precisou ser esvaziado antes: `output/`, `tmp/` e os artefatos do job
**não** são recursos do Terraform, e um bucket com objetos não pode ser removido.

```bash
aws s3 rm s3://lab-aula05-glue-3225002 --recursive
terraform destroy -refresh=false     # -refresh=false pelo mesmo motivo da seção 2
```

```text
Destroy complete! Resources: 5 destroyed.
```

Conta verificada ao final:

```text
buckets do lab: 0
glue jobs:      0
```

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (+ `RUN_ID`)
- [x] 4. Resultado do word count (`./ver_resultado.sh`)
- [x] 5. Top palavras + interpretação
- [x] 6. Logs do driver (bônus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")

---

## Dois problemas que a turma vai encontrar

1. **Bucket S3 quebra no primeiro apply** (SCP de *object lock*). Contorno:
   `terraform untaint aws_s3_bucket.lab` + `terraform apply -refresh=false` —
   e `-refresh=false` também no `destroy`.
2. **`saveAsTextFile` falha no Glue 4.0** com
   `ClassNotFoundException: DirectOutputCommitter`. Contorno: configurar o
   `FileOutputCommitter` no `main()` antes da gravação (seção 3).
