# Labs - Curso de Big Data

Repositório de laboratórios práticos (TF)
Cada aula técnica (2 a 10) tem sua própria pasta com um lab completo,
um **ambiente Docker dedicado** e correção automática (CI/CD) via GitHub
Actions que roda automaticamente em toda Pull Request.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado na sua máquina
- [Git](https://git-scm.com/) para clonar o repositório e enviar suas alterações
- Uma conta no GitHub


## Labs disponíveis

| Pasta | Aula | O que é corrigido automaticamente | Ambiente Docker |
|---|---|---|---|
| `aula-02-hadoop/` | Infraestrutura e Ecossistema Hadoop | Simulação de blocos/replicação HDFS + job MapReduce (`mrjob`) | Python 3.10 |
| `aula-03-kafka-spark-streaming/` | Kafka e Spark Streaming | Parsing/validação de mensagens + agregação por janela de tempo | Python 3.10 + Java 17 + Spark |
| `aula-04-nosql/` | Modelos e Implementações NoSQL | CRUD e agregações em MongoDB (`pymongo` + `mongomock`) | Python 3.10 |
| `aula-05-spark-fundamentos/` | Arquitetura e Fundamentos do Spark | Operações com RDDs (map/filter/reduceByKey/combineByKey) | Python 3.10 + Java 17 + Spark |
| `aula-06-spark-sql-dataframes/` | Spark SQL e DataFrames | Filtragem, agregação e join com a API de DataFrames | Python 3.10 + Java 17 + Spark |
| `aula-07-machine-learning/` | Machine Learning com Big Data | Pipeline de classificação com Spark MLlib | Python 3.10 + Java 17 + Spark |
| `aula-08-nlp/` | NLP com Big Data | Tokenização, stopwords, stemming e sentimento por léxico | Python 3.10 |
| `aula-09-data-warehousing/` | Data Warehousing e Data Lakes | Consultas SQL estilo Hive (Spark SQL + Hive support) | Python 3.10 + Java 17 + Spark |
| `aula-10-visualizacao/` | Visualização de Dados | Agregações para dashboards (totais diários, ranking, média móvel) | Python 3.10 |
| `aula-11-planejamento-projeto/` | Planejamento do Projeto (grupo) | Proposta preenchida (conformidade estrutural) | Python 3.10 |
| `aula-12-ingestao-preprocessamento/` | Ingestão e Pré-processamento (grupo) | Funções de pipeline implementadas + checkpoint | Python 3.10 |
| `aula-13-analise-modelos/` | Análise e Modelos (grupo) | Funções de análise implementadas + checkpoint | Python 3.10 |
| `aula-14-visualizacao-conclusao/` | Visualização e Conclusão (grupo) | Relatório final + checklist de entregáveis | Python 3.10 |

## Estrutura de cada lab

```
aula-XX-nome/
├── Dockerfile           <- Ambiente completo para rodar o lab
├── README.md            <- Objetivo + instruções específicas do lab
├── requirements.txt     <- Dependências Python
├── src/                 <- Onde você edita o código (TODOs)
├── tests/               <- Correção automática (NÃO EDITAR)
├── data/                <- Dados de exemplo
└── docker-compose.yml   <- Só nas Aulas 3 e 4, para prática manual opcional
```

## Como fazer um lab (passo a passo)

### 1. Fork e Clone

```bash
# Fork pelo GitHub (botão "Fork" no canto superior direito)
# Depois clone o seu fork:
git clone https://github.com/SEU-USUARIO/labs-big-data.git
cd labs-big-data
```

### 2. Crie uma branch para o lab

```bash
git checkout -b aula-02-hadoop-SEURA
```

### 3. Edite o código

Abra os arquivos em `src/` da aula correspondente e complete os `TODO`s.

### 4. Teste localmente com Docker

```bash
cd aula-02-hadoop

# Construa a imagem (só precisa fazer de novo se mudar requirements.txt)
docker build -t lab-aula-02 .

# Rode os testes
docker run --rm lab-aula-02
```

**Dica:** Para não rebuildar a cada alteração, monte o código como volume:

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-02
```

### 5. Envie e abra uma PR

```bash
git add .
git commit -m "Aula 02: implementação do lab de Hadoop"
git push origin aula-02-hadoop-SEURA
```

Abra uma **Pull Request** do seu fork para o repositório original
(branch `main`). O GitHub Actions roda a correção automaticamente
dentro de um container Docker idêntico ao que você usou localmente.

### 6. Aguarde o resultado

- ✅ = Todos os testes passaram — parabéns!
- ❌ = Algo falhou — clique em "Details" para ver quais testes falharam

Se algo falhar, corrija o código, faça commit+push de novo na mesma
branch, e o CI roda novamente.

## Como a correção automática funciona

1. Quando você abre (ou atualiza) uma PR, o GitHub Actions detecta quais
   arquivos foram alterados.
2. O workflow correspondente faz **build da imagem Docker** do lab
   (usando o mesmo `Dockerfile` que você usa localmente).
3. Roda `pytest` **dentro do container** — o mesmo ambiente, as mesmas
   dependências, sem surpresas.
4. O resultado é publicado como um "check" na PR e um resumo no
   Step Summary.

## Para o professor: como exigir que o CI passe antes do merge

No GitHub, vá em **Settings → Branches → Branch protection rules** para
a branch `main` e ative:

- "Require status checks to pass before merging"
- Selecione o check `Rodar testes automaticos do lab` de cada workflow

Isso impede que uma PR seja mesclada enquanto os testes não passarem.
