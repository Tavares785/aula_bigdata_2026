# Aula 07 — Trabalho Final: Classificação de churn com Spark MLlib na AWS (AWS Glue)

Lab **passo a passo** do **Trabalho Final (TF)** da aula-07: você vai rodar um
pipeline de **classificação de churn** com **Spark MLlib** em um Spark
**gerenciado** na AWS (**AWS Glue**), provisionado com **Terraform**, dentro do
**AWS Academy Learner Lab**.

> 💯 **Este Trabalho Final vale até 1.5 pontos.**

---

## Objetivo

Treinar e avaliar um classificador de **churn** (se o cliente cancela ou
permanece) usando **Spark MLlib** em um Spark gerenciado na nuvem — o **AWS
Glue** — sem precisar subir e manter um cluster ligado. Você vai completar as
funções de ML do `job/ml_job.py`, enviar o script e o dataset para o **S3**,
disparar um **Glue Job**, e ler de volta as **métricas** e uma **amostra de
previsões**. É o mesmo pipeline MLlib da aula (features → treino/teste →
classificador → avaliação), só que processado por um driver e executors
provisionados pela AWS sob demanda.

### Por que AWS Glue (e não EMR Serverless)?

Neste Learner Lab desta turma o **EMR Serverless está bloqueado** (a `LabRole`
não confia em `emr-serverless.amazonaws.com`, então qualquer chamada dá
`AccessDenied`). O **AWS Glue funciona** (a `LabRole` confia em
`glue.amazonaws.com`) e é o mesmo Spark gerenciado usado com sucesso na aula-05
deste repositório.

### Como o bucket S3 é criado (AWS CLI, não `aws_s3_bucket`)

No Learner Lab há uma **SCP** da organização que **nega**
`s3:GetBucketObjectLockConfiguration` — leitura que o recurso `aws_s3_bucket`
sempre faz no create/refresh, resultando em `AccessDenied`. Por isso o bucket é
criado via **AWS CLI** dentro do próprio `terraform apply` (padrão
`terraform_data` + `local-exec`); esse mesmo apply sobe o script e o dataset, e o
`terraform destroy` remove o bucket. É por isso também que o **AWS CLI é
requisito** deste lab. Você não precisa editar nada disso — a infra já vem pronta.

---

## Arquitetura

```
   +------------------+       start-job-run        +---------------------------+
   |      S3          |  ------------------------>  |       AWS Glue Job        |
   |  input/ churn.csv|                             |    (Spark, glueetl)       |
   |  scripts/ ml_job |                             |                           |
   |                  |   lê input + script         |   +-------------------+   |
   |                  | <-------------------------- |   |  DRIVER (SparkCtx) |   |
   | output/metrics   |                             |   +-------------------+   |
   | output/predictions                             |   +---+  +---+            |
   |  tmp/    (temp)  |   escreve output            |   |EX |  |EX |  (2x G.1X) |
   +------------------+ <-------------------------- |   +---+  +---+            |
                                                    +-------------|-------------+
                                                                  | logs do driver
                                                                  v
                                                    +---------------------------+
                                                    |  CloudWatch Logs          |
                                                    |  /aws-glue/jobs/output    |
                                                    +---------------------------+
```

- **S3** = armazenamento distribuído/durável (guarda o dataset de entrada, o
  script, as métricas e a amostra de previsões). O script fica em
  `scripts/ml_job.py` e é **lido pelo Glue** a cada execução.
- **AWS Glue Job** = o "cluster" gerenciado. Você não liga máquinas: ao disparar
  o job, a AWS provisiona o **driver** (onde roda o `SparkContext`/MLlib) e os
  **executors** (2× `G.1X`), e os libera ao terminar.
- **CloudWatch Logs** = onde ficam os logs do driver (grupo
  `/aws-glue/jobs/output`); é ali que aparecem os `print(...)` do `ml_job.py` com
  as métricas (`accuracy`, `areaUnderROC`).
- Relação com a aula: `VectorAssembler`, `LogisticRegression`,
  `MulticlassClassificationEvaluator` e `BinaryClassificationEvaluator`
  continuam iguais. O **driver** coordena o treino; os **executors** processam as
  partições — só que agora na nuvem.

---

## Pré-requisitos

- Conta **AWS Academy Learner Lab** (com sessão ativa).
- **AWS CLI v2** instalada e autenticada (`aws --version`) — **obrigatório**: o
  bucket S3 é criado via AWS CLI dentro do `terraform apply` (ver nota acima).
- **Terraform >= 1.5** (`terraform version`).
- **Python local** (3.10+ com Java 17+) para completar e **testar os TODOs** do
  `job/ml_job.py` antes de subir para a AWS.
- O dado do lab: `data/churn.csv` (já incluído nesta pasta).

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
- `bucket_nome` = um nome **globalmente único** (ex.: `lab-aula07-glue-SEURA`).
- `regiao` e `tags` já vêm prontos.

> ⚠️ `terraform.tfvars` está no `.gitignore` — não o commite.

---

## Passo 3 — Completar os TODOs em `job/ml_job.py` e testar local

Abra `job/ml_job.py` e implemente as **três funções** marcadas como TODO:

- `build_feature_vector(df)` — monta a coluna `features` com `VectorAssembler`
  a partir das colunas de entrada e retorna o DataFrame resultante.
- `train_classifier(treino)` — treina **APENAS** um `LogisticRegression` usando
  a coluna `features` e a coluna `label`, retornando o modelo treinado.
- `evaluate_accuracy(previsoes)` — calcula a acurácia com
  `MulticlassClassificationEvaluator` (`metricName="accuracy"`), retornando um
  `float` em `[0, 1]`.

**Teste a lógica localmente ANTES de subir.** O módulo foi escrito para
**importar sem o SDK do Glue** (há um `try/except ImportError`), então você pode
validar suas funções numa máquina com Python 3.10+ e Java 17+ (sem Docker):

```bash
pip install pyspark==3.5.1
python3 - <<'PY'
import sys; sys.path.insert(0, "job")
from pyspark.sql import SparkSession
import ml_job

spark = SparkSession.builder.master("local[2]").appName("teste-local").getOrCreate()
df = (spark.read.option("header", True).option("inferSchema", True)
      .csv("data/churn.csv").withColumnRenamed("churn", "label"))

dados = ml_job.build_feature_vector(df)
treino, teste = dados.randomSplit([0.7, 0.3], seed=42)
modelo = ml_job.train_classifier(treino)
previsoes = modelo.transform(teste)
print("acuracia:", ml_job.evaluate_accuracy(previsoes))
spark.stop()
PY
```

> Dica: se alguma função ainda não foi implementada, ela levanta
> `NotImplementedError` com a mensagem do TODO correspondente. Quando o teste
> local imprimir uma acurácia plausível (acima do acaso), suba para o AWS Glue.

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
(`job/ml_job.py` → `s3://SEU_BUCKET/scripts/`) e o **dataset**
(`data/churn.csv` → `s3://SEU_BUCKET/input/`) para o S3.

Ao final, o Terraform mostra os **outputs**:
- `bucket_nome` — nome do bucket S3 do lab.
- `glue_job_nome` — nome do Glue Job (usado no `aws glue start-job-run`).
- `labrole_arn` — ARN da LabRole (IAM role do Glue Job).

Os scripts do Passo 5 leem esses outputs automaticamente.

---

## Passo 5 — Rodar o job e ver o resultado

```bash
cd ../scripts
./run_job.sh
```

O `run_job.sh`:
1. Lê `bucket_nome`, `glue_job_nome` e `labrole_arn` dos outputs do Terraform.
2. **Re-sobe** `job/ml_job.py` para `s3://SEU_BUCKET/scripts/` e o
   `data/churn.csv` para `s3://SEU_BUCKET/input/` (reflete as edições feitas
   depois do `apply`).
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
- `output/metrics/` → CSV `metrica,valor` com `accuracy` e `areaUnderROC`.
- `output/predictions/` → amostra `features...,label,prediction`.

**Logs do driver** ficam no **CloudWatch** (grupo `/aws-glue/jobs/output`). Pelo
console: **AWS Glue → Jobs → seu job → aba Runs → selecione o run → Output logs**.
Os `print(...)` do `ml_job.py` (incluindo as métricas) aparecem ali.

> 📸 A partir daqui você já deve ir **capturando as evidências** conforme executa
> cada passo (identidade AWS, `apply`, job `SUCCEEDED` + `JobRunId`, métricas,
> amostra de previsões, logs e `destroy`). Veja a seção
> **["Entrega de evidências"](#entrega-de-evidências)** e use o template
> [`evidencias/TEMPLATE.md`](evidencias/TEMPLATE.md).

---

## Passo 6 — Limpeza (OBRIGATÓRIA)

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
mkdir -p evidencias/SEURA
cp evidencias/TEMPLATE.md evidencias/SEURA/EVIDENCIAS.md
```

Preencha o `EVIDENCIAS.md` e salve os **prints na mesma pasta** (ex.:
`evidencias/SEURA/02-apply.png`). Detalhes em
[`evidencias/README.md`](evidencias/README.md).

Checklist das evidências:

- [ ] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [ ] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [ ] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [ ] 4. Resultado: métricas (`accuracy`, `areaUnderROC`) via `./ver_resultado.sh`
- [ ] 5. Amostra de previsões + interpretação (2–3 frases)
- [ ] 6. Logs do driver no CloudWatch (**opcional / bônus**)
- [ ] 7. Limpeza com `terraform destroy` ("Destroy complete!")

> ⚠️ **Nunca** inclua credenciais/tokens nos prints. Se aparecerem (Access Key,
> Secret, Session Token), **mascare** antes de salvar a imagem.

---

## Entrega

- Faça **fork** do repositório e crie a branch `aula-07-aws-SEURA`.
- Complete o `job/ml_job.py` (os três TODOs) e inclua-o na entrega.
- Inclua a pasta `evidencias/<RA>/` na PR (com `EVIDENCIAS.md` + prints), conforme
  a seção **["Entrega de evidências"](#entrega-de-evidências)**.
- Abra um **Pull Request**.
- Anexe evidências: **print do estado `SUCCEEDED`** do job (com o `JobRunId`) e as
  **métricas + amostra de previsões** (`./ver_resultado.sh`).

---

## Mapa conceito ML ↔ serviço AWS

| Conceito de ML (local)                | Equivalente no TF (AWS)                               |
|---------------------------------------|-------------------------------------------------------|
| Dataset CSV no disco                  | `churn.csv` em `s3://.../input/`                       |
| `spark-submit` no docker-compose      | `aws glue start-job-run` (Glue gerenciado)            |
| Driver/executors locais               | Driver + 2× `G.1X` provisionados pelo Glue            |
| `print(...)` no terminal              | Log do driver no CloudWatch `/aws-glue/jobs/output`   |
| Saída em arquivo local                | `s3://.../output/metrics` e `.../output/predictions`  |

---

## Solução de problemas

- **`ExpiredToken` / `403`**: credenciais do Learner Lab expiraram. Volte ao
  "AWS Details" e **reexporte** `AWS_ACCESS_KEY_ID`/`SECRET`/`SESSION_TOKEN`.
- **`AccessDenied` em `GetBucketObjectLockConfiguration` / SCP**: se aparecer erro
  de Object Lock ao criar o bucket, é a SCP do Learner Lab. Por isso o lab cria o
  bucket via AWS CLI (não `aws_s3_bucket`) — já é o padrão do `main.tf`. Garanta
  que o `versions.tf` está com o provider `aws` fixado em `5.31.0` e que você não
  substituiu o bloco do bucket por `aws_s3_bucket`.
- **`aws: command not found` / bucket não criado**: o `terraform apply` cria o
  bucket chamando o AWS CLI (`local-exec`). Instale o **AWS CLI v2** e garanta que
  `aws sts get-caller-identity` funciona antes do apply.
- **Nome de bucket já existe**: o nome do S3 é **global**. Escolha outro
  `bucket_nome` no `terraform.tfvars` (ex.: inclua o seu RA) e rode
  `terraform apply` de novo.
- **Job `FAILED`**: leia o `ErrorMessage` do run (o `run_job.sh` já o imprime) e os
  **logs no CloudWatch** (grupos `/aws-glue/jobs/output` e `/aws-glue/jobs/error`).
  Pelo console: **AWS Glue → Jobs → seu job → Runs**.
- **`NotImplementedError`**: algum TODO do `job/ml_job.py` (Passo 3) não foi
  implementado antes de subir. Complete as três funções e teste localmente.
