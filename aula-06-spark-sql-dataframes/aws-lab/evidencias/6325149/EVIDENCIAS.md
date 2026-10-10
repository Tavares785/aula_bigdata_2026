# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

## Identificação

- **Nome:** Gabriel Reis Cunha
- **RA:** 6325149
- **Branch:** aula-06-6325149
- **Data:** 2026-10-10

---

## 1. Identidade AWS ativa

**Comando:**
```bash
aws sts get-caller-identity
```

Saída (conta mascarada):
```text
arn:aws:sts::<conta>:assumed-role/voclabs/user5367756=Gabriel_Reis_Cunha
```

Confirmado: não é usuário root; é a role padrão do AWS Academy Learner Lab
(`assumed-role/voclabs/...`). Antes do apply, a conta estava vazia (0 buckets,
0 jobs Glue, 0 log groups `/aws-glue`, 0 instâncias EC2).

---

## 2. `terraform apply` concluído

**Onde:** `cd aws-lab/infra && terraform apply`

`terraform plan` mostrou `Plan: 2 to add, 0 to change, 0 to destroy.`

Saída final:
```text
terraform_data.bucket: Creation complete after 9s [id=20525e83-8027-ccf4-c3d6-46ef0bbf26b8]
aws_glue_job.topn: Creating...
aws_glue_job.topn: Creation complete after 1s [id=job-aula06-topn-clientes]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome = "lab-aula06-glue-6325149"
glue_job_nome = "job-aula06-topn-clientes"
labrole_arn = "arn:aws:iam::<conta>:role/LabRole"
```

---

## 3. Job com estado SUCCEEDED (Glue)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

```text
RUN_ID = jr_de224fe534f8e222e49f49a402aba6dbed9ea36156c361ca50e47d36e2b0f530
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED
Job concluido com SUCESSO.
```

Tempo de execução reportado pelo Glue: 91 s (2 workers G.1X, Glue 4.0).

---

## 4. Resultado do TOP-N de clientes

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

```text
$ aws s3 ls s3://lab-aula06-glue-6325149/output/top_clientes/
2026-10-10 10:08:28        189 part-00000-bd14c1db-1e05-45a0-a685-e4c17c78cf6f-c000.csv

customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

---

## 5. Interpretação do TOP-N

Top-N:
```text
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

Interpretação:

> O `join` entre `pedidos` e `clientes` por `customer_id` trouxe o nome do cliente
> para cada pedido; o `groupBy` por (`customer_id`, `customer_name`) com `F.sum`
> somou o gasto de cada um, e `orderBy(desc)` + `limit(5)` fechou o TOP-5. Isabela
> Nunes (C009) e Diego Ferreira (C004) concentram os maiores gastos, bem acima
> dos demais. O resultado é idêntico ao de um cálculo independente em Python puro
> feito localmente (as diferenças nas últimas casas, como `12928.099999999999`,
> são só ponto flutuante). Como o DataFrame é declarativo, o Spark do Glue
> distribui o trabalho entre o driver e os executors sem eu gerenciar o cluster.

---

## 6. Logs do driver (opcional / bônus)

Não coletado.

---

## 7. Limpeza (`terraform destroy`)

**Onde:** `cd aws-lab/infra && terraform destroy`

```text
aws_glue_job.topn: Destruction complete after 1s
terraform_data.bucket (local-exec): remove_bucket: lab-aula06-glue-6325149
terraform_data.bucket: Destruction complete after 3s

Destroy complete! Resources: 2 destroyed.
```

Verificação posterior (nada restou):
```text
aws s3api head-bucket --bucket lab-aula06-glue-6325149
  -> An error occurred (404) when calling the HeadBucket operation: Not Found
aws glue get-job --job-name job-aula06-topn-clientes
  -> An error occurred (EntityNotFoundException) when calling the GetJob operation: Job not found.
buckets: 0  jobs: 0
```

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [x] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [x] 5. Interpretação do TOP-N (2–3 frases)
- [ ] 6. Logs do driver (opcional / bônus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")
