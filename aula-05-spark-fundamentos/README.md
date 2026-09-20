# Lab - Aula 05: Fundamentos do Spark (RDDs) na AWS

Este lab executa as operações com **RDDs (Resilient Distributed Datasets)** do
Spark em um **Spark gerenciado na nuvem** — o **AWS EMR Serverless** —
provisionado com **Terraform** e rodando dentro do **AWS Academy Learner Lab**.
Você envia o script e os dados para o S3, submete um job e lê o resultado de
volta, sem precisar manter um cluster ligado.

## Onde está o lab

Todo o material do lab está na subpasta [`aws-lab/`](aws-lab/). O passo a passo
completo (credenciais, Terraform, submissão do job e limpeza) está em
[`aws-lab/README.md`](aws-lab/README.md).

## Estrutura

```
aws-lab/
├── README.md            # passo a passo completo
├── infra/               # Terraform (S3 + EMR Serverless)
├── job/rdd_job.py       # script PySpark de RDDs (TODOs do aluno)
├── scripts/             # run_job.sh, ver_resultado.sh
├── evidencias/          # entrega das evidências por RA (TEMPLATE.md)
└── data/sample_lines.txt
```

## Objetivo

- Praticar **RDDs**: word count com `flatMap` / `map` / `reduceByKey`.
- Entender o papel de **driver** e **executors** num Spark gerenciado.
- Usar o **S3** como armazenamento (entrada, script, saída e logs).

## Como começar

Siga o passo a passo em [`aws-lab/README.md`](aws-lab/README.md).

## Entrega

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-05-aws-SEURA`.
3. Coloque seus artefatos na pasta do seu **RA**.
4. Inclua suas evidências em `aws-lab/evidencias/<RA>/` (copie e preencha
   `aws-lab/evidencias/TEMPLATE.md`) — veja o passo a passo em
   [`aws-lab/README.md`](aws-lab/README.md).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch original.
