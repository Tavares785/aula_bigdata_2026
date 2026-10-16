# Lab - Aula 08: NLP com Big Data

## Objetivo

Implementar blocos básicos de um pipeline de NLP: tokenização, remoção de stopwords, stemming simplificado e análise de sentimento por léxico.

## O que completar

Complete os TODOs em `src/nlp_basics.py`.

## Testar com Docker

```bash
docker build -t lab-aula-08 .
docker run --rm lab-aula-08
```

Para executar sem Docker, use Python 3.10 ou superior:

```bash
python -m venv venv
pip install -r requirements.txt
pytest -v
```

## Entrega

Crie uma branch `aula-08-SEURA`, implemente os TODOs, teste localmente e abra uma Pull Request para a branch `master` do repositório do professor.
