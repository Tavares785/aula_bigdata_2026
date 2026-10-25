# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

## Identificação

- **Nome:** Matheus Mantovani
- **RA:** 1120245
- **Branch:** aula-06-aws-1120245
- **Conta AWS:** 864636683316
- **Região:** us-east-1
- **Bucket:** lab-aula06-glue-1120245
- **Glue Job:** job-aula06-topn-clientes

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [x] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [x] 5. Interpretação do TOP-N (2–3 frases)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")

---

## 1. Identidade AWS ativa

```json
{
    "UserId": "AROAYXOECQOVWL7BKJZBB:MasterKey",
    "Account": "864636683316",
    "Arn": "arn:aws:sts::864636683316:assumed-role/LabRole/MasterKey"
}
```

---

## 2. Terraform apply

```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:
bucket_nome   = "lab-aula06-glue-1120245"
glue_job_nome = "job-aula06-topn-clientes"
labrole_arn   = "arn:aws:iam::864636683316:role/LabRole"
```

---

## 3. Job SUCCEEDED

```
RUN_ID = jr_6d6ac7c474d2ad0a3d7f2fabac0d4a3dabd14d9a6b90c460d1023b7497e9db5d

estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED

Job concluído com SUCESSO.
```

---

## 4. Resultado do TOP-N de clientes

```
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

---

## 5. Interpretação do TOP-N

O resultado mostra os 5 clientes com maior gasto total no dataset. Isabela Nunes
lidera com R$ 12.928,10 em compras, seguida de Diego Ferreira com R$ 9.862,40 —
juntos representam mais de 60% do faturamento total do top-5. A diferença expressiva
entre o 2º e o 3º lugar (Ana Souza, R$ 3.612,09) indica que os dois primeiros
clientes são outliers de alto valor, um padrão comum em bases de e-commerce onde
uma minoria concentra grande parte da receita.

---

## 7. Terraform destroy

```
Destroy complete! Resources: 2 destroyed.
```

Bucket `lab-aula06-glue-1120245` e Glue Job `job-aula06-topn-clientes` removidos
com sucesso. Sem recursos residuais na conta.
