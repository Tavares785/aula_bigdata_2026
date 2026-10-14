# Aula 06 — Rodando Spark SQL / DataFrames na AWS (AWS Glue)

Lab **passo a passo** para você executar as operações de **DataFrames / Spark SQL**
da aula-06 em um Spark **gerenciado** na AWS (**AWS Glue**), provisionado com
**Terraform**, dentro do **AWS Academy Learner Lab**.

---

## Objetivo

Rodar as operações de **DataFrames / Spark SQL** da aula-06 (**filter**,
**groupBy + agregação**, **join** e **top-N**) em um **Spark gerenciado na nuvem**
— o **AWS Glue** — sem precisar subir e manter um cluster ligado. Você vai enviar
o script e os dados (dois CSVs: `pedidos.csv` e `clientes.csv`) para o **S3**,
disparar um **Glue Job** e ler de volta o **TOP-N de clientes por gasto**. É a
mesma API de DataFrames da aula, mas processada por um **driver** e **executors**
provisionados pela AWS sob demanda, com o **S3** como armazenamento (entrada,
script, saída e logs).

### Por que AWS Glue (e não EMR Serverless)?

Neste Learner Lab desta turma o **EMR Serverless está bloqueado** (a `LabRole` não
confia em `emr-serverless.amazonaws.com`, então qualquer chamada dá `AccessDenied`).
O **AWS Glue funciona** (a `LabRole` confia em `glue.amazonaws.com`) e é o mesmo
Spark gerenciado usado com sucesso na prova deste repositório.

### Como o bucket S3 é criado (AWS CLI, não `aws_s3_bucket`)

No Learner Lab há uma **SCP** da organização que **nega**
`s3:GetBucketObjectLockConfiguration` — leitura que o recurso `aws_s3_bucket`
sempre faz no create/refresh, resultando em `AccessDenied`. Por isso o bucket é
criado via **AWS CLI** dentro do próprio `terraform apply` (padrão
`terraform_data` + `local-exec`); esse mesmo apply sobe o script e os dados, e o
`terraform destroy` remove o bucket. É por isso também que o **AWS CLI é
requisito** deste lab. Você não precisa editar nada disso — a infra já vem pronta.

---

## Arquitetura

```
   +----------------------+     start-job-run       +---------------------------+
   |         S3           | ----------------------> |       AWS Glue Job        |
   |  input/pedidos.csv   |                         |    (Spark, glueetl)       |
   |  input/clientes.csv  |                         |                           |
   |  scripts/ (.py)      |   lê 2 inputs + script  |   +-------------------+   |
   |                      | <---------------------- |   |  DRIVER (SparkSes.)|   |
   |  output/top_clientes |                         |   +-------------------+   |
   |  logs/   (logs)      |   escreve output CSV    |   +---+  +---+  +---+     |
   |  tmp/    (temp)      | <---------------------- |   |EX |  |EX |  |EX | ...  |
   +----------------------+                         |   +---+  +---+  +---+     |
                                                    +-------------|-------------+
                                                                  | logs do driver
                                                                  v
                                                    +---------------------------+
                                                    |  CloudWatch Logs          |
                                                    |  /aws-glue/jobs/output    |
                                                    +---------------------------+
```

- **S3** = armazenamento distribuído/durável (guarda os **2 CSVs de entrada**,
  o script, a saída e os logs). O script fica em `scripts/dataframe_job.py` e é
  **lido pelo Glue** a cada execução. Destaque: há **dois inputs**
  (`input/pedidos.csv` e `input/clientes.csv`) e **um output** (`output/top_clientes`).
- **AWS Glue Job** = o "cluster" gerenciado. Você não liga máquinas: ao disparar
  o job, a AWS provisiona o **driver** (onde roda a `SparkSession`) e os
  **executors** (que processam as partições dos DataFrames) e os libera ao terminar.
- **CloudWatch Logs** = onde ficam os logs do driver (grupo `/aws-glue/jobs/output`);
  é ali que aparece o `print(...)` / `show(...)` do `dataframe_job.py`.
- Relação com a aula-06: `filter`, `groupBy` + `F.sum`, `join` e `orderBy/limit`
  continuam iguais. O **driver** coordena; os **executors** processam os dados
  particionados — só que agora na nuvem.

---

## Pré-requisitos

- Conta **AWS Academy Learner Lab** (com sessão ativa).
- **AWS CLI v2** instalada e autenticada (`aws --version`) — **obrigatório**: o
  bucket S3 é criado via AWS CLI dentro do `terraform apply` (ver nota abaixo).
- **Terraform >= 1.5** (`terraform version`).
- Os dados do lab: `data/pedidos.csv` e `data/clientes.csv` (já incluídos nesta pasta).

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
pré-provisionada. Pegue o ARN dela:

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
- `bucket_nome` = um nome **globalmente único** (ex.: `lab-aula06-glue-SEURA`).
- `regiao` e `tags` já vêm prontos.

> ⚠️ `terraform.tfvars` está no `.gitignore` — não o commite.

---

## Passo 3 — Completar os TODOs em `job/dataframe_job.py`

Abra `job/dataframe_job.py` e implemente as duas funções marcadas como TODO
(as outras duas — `filter_high_value_sales` e `join_orders_with_customers` — já
vêm **prontas** como referência da API de DataFrames):

- `total_revenue_by_category(orders_df)` — receita total por categoria: `groupBy`
  por `category`, `F.sum("value").alias("total_revenue")` e `orderBy` decrescente.
- `top_n_customers_by_spend(orders_df, customers_df, n)` — os `n` clientes que
  mais gastaram: **reutiliza** `join_orders_with_customers`, agrupa por
  `(customer_id, customer_name)`, soma `value` como `total_spend`, ordena
  decrescente e limita a `n`.

**Teste a lógica localmente ANTES de subir.** Você pode validar rapidamente suas
funções numa máquina com Python 3.10+ e Java 17+ instalados (sem Docker):

```bash
pip install pyspark==3.5.1
python3 - <<'PY'
import sys; sys.path.insert(0, "job")
from pyspark.sql import SparkSession
from dataframe_job import top_n_customers_by_spend

spark = SparkSession.builder.master("local[2]").appName("teste-local").getOrCreate()

pedidos = spark.createDataFrame(
    [
        ("P1", "C001", "eletronicos", 1000.0),
        ("P2", "C001", "livros", 200.0),
        ("P3", "C002", "moveis", 500.0),
    ],
    ["order_id", "customer_id", "category", "value"],
)
clientes = spark.createDataFrame(
    [("C001", "Ana Souza", "SP"), ("C002", "Bruno Almeida", "RJ")],
    ["customer_id", "customer_name", "customer_uf"],
)

top_n_customers_by_spend(pedidos, clientes, 5).show(truncate=False)
spark.stop()
PY
```

> Dica: a API de DataFrames (`filter`, `join`, `groupBy`, `F.sum`, `orderBy`,
> `limit`) é a mesma vista na aula-06. Quando o resultado local bater com o
> esperado, suba para o AWS Glue.

---

## Passo 4 — Provisionar a infraestrutura

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
(`job/dataframe_job.py` → `s3://SEU_BUCKET/scripts/`) e os **dois CSVs**
(`data/pedidos.csv` e `data/clientes.csv` → `s3://SEU_BUCKET/input/`) para o S3.

Ao final, o Terraform mostra os **outputs**:
- `bucket_nome` — nome do bucket S3 do lab.
- `glue_job_nome` — nome do Glue Job (usado no `aws glue start-job-run`).
- `labrole_arn` — ARN da LabRole (IAM role do Glue Job).

Os scripts do Passo 5 leem esses outputs automaticamente.

---

## Passo 5 — Rodar o job

```bash
cd ../scripts
./run_job.sh
```

O `run_job.sh`:
1. Lê `bucket_nome`, `glue_job_nome` e `labrole_arn` dos outputs do Terraform.
2. **Re-sobe** `job/dataframe_job.py` para `s3://SEU_BUCKET/scripts/` e os dois
   CSVs (`pedidos.csv`, `clientes.csv`) para `s3://SEU_BUCKET/input/` (reflete as
   edições feitas depois do `apply`).
3. **Limpa a saída anterior** (`s3://SEU_BUCKET/output/top_clientes/`), pois a
   escrita falha/duplica se o prefixo já existir.
4. Dispara o job (`aws glue start-job-run`) e captura o `JobRunId`.
5. Faz **polling** do estado a cada 15s.

Estados do Glue: `STARTING → RUNNING → SUCCEEDED` (ou `FAILED`/`TIMEOUT`/`STOPPED`).
O script termina com código 0 em `SUCCEEDED`.

---

## Passo 6 — Ver o resultado e os logs

```bash
./ver_resultado.sh
```

Isso lista `s3://SEU_BUCKET/output/top_clientes/` e imprime o conteúdo
(`customer_id,customer_name,total_spend`).

**Logs do driver** ficam no **CloudWatch** (grupo `/aws-glue/jobs/output`). Pelo
console: **AWS Glue → Jobs → seu job → aba Runs → selecione o run → Output logs**.
O `print(...)` / `show(...)` do `dataframe_job.py` aparece ali.

> 📸 A partir daqui você já deve ir **capturando as evidências** conforme executa
> cada passo (identidade AWS, `apply`, job `SUCCEEDED`, resultado, logs e `destroy`).
> Veja a seção **["Entrega de evidências"](#entrega-de-evidências)** e use o
> template [`evidencias/TEMPLATE.md`](evidencias/TEMPLATE.md).

---

## Passo 7 — Limpeza (OBRIGATÓRIA)

```bash
cd ../infra
terraform destroy   # confirme com 'yes'
```

> O **AWS Glue cobra por tempo de execução do job** (não fica "ligado" entre
> execuções), mas ainda assim **destrua o bucket e o job ao final**. O Learner Lab
> tem **orçamento e tempo de sessão limitados** — não deixe recursos residuais.

---

## Entrega de evidências

Você entrega as evidências dentro de `evidencias/<SEU_RA>/`. Copie o template e
preencha:

```bash
mkdir -p aws-lab/evidencias/SEURA
cp aws-lab/evidencias/TEMPLATE.md aws-lab/evidencias/SEURA/EVIDENCIAS.md
```

Preencha o `EVIDENCIAS.md` e salve os **prints na mesma pasta** (ex.:
`evidencias/SEURA/02-apply.png`). Detalhes em
[`evidencias/README.md`](evidencias/README.md).

Checklist das evidências:

- [ ] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [ ] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [ ] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [ ] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [ ] 5. Interpretação do TOP-N (2–3 frases)
- [ ] 6. Logs do driver (**opcional / bônus**)
- [ ] 7. Limpeza com `terraform destroy` ("Destroy complete!")

> ⚠️ **Nunca** inclua credenciais/tokens nos prints. Se aparecerem (Access Key,
> Secret, Session Token), **mascare** antes de salvar a imagem.

---

## Entrega

- Faça **fork** do repositório e crie a branch `aula-06-aws-SEURA`.
- Coloque seus artefatos na pasta do seu **RA** (coerente com o README da aula-06),
  incluindo o `job/dataframe_job.py` completo.
- Inclua a pasta `evidencias/<RA>/` na PR (com `EVIDENCIAS.md` + prints), conforme
  a seção **["Entrega de evidências"](#entrega-de-evidências)**.
- Abra um **Pull Request**.
- Anexe evidências: **print do estado `SUCCEEDED`** do job e o **output** do
  TOP-N de clientes (`./ver_resultado.sh`).

---

## Mapeamento conceito ↔ serviço

| Conceito (aula-06)                    | Serviço/Recurso na AWS                          |
|---------------------------------------|-------------------------------------------------|
| DataFrame / Spark SQL (filter, join)  | AWS Glue (Spark) executando o job               |
| groupBy + agregação (F.sum)           | AWS Glue (Spark) executando o job               |
| Driver (SparkSession)                 | Driver gerenciado pelo AWS Glue                 |
| Executors (processam partições)       | Executors gerenciados pelo AWS Glue             |
| Armazenamento distribuído (HDFS)      | Amazon S3 (2 inputs, script, output, logs)      |
| Cluster ligado/desligado              | AWS Glue Job (sob demanda, cobra por execução)  |

---

## Solução de problemas

- **`ExpiredToken` / `403`**: credenciais expiraram. Volte ao "AWS Details" do
  Learner Lab e **reexporte** `AWS_ACCESS_KEY_ID`/`SECRET`/`SESSION_TOKEN`.
- **`AccessDenied` em `GetBucketObjectLockConfiguration` / `voc-cancel-cred` /
  SCP**: se aparecer erro de Object Lock ao criar o bucket, é a SCP do Learner
  Lab. Por isso o lab cria o bucket via AWS CLI (não `aws_s3_bucket`). Garanta que
  o `versions.tf` está com o provider `aws` fixado em `5.31.0` e que você não
  substituiu o bloco do bucket por `aws_s3_bucket`.
- **`aws: command not found` / bucket não criado**: o `terraform apply` cria o
  bucket chamando o AWS CLI (`local-exec`). Instale o **AWS CLI v2** e garanta que
  `aws sts get-caller-identity` funciona antes do apply.
- **Bucket name já existe**: o nome do S3 é **global**. Escolha outro
  `bucket_nome` no `terraform.tfvars` e rode `terraform apply` de novo.
- **Job `FAILED`**: leia o `ErrorMessage` do run (o `run_job.sh` já o imprime) e os
  **logs no CloudWatch** (grupos `/aws-glue/jobs/output` e `/aws-glue/jobs/error`),
  ou os artefatos em `s3://SEU_BUCKET/logs/`. Pelo console: **AWS Glue → Jobs →
  seu job → Runs**. Erros comuns: TODOs não implementados (`NotImplementedError`),
  caminho `--PEDIDOS`/`--CLIENTES`/`--OUTPUT` errado, ou output já existente (o
  `run_job.sh` já apaga `s3://SEU_BUCKET/output/top_clientes/` antes de re-rodar).
- **`NotImplementedError`**: você esqueceu de completar os TODOs em
  `job/dataframe_job.py` (Passo 3) antes de subir.
