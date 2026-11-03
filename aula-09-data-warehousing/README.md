# Lab - Aula 09: Data Warehousing e Data Lakes

## Objetivo

Praticar consultas **SQL estilo Hive** sobre dados estruturados — o
mesmo tipo de query que rodaria em um Data Warehouse sobre HDFS:

- **Agregação por região** — `GROUP BY` + `SUM` + `ORDER BY`
- **Top-N produtos** — ranking com `LIMIT`
- **Filtro com HAVING** — regiões acima de um threshold de receita

O lab usa Spark SQL com `enableHiveSupport()` (metastore Hive embutido),
simulando o mesmo comportamento de um cluster Hive real.

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` em:

- `src/warehouse_queries.py`

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-09-data-warehousing

# 2. Construa a imagem Docker (inclui Java + Spark + Hive support)
docker build -t lab-aula-09 .

# 3. Rode os testes
docker run --rm lab-aula-09
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-09
```

## Alternativa: rodar sem Docker

Requer Java 17+ e Python 3.10 instalados:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Como entregar

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-09-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
