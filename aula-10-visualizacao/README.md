# Lab - Aula 10: Visualização de Dados em Larga Escala

## Objetivo

Praticar a **preparação de dados para dashboards** — as agregações que
alimentariam painéis no Apache Superset, Zeppelin ou qualquer ferramenta
de BI:

- **Totais diários** — soma de valores agrupados por data
- **Top categorias** — ranking das categorias com maior faturamento
- **Média móvel** — suavização de séries temporais para visualização

A parte de criar o dashboard em si é prática manual (ferramentas de BI
são interativas); a correção automática foca na lógica de preparação.

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` em:

- `src/dashboard_data_prep.py`

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-10-visualizacao

# 2. Construa a imagem Docker
docker build -t lab-aula-10 .

# 3. Rode os testes
docker run --rm lab-aula-10
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-10
```

## Alternativa: rodar sem Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Como entregar

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-10-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
