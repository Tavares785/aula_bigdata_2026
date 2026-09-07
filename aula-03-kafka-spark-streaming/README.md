# Lab - Aula 03: Apache Kafka e Spark Streaming

## Objetivo

Praticar dois conceitos fundamentais de processamento em tempo real:

1. **Parsing e validação de mensagens Kafka** (`src/kafka_event_parser.py`)
   — a lógica que um Consumer executa para interpretar e filtrar
   mensagens vindas de um tópico.
2. **Agregações por janela de tempo** (`src/stream_aggregation.py`) — o
   padrão central do Spark Structured Streaming, usando `F.window()`
   sobre DataFrames.

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` nos arquivos:

- `src/kafka_event_parser.py` — parsing JSON, validação de campos e filtro
- `src/stream_aggregation.py` — contagem e soma por janela de tempo

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-03-kafka-spark-streaming

# 2. Construa a imagem Docker (inclui Java + Spark + Python)
docker build -t lab-aula-03 .

# 3. Rode os testes
docker run --rm lab-aula-03
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-03
```

## Alternativa: rodar sem Docker

Requer Java 17+ e Python 3.10 instalados:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Prática manual com Kafka real (opcional, não corrigida automaticamente)

Para experimentar com um broker Kafka de verdade:

```bash
# Sobe o broker Kafka local
docker compose up -d

# Produza/consuma mensagens no tópico "eventos" usando kafka-python
# (veja exemplos no data/sample_events.jsonl)

# Quando terminar
docker compose down
```

## Como entregar

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-03-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
