# Aula 05 — Rodando os RDDs do Spark na AWS (AWS Glue)

Lab **passo a passo** para você executar a lógica de RDDs da aula-05 em um Spark
**gerenciado** na AWS (**AWS Glue**), provisionado com **Terraform**, dentro do
**AWS Academy Learner Lab**.

---

## Objetivo

Rodar as operações de **RDD** da aula-05 (`word_count_rdd`) em um **Spark gerenciado
na nuvem** — o **AWS Glue** — sem precisar subir e manter um cluster ligado.
Você vai enviar o script e os dados para o **S3**, disparar um **Glue Job** e ler o
resultado de volta do S3. É a mesma API de RDDs da aula, mas processada por um
driver e executors provisionados pela AWS sob demanda.

### Por que AWS Glue (e não EMR Serverless)?

Neste Learner Lab desta turma o **EMR Serverless está bloqueado** (a `LabRole` não
confia em `emr-serverless.amazonaws.com`, então qualquer chamada dá `AccessDenied`).
O **AWS Glue funciona** (a `LabRole` confia em `glue.amazonaws.com`) e é o mesmo
Spark gerenciado usado com sucesso na prova deste repositório.

---

## Arquitetura

```
   +------------------+       start-job-run        +---------------------------+
   |      S3          |  ------------------------>  |       AWS Glue Job        |
   |  input/  (dados) |                             |    (Spark, glueetl)       |
   |  scripts/ (.py)  |                             |                           |
   |                  |   lê input + script         |   +-------------------+   |
   |                  | <-------------------------- |   |  DRIVER (SparkCtx) |   |
   |  output/ (result)|                             |   +-------------------+   |
   |  logs/   (logs)  |   escreve output            |   +---+  +---+  +---+     |
   |  tmp/    (temp)  | <-------------------------- |   |EX |  |EX |  |EX | ...  |
   +------------------+                             |   +---+  +---+  +---+     |
                                                    +-------------|-------------+
                                                                  | logs do driver
                                                                  v
                                                    +---------------------------+
                                                    |  CloudWatch Logs          |
                                                    |  /aws-glue/jobs/output    |
                                                    +---------------------------+
```

- **S3** = armazenamento distribuído/durável (guarda entrada, script, saída e logs).
  O script fica em `scripts/rdd_job.py` e é **lido pelo Glue** a cada execução.
- **AWS Glue Job** = o "cluster" gerenciado. Você não liga máquinas: ao disparar
  o job, a AWS provisiona o **driver** (onde roda o `SparkContext`) e os
  **executors** (que processam as partições dos RDDs) e os libera ao terminar.
- **CloudWatch Logs** = onde ficam os logs do driver (grupo `/aws-glue/jobs/output`);
  é ali que aparece o `print(...)` do `rdd_job.py`.
- Relação com a aula-05: o `sc.parallelize(...)`, `flatMap`, `map` e `reduceByKey`
  continuam iguais. O **driver** coordena; os **executors** processam os dados
  particionados — só que agora na nuvem.

---

## Pré-requisitos

- Conta **AWS Academy Learner Lab** (com sessão ativa).
- **AWS CLI v2** instalada (`aws --version`).
- **Terraform >= 1.5** (`terraform version`).
- O dado do lab: `data/sample_lines.txt` (já incluído nesta pasta).

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
- `bucket_nome` = um nome **globalmente único** (ex.: `lab-aula05-glue-SEURA`).
- `regiao` e `tags` já vêm prontos.

> ⚠️ `terraform.tfvars` está no `.gitignore` — não o commite.

---

## Passo 3 — Completar os TODOs em `job/rdd_job.py`

Abra `job/rdd_job.py` e implemente as duas funções marcadas como TODO:

- `word_count_rdd(sc, lines)` — contagem de palavras com RDDs (mesmo contrato da
  aula-05: ordenar por contagem desc e, em empate, alfabética asc).
- `top_n_palavras(sc, lines, n)` — as `n` palavras mais frequentes (reutiliza
  `word_count_rdd`).

**Teste a lógica localmente ANTES de subir.** Você pode validar rapidamente suas
funções de RDD numa máquina com Python 3.10+ e Java 17+ instalados (sem Docker):

```bash
pip install pyspark==3.5.1
# em um pequeno teste interativo, importe e chame word_count_rdd/top_n_palavras
python3 - <<'PY'
from pyspark import SparkContext
import sys; sys.path.insert(0, "job")
from rdd_job import word_count_rdd
sc = SparkContext("local[2]", "teste-local")
print(word_count_rdd(sc, ["gato rato gato", "rato correu gato"]))
sc.stop()
PY
```

> Dica: a API de RDDs (`sc.parallelize`, `flatMap`, `map`, `reduceByKey`) é a mesma
> vista na aula-05. Quando o resultado local bater com o exemplo do docstring, suba
> para o AWS Glue.

---

## Passo 4 — Provisionar a infraestrutura

```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply     # confirme com 'yes'
```

O `apply` já **sobe o script** (`job/rdd_job.py` → `s3://SEU_BUCKET/scripts/`) e o
**dado de exemplo** (`data/sample_lines.txt` → `s3://SEU_BUCKET/input/`) para o S3.

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
2. **Re-sobe** `job/rdd_job.py` para `s3://SEU_BUCKET/scripts/` e o
   `data/sample_lines.txt` para `s3://SEU_BUCKET/input/` (reflete as edições feitas
   depois do `apply`).
3. **Limpa a saída anterior** (`s3://SEU_BUCKET/output/wordcount/`), pois o
   `saveAsTextFile` falha se o prefixo já existir.
4. Dispara o job (`aws glue start-job-run`) e captura o `JobRunId`.
5. Faz **polling** do estado a cada 15s.

Estados do Glue: `STARTING → RUNNING → SUCCEEDED` (ou `FAILED`/`TIMEOUT`/`STOPPED`).
O script termina com código 0 em `SUCCEEDED`.

---

## Passo 6 — Ver o resultado e os logs

```bash
./ver_resultado.sh
```

Isso lista `s3://SEU_BUCKET/output/wordcount/` e imprime o conteúdo
(`palavra,contagem`).

**Logs do driver** ficam no **CloudWatch** (grupo `/aws-glue/jobs/output`). Pelo
console: **AWS Glue → Jobs → seu job → aba Runs → selecione o run → Output logs**.
O `print(...)` do `rdd_job.py` aparece ali.

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
- [ ] 4. Resultado do word count (`./ver_resultado.sh`)
- [ ] 5. Top palavras + interpretação (2–3 frases)
- [ ] 6. Logs do driver (**opcional / bônus**)
- [ ] 7. Limpeza com `terraform destroy` ("Destroy complete!")

> ⚠️ **Nunca** inclua credenciais/tokens nos prints. Se aparecerem (Access Key,
> Secret, Session Token), **mascare** antes de salvar a imagem.

---

## Entrega

- Faça **fork** do repositório e crie a branch `aula-05-aws-SEURA`.
- Coloque seus artefatos na pasta do seu **RA** (coerente com o README da aula-05),
  incluindo o `job/rdd_job.py` completo.
- Inclua a pasta `evidencias/<RA>/` na PR (com `EVIDENCIAS.md` + prints), conforme
  a seção **["Entrega de evidências"](#entrega-de-evidências)**.
- Abra um **Pull Request**.
- Anexe evidências: **print do estado `SUCCEEDED`** do job e o **output** do word
  count (`./ver_resultado.sh`).

---

## Mapeamento conceito ↔ serviço

| Conceito (aula-05)               | Serviço/Recurso na AWS                          |
|----------------------------------|-------------------------------------------------|
| RDD / transformações e ações     | AWS Glue (Spark) executando o job               |
| Driver (SparkContext)            | Driver gerenciado pelo AWS Glue                 |
| Executors (processam partições)  | Executors gerenciados pelo AWS Glue             |
| Armazenamento distribuído (HDFS) | Amazon S3 (input, script, output, logs)         |
| Cluster ligado/desligado         | AWS Glue Job (sob demanda, cobra por execução)  |

---

## Solução de problemas

- **`ExpiredToken` / `403`**: credenciais expiraram. Volte ao "AWS Details" do
  Learner Lab e **reexporte** `AWS_ACCESS_KEY_ID`/`SECRET`/`SESSION_TOKEN`.
- **Bucket name já existe**: o nome do S3 é **global**. Escolha outro
  `bucket_nome` no `terraform.tfvars` e rode `terraform apply` de novo.
- **Job `FAILED`**: leia o `ErrorMessage` do run (o `run_job.sh` já o imprime) e os
  **logs no CloudWatch** (grupos `/aws-glue/jobs/output` e `/aws-glue/jobs/error`),
  ou os artefatos em `s3://SEU_BUCKET/logs/`. Pelo console: **AWS Glue → Jobs →
  seu job → Runs**. Erros comuns: TODOs não implementados (`NotImplementedError`),
  caminho `--INPUT`/`--OUTPUT` errado, ou output já existente (o `run_job.sh` já
  apaga `s3://SEU_BUCKET/output/wordcount/` antes de re-rodar).
- **`NotImplementedError`**: você esqueceu de completar os TODOs em
  `job/rdd_job.py` (Passo 3) antes de subir.
