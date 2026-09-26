# Lab - Aula 06: Spark SQL e DataFrames na AWS

Este lab executa operações de **Spark SQL / DataFrames** em um **Spark gerenciado
na nuvem** — o **AWS Glue** — provisionado com **Terraform** e rodando dentro do
**AWS Academy Learner Lab**. Você envia o script e os dados (dois CSVs:
`pedidos.csv` e `clientes.csv`) para o S3, dispara um Glue Job e lê de volta o
**TOP-N de clientes por gasto**, sem precisar manter um cluster ligado.

## Onde está o lab

Todo o material do lab está na subpasta [`aws-lab/`](aws-lab/). O passo a passo
completo (credenciais, Terraform, submissão do job e limpeza) está em
[`aws-lab/README.md`](aws-lab/README.md).

## Estrutura

```
aws-lab/
├── README.md                 # passo a passo completo
├── infra/                    # Terraform (S3 + AWS Glue Job)
├── job/dataframe_job.py      # script PySpark completo de DataFrames/Spark SQL
├── scripts/                  # run_job.sh, ver_resultado.sh
├── evidencias/               # entrega das evidências por RA (TEMPLATE.md)
└── data/
    ├── pedidos.csv           # order_id, customer_id, category, value
    └── clientes.csv          # customer_id, customer_name, customer_uf
```

## Objetivo

- Praticar **DataFrames / Spark SQL**: `filter`, `groupBy` + agregação (`F.sum`),
  `join` e **top-N**.
- Entender a diferença entre **DataFrames** e **RDDs** (API declarativa,
  otimizada pelo Catalyst, sobre dados estruturados).
- Usar o **S3** como armazenamento (dois inputs, script, saída e logs) e o papel
  de **driver** e **executors** num Spark gerenciado.

## Como começar

Siga o passo a passo em [`aws-lab/README.md`](aws-lab/README.md).

## Entrega

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-06-aws-SEURA`.
3. Coloque seus artefatos na pasta do seu **RA**.
4. Inclua suas evidências em `aws-lab/evidencias/<RA>/` (copie e preencha
   `aws-lab/evidencias/TEMPLATE.md`) — veja o passo a passo em
   [`aws-lab/README.md`](aws-lab/README.md).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch original.
