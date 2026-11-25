# Evidências - Aula 12: Ingestão e Pré-processamento

Prints da execução do pipeline no AWS Academy Learner Lab (conta
`269622000641`, região `us-east-1`). Credenciais mascaradas.

| # | Evidência | Arquivo |
|---|---|---|
| 1 | `terraform apply` concluído (6 recursos criados) | `01-apply.png` |
| 2 | Glue Job `mercadofacil-etl-pedidos` com status `SUCCEEDED` | `02-glue-job.png` |
| 3 | Consulta no Athena sobre a gold | `03-athena.png` |
| 4 | `terraform destroy` concluído | `04-destroy.png` |

## Glue Job

- Job: `mercadofacil-etl-pedidos`
- JobRunId: `jr_aafbaed12aae867e24b50ed914019249d50165e260392d1ab6c98bb6ee9456f0`
- Estado final: `SUCCEEDED`

## Consulta do Athena

```sql
SELECT faixa_atraso, itens_avaliados, nota_media, pct_nota_baixa
FROM mercadofacil_db.nota_por_faixa_atraso
ORDER BY faixa_atraso
```

| faixa_atraso | itens_avaliados | nota_media | pct_nota_baixa |
|---|---|---|---|
| 1_no_prazo | 6489 | 4.12 | 9.91 |
| 2_atraso_1_a_3_dias | 548 | 3.32 | 20.44 |
| 3_atraso_4_a_7_dias | 746 | 2.54 | 53.08 |
| 4_atraso_8_ou_mais_dias | 577 | 2.2 | 65.16 |
