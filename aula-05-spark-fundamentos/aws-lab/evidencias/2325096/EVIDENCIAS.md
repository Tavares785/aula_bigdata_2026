# Evidências — Lab Aula 05 (Spark RDDs na AWS)

## Identificação

* **Nome:** Eloísa Brandão
* **RA:** 2325096
* **Branch:** aula-05-aws-Eloisa
* **Data:** 19/09/2026

---

## 1. Identidade AWS ativa

Saída de `aws sts get-caller-identity`:

**Comando:**

```bash
aws sts get-caller-identity
```

```text
{
    "UserId": "AROA...:user5367919=Elo__sa_",
    "Account": "093731329001",
    "Arn": "arn:aws:sts::093731329001:assumed-role/voclabs/user5367919=Elo__sa_"
}
```

Print (opcional):

![identidade AWS](01-identity.png)

---

## 2. `terraform apply` concluído

O `terraform apply` foi concluído com sucesso:

```text
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome = "lab-aula05-glue-2325096"
glue_job_nome = "job-aula05-wordcount"
labrole_arn = "arn:aws:iam::093731329001:role/LabRole"
```

Print:

![terraform apply](02-apply.png)

---

## 3. Job com estado SUCCEEDED (Glue)

O job foi executado com sucesso no AWS Glue:

```text
RUN_ID = jr_063fd4a2e654aeb686eaa8df0d5102cd40cdcd524862b9504251a7216c4cbf08
Job terminou com estado: SUCCEEDED.
```

Print:

![job success](03-job-success.png)

---

## 4. Resultado do word count

Saída do `./ver_resultado.sh`:

```text
BUCKET = lab-aula05-glue-2325096

=== Conteudo do word count (palavra,contagem) ===

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
voltou,3
```

Print (opcional):

![resultado word count](04-resultado.png)

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

Interpretação:

> As palavras mais frequentes incluem termos ligados ao contexto de e-commerce, como "pedido" e "cliente", indicando que o texto aborda principalmente operações de compra e atendimento. O processamento foi realizado com RDDs, utilizando o driver para coordenar a execução e os executors para processar os dados distribuídos. O resultado final foi ordenado pela quantidade de ocorrências, com as palavras mais frequentes aparecendo primeiro.

---

## 6. Logs do driver (opcional / bônus)

Print dos logs do driver no CloudWatch:

![logs do driver](05-driver-log.png)

---

## 7. Limpeza (`terraform destroy`)

O `terraform destroy` foi executado após a conclusão do laboratório, removendo os recursos gerenciados pelo Terraform:

```text
Destroy complete!
```

O bucket S3, que não foi gerenciado pelo Terraform devido à restrição de `GetBucketObjectLockConfiguration` do ambiente Learner Lab, também foi removido manualmente após a execução do laboratório.

Print:

![terraform destroy](06-destroy.png)

---

## Checklist de conferência

* [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
* [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
* [x] 3. Job com estado `SUCCEEDED` (Glue) + `RUN_ID`
* [x] 4. Resultado do word count (`./ver_resultado.sh`)
* [x] 5. Top palavras + interpretação
* [ ] 6. Logs do driver (opcional / bônus)
* [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")
