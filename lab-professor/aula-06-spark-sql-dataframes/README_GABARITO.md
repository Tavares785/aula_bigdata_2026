# Gabarito — Aula 06 (Spark SQL / DataFrames no AWS Glue)

> ⚠️ **Uso interno do professor. NÃO distribuir ao aluno.**
> Esta pasta contém a **solução de referência** (versão RESOLVIDA) do lab AWS da
> aula-06. O lab do aluno, com o esqueleto e os TODOs entregues à turma, fica em
> [`aula-06-spark-sql-dataframes/aws-lab/`](../../aula-06-spark-sql-dataframes/aws-lab/)
> — nada lá foi alterado.

## O que o aluno realmente resolve

A **infra (Terraform) já vem PRONTA** no lab do aluno: um bucket S3 privado
(único, com prefixos `scripts/`, `input/`, `output/`, `logs/` e `tmp/`) + um
**AWS Glue Job** (`glueetl`, Spark 4.0), usando a `LabRole` por ARN como IAM
role de execução. Não há nada a "resolver" na infra.

> **Por que Glue e não EMR Serverless?** Neste Learner Lab o EMR Serverless está
> bloqueado (a `LabRole` não confia em `emr-serverless.amazonaws.com`), mas o
> Glue funciona (a `LabRole` confia em `glue.amazonaws.com`). Por isso o lab foi
> convertido para Glue. É o mesmo serviço usado na prova deste repositório.

O que o aluno preenche são **as duas funções de DataFrame** em
`job/dataframe_job.py` (`total_revenue_by_category` e `top_n_customers_by_spend`,
que no esqueleto levantam `NotImplementedError`). As funções
`filter_high_value_sales` e `join_orders_with_customers` **já vêm prontas** como
referência (modelo de uso da API de DataFrames). Portanto, o gabarito essencial
desta aula é o **`job/dataframe_job.py` resolvido**.

## Árvore de arquivos do gabarito

```
lab-professor/aula-06-spark-sql-dataframes/
├── README_GABARITO.md               # este arquivo
├── infra/                           # idêntica à do aluno (já vem pronta, Glue)
│   ├── versions.tf                  # Terraform >= 1.5.0, provider aws ~> 5.0
│   ├── variables.tf                 # regiao, labrole_arn, bucket_nome, tags
│   ├── main.tf                      # S3 privado + aws_glue_job "topn" (glueetl)
│   ├── outputs.tf                   # bucket_nome, glue_job_nome, labrole_arn
│   └── terraform.tfvars.example     # modelo de variáveis (sem credenciais)
├── data/                            # cópia dos CSVs (main.tf os sobe via filemd5)
│   ├── pedidos.csv                  # order_id, customer_id, category, value
│   └── clientes.csv                 # customer_id, customer_name, customer_uf
└── job/
    └── dataframe_job.py             # RESOLVIDO: total_revenue_by_category
                                     #            + top_n_customers_by_spend
                                     # (filter/join já vêm prontos como referência)
```

## Como validar / rodar (mesmos comandos do lab)

> Região obrigatória: **us-east-1**. As credenciais do Learner Lab são
> temporárias e expiram por sessão — reconfigure a cada início. **Nunca**
> versione credenciais.

### 1. Configurar credenciais temporárias

Copie Access Key / Secret Key / Session Token do painel **AWS Details** e exporte:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Provisionar a infra

```bash
cd lab-professor/aula-06-spark-sql-dataframes/infra
cp terraform.tfvars.example terraform.tfvars
# edite terraform.tfvars: labrole_arn (ARN da LabRole da sua conta) e
# bucket_nome (nome global único).

terraform init
terraform validate
terraform plan
terraform apply
```

O `apply` cria o bucket S3 privado e o Glue Job, e **já sobe o script
(`scripts/dataframe_job.py`) e os DOIS CSVs de entrada
(`input/pedidos.csv` e `input/clientes.csv`)** ao S3. Anote os outputs
(`bucket_nome`, `glue_job_nome`, `labrole_arn`).

### 3. Disparar o Glue Job

O caminho mais rápido é **reaproveitar os scripts do aluno** em
[`../../aula-06-spark-sql-dataframes/aws-lab/scripts/`](../../aula-06-spark-sql-dataframes/aws-lab/scripts/).
O `run_job.sh` re-envia o script/dados, limpa a saída anterior, dispara o job e
faz polling do estado (`STARTING → RUNNING → SUCCEEDED/FAILED`):

```bash
cd ../../aula-06-spark-sql-dataframes/aws-lab/scripts
BUCKET=<bucket_nome> GLUE_JOB=<glue_job_nome> ./run_job.sh
```

> Para validar o **gabarito**, aponte o `run_job.sh` para o `dataframe_job.py`
> resolvido desta pasta (ou copie-o por cima) antes de disparar — o script
> re-envia o `job/dataframe_job.py` para o S3 automaticamente.

Como alternativa, o disparo manual equivalente (a IAM role já está no Job, então
não se passa role no `start-job-run`):

```bash
aws glue start-job-run \
  --job-name <glue_job_nome> \
  --region us-east-1 \
  --query 'JobRunId' --output text
```

Para acompanhar o estado de um run específico:

```bash
aws glue get-job-run \
  --job-name <glue_job_nome> \
  --run-id <JobRunId> \
  --region us-east-1 \
  --query 'JobRun.JobRunState' --output text
# estados: STARTING -> RUNNING -> SUCCEEDED / FAILED / TIMEOUT / STOPPED
```

### 4. Ver o resultado

```bash
cd ../../aula-06-spark-sql-dataframes/aws-lab/scripts
BUCKET=<bucket_nome> ./ver_resultado.sh
# ou diretamente (a saída é um CSV part-*.csv com header):
aws s3 cp "s3://<bucket_nome>/output/top_clientes/" - --recursive
```

Os logs do driver (inclusive o `print` do TOP-N de clientes) ficam no
**CloudWatch**, no grupo `/aws-glue/jobs/output` (erros em
`/aws-glue/jobs/error`).

### 5. Limpeza (obrigatória ao final)

```bash
cd lab-professor/aula-06-spark-sql-dataframes/infra
terraform destroy
```

## Saída esperada (TOP-5 clientes por gasto)

Rodando o `dataframe_job.py` resolvido sobre os CSVs do lab
([`data/pedidos.csv`](data/pedidos.csv) + [`data/clientes.csv`](data/clientes.csv)):

- **Clientes:** 15
- **Pedidos:** 60
- **Categorias:** 4

**TOP-5** (`customer_id,customer_name,total_spend`, ordenado por `total_spend`
decrescente):

```
C009,Isabela Nunes,12928.1
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.09
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

> Complemento — **receita total por categoria** (`total_revenue_by_category`,
> ordem decrescente), útil para conferir a agregação:
>
> ```
> eletronicos,32995.54
> moveis,9865.3
> vestuario,2008.79
> livros,1149.1
> ```

## Correção automática (CI)

Esta aula **não tem rubrica separada**. A verificação automática é o **CI leve**
que roda em cada alteração:

- `terraform fmt` / `terraform validate` na infra.
- `python3 -m py_compile` no `job/dataframe_job.py`.
