# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

> Complete este arquivo durante a execução do lab. Salve os prints nesta pasta
> e nunca inclua Access Key, Secret Key ou Session Token.

## Identificação

- **Nome:**Eloísa
- **RA:** 2325096
- **Branch:** aula-06-aws-2325096
- **Data:** 2026-09-26

---

## 1. Identidade AWS ativa

Saída de `aws sts get-caller-identity` (pode mascarar `Account` e `UserId`).

```text
{
	"UserId": "[mascarado]",
	"Account": "[mascarado]",
	"Arn": "arn:aws:sts::[mascarado]:assumed-role/voclabs/[mascarado]"
}
```

---

## 2. `terraform apply` concluído

Inclua "Apply complete!" e os outputs `bucket_nome`, `glue_job_nome` e
`labrole_arn`. Não mostre credenciais.

```text
Apply complete! Resources: 2 added, 0 changed, 1 destroyed.

Outputs:
bucket_nome = "lab-aula06-glue-2325096-330819858615-20260926"
glue_job_nome = "job-aula06-topn-clientes"
labrole_arn = "arn:aws:iam::330819858615:role/LabRole"
```

---

## 3. Job com estado SUCCEEDED (Glue)

Inclua o estado `SUCCEEDED` e o `RUN_ID` (`JobRunId`).

```text
RUN_ID = jr_dd0c0918ba0bc6f4026c5f46f1a442487bc184536dfbaddbd00a99d03339411a
estado: SUCCEEDED
Job concluido com SUCESSO.
```

Print: `03-job-success.png`

---

## 4. Resultado do TOP-N de clientes

Cole a saída de `./ver_resultado.sh`, incluindo `customer_id`, `customer_name`
e `total_spend`.

```text
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

Print: `04-resultado.png`

---

## 5. Interpretação do TOP-N

```text
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

Após o `join` por `customer_id`, os DataFrames foram agrupados por cliente e as
compras somadas; Isabela Nunes lidera (R$ 12.928,10), seguida por Diego Ferreira
(R$ 9.862,40). A ordenação decrescente com `limit(5)` seleciona os maiores gastos;
o driver coordena o job Spark e os executors processam as partições. Os dígitos
extras em alguns totais são artefatos de ponto flutuante; para leitura em centavos,
os valores devem ser arredondados para duas casas decimais.


---

## 6. Logs do driver (opcional / bônus)

Print do CloudWatch no grupo `/aws-glue/jobs/output`:

`05-driver-log.png`

---

## 7. Limpeza (`terraform destroy`)

Inclua "Destroy complete!" para confirmar a remoção dos recursos.

```text
Destroy complete! Resources: 2 destroyed.
```

Print: `06-destroy.png`

---

## Checklist de conferência

- [x] Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] `terraform apply` concluído com outputs
- [x] Glue Job `SUCCEEDED` com `JobRunId`
- [x] Resultado do TOP-N
- [x] Interpretação em 2–3 frases
- [ ] Logs do driver (opcional)
- [x] `terraform destroy` concluído