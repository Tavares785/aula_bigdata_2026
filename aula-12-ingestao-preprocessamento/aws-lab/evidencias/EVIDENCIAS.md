# Evidências — Lab Aula 12 (Ingestão e Pré-processamento)

## Identificação

- **Nome:** Luiza Rolfsen
- **Branch:** aula-12-aws-6325257
- **Data:** 2026-11-18

---

## 1. `terraform apply` concluído

Print do `aws glue get-job` mostrando o job criado com `GlueVersion: 4.0`, `Role: LabRole`
e `ScriptLocation: s3://mercadofacil-grupo3/scripts/etl.py`.


## 2. Glue Job SUCCEEDED

Saída do `run_job.sh` mostrando `Status: SUCCEEDED` e o `JobRunId`.

```
JobRunId: jr_614307776f1475155a5d500e94d4895d94c2c6d5be9169d54970223fe89e42a4
Status: SUCCEEDED
```


## 3. Consulta Athena na tabela gold

Consulta na tabela `atrasos_por_transportadora_estado` do banco `mercadofacil_db`
mostrando as colunas: `transportadora`, `estado`, `total_entregas`, `total_atrasadas`,
`media_atraso_dias`, `media_nota`, `pct_atrasadas`.


---

## 4. `terraform destroy` concluído

Saída do `terraform destroy` mostrando remoção dos arquivos do S3 e
`Destroy complete! Resources: 6 destroyed`.


## Checklist

- [x] 1. `terraform apply` concluído
- [x] 2. Glue Job `SUCCEEDED` com `JobRunId`
- [x] 3. Consulta Athena na tabela gold
- [x] 4. `terraform destroy` concluído

![alt text](<Captura de tela 2026-11-18 205246.png>) ![alt text](<Captura de tela 2026-11-18 222025.png>) ![alt text](<Captura de tela 2026-11-18 221927.png>) ![alt text](<Captura de tela 2026-11-18 221456.png>) ![alt text](<Captura de tela 2026-11-18 205317.png>) ![alt text](<Captura de tela 2026-11-18 205304.png>)