# Lab - Aula 04: Modelos e Implementações NoSQL

## Objetivo

Praticar operações fundamentais em um banco de dados orientado a
documentos (MongoDB), usando a API real do `pymongo`:

- **CRUD** — inserção, busca com filtros e ordenação
- **Agregações** — pipeline de agregação para calcular médias
- **Operações atômicas** — `$inc` para atualizar campos numéricos

O lab usa `mongomock` (simulação do MongoDB em memória), então o código
que você escreve é **idêntico** ao que rodaria contra um MongoDB real.

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` em:

- `src/mongo_products.py`

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-04-nosql

# 2. Construa a imagem Docker
docker build -t lab-aula-04 .

# 3. Rode os testes
docker run --rm lab-aula-04
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-04
```

## Alternativa: rodar sem Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Prática manual com MongoDB/Cassandra reais (opcional)

Para experimentar com bancos NoSQL de verdade:

```bash
# Sobe MongoDB e Cassandra locais
docker compose up -d

# Conecte com pymongo em localhost:27017
# Conecte com cassandra-driver em localhost:9042

# Quando terminar
docker compose down
```

## Como entregar

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-04-SEURA`.
3. Crie a pasta com seu RA em `src/` ex: `src/252525/`
4. Complete os TODOs em `src/` copiando para sua pasta RA.
5. Teste localmente com Docker (veja acima).
6. Faça **commit + push** para o seu fork.
7. Abra uma **Pull Request** para a branch `main` do repositório original.
8. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
