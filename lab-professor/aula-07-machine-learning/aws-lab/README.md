# Aula 07 — DEMO DO PROFESSOR: Previsão de direção de ações com Spark MLlib na AWS (AWS Glue)

Demo **passo a passo** do **professor** para a aula-07: um pipeline de
**classificação binária** que prevê se uma ação **sobe (1)** ou **cai (0)** no
dia seguinte, com **Spark MLlib** em um Spark **gerenciado** na AWS (**AWS
Glue**), provisionado com **Terraform**, dentro do **AWS Academy Learner Lab**.

> ℹ️ **Isto é uma DEMO — não vale nota.** Serve para mostrar, ao vivo, o mesmo
> pipeline MLlib + Glue do Trabalho Final, só que aplicado a **outro domínio**
> (previsão de direção de ações, em vez de **churn**), para dar repertório.
>
> 🧩 **Diferença essencial para o TF do aluno:** aqui o job PySpark já vem
> **completo e pronto para rodar** (sem TODOs, sem `NotImplementedError`). No TF
> os alunos é que completam as funções de ML.
>
> 📂 **Este diretório é independente do TF do aluno** em
> `aula-07-machine-learning/aws-lab/`. Nada aqui interfere no lab de churn.

---

## Objetivo

Mostrar o pipeline de ML (features → treino/teste → classificador → avaliação)
rodando no **AWS Glue** aplicado à **previsão de direção de ações**. Para
enriquecer a demo, o job treina e **compara DOIS modelos** sobre o mesmo
conjunto de treino — **Regressão Logística** e **Random Forest** — e imprime uma
**tabela comparativa** (acurácia, F1 e AUC-ROC) no **CloudWatch**. Também grava
as **métricas** e uma **amostra de previsões** no **S3**.

As features de entrada são **técnicas sintéticas**:
`retorno_1d`, `retorno_5d`, `media_movel_5`, `media_movel_10`, `volume_rel` e
`volatilidade_5`. A coluna alvo no CSV é `subiu` (1 = subiu no dia seguinte,
0 = caiu), renomeada para `label` na leitura.

### Por que AWS Glue (e não EMR Serverless)?

Neste Learner Lab o **EMR Serverless está bloqueado** (a `LabRole` não confia em
`emr-serverless.amazonaws.com`, então qualquer chamada dá `AccessDenied`). O
**AWS Glue funciona** (a `LabRole` confia em `glue.amazonaws.com`) e é o mesmo
Spark gerenciado usado com sucesso na aula-05 deste repositório.

### Como o bucket S3 é criado (AWS CLI, não `aws_s3_bucket`)

No Learner Lab há uma **SCP** da organização que **nega**
`s3:GetBucketObjectLockConfiguration` — leitura que o recurso `aws_s3_bucket`
sempre faz no create/refresh, resultando em `AccessDenied`. Por isso o bucket é
criado via **AWS CLI** dentro do próprio `terraform apply` (padrão
`terraform_data` + `local-exec`); esse mesmo apply sobe o script e o dataset, e o
`terraform destroy` remove o bucket. É por isso também que o **AWS CLI é
requisito** desta demo.

---

## Arquitetura

```
   +---------------------+       start-job-run        +---------------------------+
   |         S3          |  ------------------------>  |       AWS Glue Job        |
   |  input/ acoes.csv   |                             |    (Spark, glueetl)       |
   |  scripts/ acoes_job |                             |                           |
   |                     |   lê input + script         |   +-------------------+   |
   |                     | <-------------------------- |   |  DRIVER (SparkCtx) |   |
   | output/metrics      |                             |   +-------------------+   |
   | output/predictions                                |   +---+  +---+            |
   |  tmp/    (temp)     |   escreve output            |   |EX |  |EX |  (2x G.1X) |
   +---------------------+ <-------------------------- |   +---+  +---+            |
                                                       +---------------|-----------+
                                                                       | logs do driver
                                                                       v
                                                       +---------------------------+
                                                       |  CloudWatch Logs          |
                                                       |  /aws-glue/jobs/output    |
                                                       +---------------------------+
```

- **S3** = armazenamento distribuído/durável (dataset de entrada, script,
  métricas e amostra de previsões). O script fica em `scripts/acoes_job.py` e é
  **lido pelo Glue** a cada execução.
- **AWS Glue Job** = o "cluster" gerenciado. Ao disparar o job, a AWS provisiona
  o **driver** (onde roda o `SparkContext`/MLlib) e os **executors** (2× `G.1X`),
  liberando-os ao terminar.
- **CloudWatch Logs** = onde ficam os logs do driver (grupo
  `/aws-glue/jobs/output`); é ali que aparece a **tabela comparativa LR x RF**.

---

## Pré-requisitos

- Conta **AWS Academy Learner Lab** (com sessão ativa).
- **AWS CLI v2** instalada e autenticada (`aws --version`) — **obrigatório**: o
  bucket S3 é criado via AWS CLI dentro do `terraform apply` (ver nota acima).
- **Terraform >= 1.5** (`terraform version`).
- O dado da demo: `data/acoes.csv` (já incluído nesta pasta).

> O job (`job/acoes_job.py`) já vem **pronto** — não há TODOs a completar.

---

## Passo 1 — Credenciais temporárias do Learner Lab

1. Inicie o Learner Lab e aguarde o indicador ficar **verde**.
2. Clique em **"AWS Details"** e depois em **"Show"** nas credenciais da AWS CLI.
3. Configure as credenciais de UMA das formas abaixo (região sempre `us-east-1`):

   **Opção A — variáveis de ambiente** (some ao fechar o terminal):
   ```bash
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   export AWS_SESSION_TOKEN="..."
   export AWS_DEFAULT_REGION="us-east-1"
   ```

   **Opção B — arquivo `~/.aws/credentials`** (inclua o `aws_session_token`):
   ```ini
   [default]
   aws_access_key_id = ...
   aws_secret_access_key = ...
   aws_session_token = ...
   region = us-east-1
   ```

> ⚠️ As credenciais são **temporárias** e **expiram por sessão**. Se aparecer
> `ExpiredToken`/`403`, volte ao "AWS Details" e reexporte as credenciais.
> **NUNCA** versione credenciais no Git.

Teste rápido:
```bash
aws sts get-caller-identity
```

---

## Passo 2 — Obter o ARN da LabRole e preencher o `terraform.tfvars`

No Learner Lab **não é permitido criar roles/policies**. Usamos a **LabRole**
pré-provisionada como `role_arn` do Glue Job. Pegue o ARN dela:

```bash
aws iam get-role --role-name LabRole --query Role.Arn --output text
```

Copie o exemplo e preencha com os seus valores:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edite `infra/terraform.tfvars`:
- `labrole_arn` = ARN retornado acima.
- `bucket_nome` = um nome **globalmente único** (ex.: `demo-aula07-acoes-PROF`).
- `regiao` e `tags` já vêm prontos.

> ⚠️ `terraform.tfvars` está no `.gitignore` — não o commite.

---

## Passo 3 — Provisionar a infraestrutura

> ✅ **Nada a completar no código:** o job `job/acoes_job.py` já está pronto
> (sem TODOs). Esta demo é só provisionar, rodar e mostrar o resultado.

> ⚠️ O **AWS CLI v2** precisa estar **instalado e autenticado** antes do apply: é
> ele quem **cria o bucket S3** (via `local-exec`). Confirme com
> `aws sts get-caller-identity` antes de rodar os comandos abaixo.

```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply     # confirme com 'yes'
```

O `apply` **cria o bucket S3 (privado) via AWS CLI** e já **sobe o script**
(`job/acoes_job.py` → `s3://SEU_BUCKET/scripts/`) e o **dataset**
(`data/acoes.csv` → `s3://SEU_BUCKET/input/`) para o S3.

Ao final, o Terraform mostra os **outputs**:
- `bucket_nome` — nome do bucket S3 da demo.
- `glue_job_nome` — nome do Glue Job (usado no `aws glue start-job-run`).
- `labrole_arn` — ARN da LabRole (IAM role do Glue Job).

Os scripts do Passo 4 leem esses outputs automaticamente.

---

## Passo 4 — Rodar o job e ver o resultado

```bash
cd ../scripts
./run_job.sh
```

O `run_job.sh`:
1. Lê `bucket_nome`, `glue_job_nome` e `labrole_arn` dos outputs do Terraform.
2. **Re-sobe** `job/acoes_job.py` e `data/acoes.csv` para o S3.
3. **Limpa a saída anterior** (`s3://SEU_BUCKET/output/`), por segurança.
4. Dispara o job (`aws glue start-job-run`) e captura o `JobRunId`.
5. Faz **polling** do estado a cada 15s.

Estados do Glue: `STARTING → RUNNING → SUCCEEDED` (ou `FAILED`/`TIMEOUT`/`STOPPED`).
O script termina com código 0 em `SUCCEEDED`; em falha, imprime o `ErrorMessage`
e aponta para o CloudWatch.

Depois do `SUCCEEDED`, veja as métricas e a amostra de previsões:

```bash
./ver_resultado.sh
```

Isso lê o bucket dos outputs do Terraform e imprime os **dois** prefixos de saída:
- `output/metrics/` → CSV `modelo,metrica,valor` com `accuracy`, `f1` e
  `areaUnderROC` para **os dois modelos** (LR e RF).
- `output/predictions/` → amostra `features...,label,prediction` (Random Forest).

> 💡 A demo imprime a **comparação Regressão Logística × Random Forest** no
> **CloudWatch** (grupo `/aws-glue/jobs/output`). Pelo console: **AWS Glue →
> Jobs → seu job → aba Runs → selecione o run → Output logs**.

---

## Passo 5 — Limpeza (OBRIGATÓRIA)

```bash
cd ../infra
terraform destroy   # confirme com 'yes'
```

> O **AWS Glue cobra por tempo de execução do job** (não fica "ligado" entre
> execuções), mas ainda assim **destrua o bucket e o job ao final**. O Learner Lab
> tem **orçamento e tempo de sessão limitados** — não deixe recursos residuais.

---

## Mapa conceito ML ↔ serviço AWS

| Conceito de ML (local)                | Equivalente nesta demo (AWS)                           |
|---------------------------------------|--------------------------------------------------------|
| Dataset CSV no disco                  | `acoes.csv` em `s3://.../input/`                        |
| `spark-submit` no docker-compose      | `aws glue start-job-run` (Glue gerenciado)             |
| Driver/executors locais               | Driver + 2× `G.1X` provisionados pelo Glue             |
| `print(...)` no terminal              | Tabela LR × RF no CloudWatch `/aws-glue/jobs/output`   |
| Saída em arquivo local                | `s3://.../output/metrics` e `.../output/predictions`   |

---

## Solução de problemas

- **`ExpiredToken` / `403`**: credenciais do Learner Lab expiraram. Volte ao
  "AWS Details" e **reexporte** `AWS_ACCESS_KEY_ID`/`SECRET`/`SESSION_TOKEN`.
- **`AccessDenied` em `GetBucketObjectLockConfiguration` / SCP**: se aparecer erro
  de Object Lock ao criar o bucket, é a SCP do Learner Lab. Por isso a demo cria o
  bucket via AWS CLI (não `aws_s3_bucket`) — já é o padrão do `main.tf`. Garanta
  que o `versions.tf` está com o provider `aws` fixado em `5.31.0`.
- **`aws: command not found` / bucket não criado**: o `terraform apply` cria o
  bucket chamando o AWS CLI (`local-exec`). Instale o **AWS CLI v2** e garanta que
  `aws sts get-caller-identity` funciona antes do apply.
- **Nome de bucket já existe**: o nome do S3 é **global**. Escolha outro
  `bucket_nome` no `terraform.tfvars` e rode `terraform apply` de novo.
- **Job `FAILED`**: leia o `ErrorMessage` do run (o `run_job.sh` já o imprime) e os
  **logs no CloudWatch** (grupos `/aws-glue/jobs/output` e `/aws-glue/jobs/error`).
  Pelo console: **AWS Glue → Jobs → seu job → Runs**.
