# Gabarito — Aula 05 (Spark/RDDs no AWS Glue)

> ⚠️ **Uso interno do professor. NÃO distribuir ao aluno.**
> Esta pasta contém a **solução de referência** (versão RESOLVIDA) do lab AWS da
> aula-05. O lab do aluno, com o esqueleto e os TODOs entregues à turma, fica em
> [`aula-05-spark-fundamentos/aws-lab/`](../../aula-05-spark-fundamentos/aws-lab/)
> — nada lá foi alterado.

## O que o aluno realmente resolve

A **infra (Terraform) já vem PRONTA** no lab do aluno: um bucket S3 privado
(único, com prefixos `scripts/`, `input/`, `output/`, `logs/`) + um **AWS Glue
Job** (`glueetl`, Spark 4.0), usando a `LabRole` por ARN como IAM role de
execução. Não há nada a "resolver" na infra.

> **Por que Glue e não EMR Serverless?** Neste Learner Lab o EMR Serverless está
> bloqueado (a `LabRole` não confia em `emr-serverless.amazonaws.com`), mas o
> Glue funciona (a `LabRole` confia em `glue.amazonaws.com`). Por isso o lab foi
> convertido para Glue.

O que o aluno preenche são **as duas funções de RDD** em `job/rdd_job.py`
(`word_count_rdd` e `top_n_palavras`, que no esqueleto levantam
`NotImplementedError`). Portanto, o gabarito essencial desta aula é o
**`job/rdd_job.py` resolvido**.

## Árvore de arquivos do gabarito

```
lab-professor/aula-05-spark-fundamentos/
├── README_GABARITO.md               # este arquivo
├── infra/                           # idêntica à do aluno (já vem pronta, Glue)
│   ├── versions.tf                  # Terraform >= 1.5.0, provider aws ~> 5.0
│   ├── variables.tf                 # regiao, labrole_arn, bucket_nome, tags
│   ├── main.tf                      # S3 privado + aws_glue_job "wordcount" (glueetl)
│   ├── outputs.tf                   # bucket_nome, glue_job_nome, labrole_arn
│   └── terraform.tfvars.example     # modelo de variáveis (sem credenciais)
└── job/
    └── rdd_job.py                   # RESOLVIDO: word_count_rdd + top_n_palavras
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
cd lab-professor/aula-05-spark-fundamentos/infra
cp terraform.tfvars.example terraform.tfvars
# edite terraform.tfvars: labrole_arn (ARN da LabRole da sua conta) e
# bucket_nome (nome global único).

terraform init
terraform validate
terraform plan
terraform apply
```

O `apply` cria o bucket S3 privado e o Glue Job, e **já sobe o script
(`scripts/rdd_job.py`) e o dado de entrada (`input/sample_lines.txt`)** ao S3.
Anote os outputs (`bucket_nome`, `glue_job_nome`, `labrole_arn`).

### 3. Disparar o Glue Job

O caminho mais rápido é **reaproveitar os scripts do aluno** em
[`../../aula-05-spark-fundamentos/aws-lab/scripts/`](../../aula-05-spark-fundamentos/aws-lab/scripts/).
O `run_job.sh` re-envia o script/dado, limpa a saída anterior, dispara o job e
faz polling do estado (`STARTING → RUNNING → SUCCEEDED/FAILED`):

```bash
cd ../../aula-05-spark-fundamentos/aws-lab/scripts
BUCKET=<bucket_nome> GLUE_JOB=<glue_job_nome> ./run_job.sh
```

> Para validar o **gabarito**, aponte o `run_job.sh` para o `rdd_job.py`
> resolvido desta pasta (ou copie-o por cima) antes de disparar — o script
> re-envia o `job/rdd_job.py` para o S3 automaticamente.

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
cd ../../aula-05-spark-fundamentos/aws-lab/scripts
BUCKET=<bucket_nome> ./ver_resultado.sh
# ou diretamente:
aws s3 cp "s3://<bucket_nome>/output/wordcount/" - --recursive
```

Os logs do driver (inclusive o `print` do word count) ficam no **CloudWatch**,
no grupo `/aws-glue/jobs/output` (erros em `/aws-glue/jobs/error`).

### 5. Limpeza (obrigatória ao final)

```bash
cd lab-professor/aula-05-spark-fundamentos/infra
terraform destroy
```

## Saída esperada (com o `data/sample_lines.txt` do lab)

Rodando o word count resolvido sobre
[`aula-05-spark-fundamentos/aws-lab/data/sample_lines.txt`](../../aula-05-spark-fundamentos/aws-lab/data/sample_lines.txt):

- **Linhas:** 44
- **Palavras (total):** 455
- **Palavras distintas:** 167

**TOP 10** (`palavra,contagem`, ordenado por contagem desc e, em empate,
alfabética asc):

```
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
```

> Observação sobre o empate em `19`: a regra é **contagem desc primeiro** e, em
> empate, **ordem alfabética asc**. Como `e` e `pedido` têm a mesma contagem
> (19), desempata pela palavra: `e` < `pedido`, então `e,19` vem antes de
> `pedido,19`.

## Correção automática (CI)

Esta aula **não tem rubrica separada**. A verificação automática é o **CI leve**
que roda em cada alteração:

- `terraform fmt` / `terraform validate` na infra.
- `python3 -m py_compile` no `job/rdd_job.py`.
