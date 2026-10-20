# Lab - Aula 08: NLP com Big Data

## Objetivo

Praticar os blocos básicos de um pipeline de **Processamento de
Linguagem Natural (NLP)** — as mesmas operações que, em Big Data, seriam
aplicadas em paralelo sobre milhões de textos:

- **Tokenização** — quebrar texto em palavras
- **Remoção de stopwords** — filtrar palavras irrelevantes
- **Stemming simplificado** — reduzir palavras à raiz
- **Análise de sentimento** — score baseado em léxico

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` em:

- `src/nlp_basics.py`

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-08-nlp

# 2. Construa a imagem Docker
docker build -t lab-aula-08 .

# 3. Rode os testes
docker run --rm lab-aula-08
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-08
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
2. Crie uma **branch** com o nome `aula-08-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
