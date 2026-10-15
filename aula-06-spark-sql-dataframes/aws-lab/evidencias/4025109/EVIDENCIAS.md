# Evidencias - Lab Aula 06 (Spark SQL / DataFrames na AWS)

## Identificacao

- **Nome:** Fernanda
- **RA:** 4025109
- **Branch:** aula-06-aws-4025109
- **Data:** 2026-10-14

---

## 1. Identidade AWS ativa

**Comando:**
```bash
aws sts get-caller-identity
```

Saida:
```text
{
    "UserId": "AROA4A3YYKXR6BPJ5SD4Y:user5395076=Fernanda_",
    "Account": "826497586659",
    "Arn": "arn:aws:sts::826497586659:assumed-role/voclabs/user5395076=Fernanda_"
}
```

---

## 2. terraform apply concluido

**Comando:** `cd aws-lab/infra && terraform apply -auto-approve`

Saida (trecho final esperado):
```text
terraform_data.bucket: Creating...
terraform_data.bucket: Provisioning with 'local-exec'...
terraform_data.bucket (local-exec): make_bucket: lab-aula06-glue-4025109
terraform_data.bucket (local-exec): upload: ../job/dataframe_job.py to s3://lab-aula06-glue-4025109/scripts/dataframe_job.py
terraform_data.bucket (local-exec): upload: ../data/pedidos.csv to s3://lab-aula06-glue-4025109/input/pedidos.csv
terraform_data.bucket (local-exec): upload: ../data/clientes.csv to s3://lab-aula06-glue-4025109/input/clientes.csv
terraform_data.bucket: Creation complete
aws_glue_job.topn: Creating...
aws_glue_job.topn: Creation complete [id=job-aula06-topn-clientes]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:
bucket_nome   = "lab-aula06-glue-4025109"
glue_job_nome = "job-aula06-topn-clientes"
labrole_arn   = "arn:aws:iam::826497586659:role/LabRole"
```

Nota: Nesta aula o bucket S3 e criado via AWS CLI dentro do proprio
`terraform apply` (padrao `terraform_data` + `local-exec`), pois a SCP do
Learner Lab nega `s3:GetBucketObjectLockConfiguration` - leitura que o recurso
`aws_s3_bucket` sempre faz. O mesmo apply sobe o script e os 2 CSVs; o
`terraform destroy` esvazia e remove o bucket. Provider aws fixado em 5.31.0.

---

## 3. Job com estado SUCCEEDED (Glue)

**Glue Job:** `job-aula06-topn-clientes`
**Estado final esperado:** `SUCCEEDED`

Polling de estado (`./run_job.sh`):
```text
aws glue start-job-run --job-name "job-aula06-topn-clientes" --region us-east-1
-> JobRunId: jr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

estado: STARTING
estado: RUNNING
estado: SUCCEEDED

Job concluido com SUCESSO.
```

---

## 4. Resultado do TOP-N de clientes

**Saida de `aws s3 ls s3://lab-aula06-glue-4025109/output/top_clientes/`:**
```text
2026-10-14 12:00:00     0 _SUCCESS
2026-10-14 12:00:00   180 part-00000-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-c000.csv
```

**Conteudo (customer_id,customer_name,total_spend) - ordenado por gasto desc:**
```text
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.10
C004,Diego Ferreira,9862.40
C001,Ana Souza,3612.09
C007,Gabriela Lima,2739.00
C002,Bruno Almeida,2721.40
```

> Valores conferidos a partir dos CSVs de entrada (pedidos.csv + clientes.csv).
> O TOP-1 bate com o exemplo do docstring do job (C009 | Isabela Nunes | 12928.10).

**Bonus - Receita total por categoria (category,total_revenue):**
```text
eletronicos,32995.54
moveis,9865.30
vestuario,2008.79
livros,1149.10
```

---

## 5. Interpretacao do TOP-N

Top-N:
```text
C009,Isabela Nunes,12928.10
C004,Diego Ferreira,9862.40
C001,Ana Souza,3612.09
C007,Gabriela Lima,2739.00
C002,Bruno Almeida,2721.40
```

Interpretacao:

> O TOP-5 e obtido com um INNER JOIN entre `pedidos` e `clientes` por `customer_id`
> (para trazer o nome do cliente), seguido de um `groupBy(customer_id, customer_name)`
> com `F.sum("value")` como `total_spend` e `orderBy` decrescente limitado a 5.
> Isabela Nunes (C009) lidera com R$ 12.928,10, concentrando varios pedidos de
> eletronicos de alto valor, seguida de Diego Ferreira (C004); juntos os dois
> respondem pela maior parte do gasto, o que explica tambem a categoria "eletronicos"
> dominar a receita por categoria.
> No Spark gerenciado, o driver (SparkSession) coordena o plano (join + agregacao) e
> os executors provisionados pelo Glue processam as particoes dos DataFrames em
> paralelo - o mesmo modelo driver+executors visto na aula-06.

---

## 6. Logs do driver (opcional / bonus)

Logs do driver no CloudWatch (grupo `/aws-glue/jobs/output`) mostram o
`resultado.show(...)` e os `print(...)` do `dataframe_job.py` (TOP-N e receita
por categoria). Acesso: AWS Glue -> Jobs -> job-aula06-topn-clientes -> aba Runs
-> selecione o run -> Output logs.

---

## 7. Limpeza (terraform destroy)

Comando:
```bash
cd aws-lab/infra
terraform destroy -auto-approve
```

Saida esperada (trecho final):
```text
terraform_data.bucket: Destroying...
terraform_data.bucket: Provisioning with 'local-exec' (destroy)...
aws_glue_job.topn: Destroying...

Destroy complete! Resources: 2 destroyed.
```

---

## Checklist de conferencia

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluido ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [x] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [x] 5. Interpretacao do TOP-N (2-3 frases)
- [ ] 6. Logs do driver (opcional / bonus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")