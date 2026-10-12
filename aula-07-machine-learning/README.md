# Lab - Aula 07: Machine Learning com Big Data

## Objetivo

Praticar o pipeline básico de **Machine Learning distribuído** com
Spark MLlib:

- **VectorAssembler** — montar o vetor de features no formato que o
  MLlib exige
- **Treinamento** — treinar um classificador (Regressão Logística)
- **Avaliação** — calcular a acurácia do modelo sobre dados de teste

## O que você precisa fazer

Complete todos os `TODO` e `raise NotImplementedError(...)` em:

- `src/ml_pipeline.py`

## Como rodar os testes localmente (usando Docker)

```bash
# 1. Entre na pasta do lab
cd aula-07-machine-learning

# 2. Construa a imagem Docker (inclui Java + Spark MLlib)
docker build -t lab-aula-07 .

# 3. Rode os testes
docker run --rm lab-aula-07
```

### Modo desenvolvimento (monta o código local no container)

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-07
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
2. Crie uma **branch** com o nome `aula-07-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
