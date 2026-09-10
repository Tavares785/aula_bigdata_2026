# Lab - Aula 02: Infraestrutura e Ecossistema Hadoop

## Objetivo

Praticar, na prática, os dois pilares do Hadoop apresentados em aula:

1. **HDFS** (`src/hdfs_blocks.py`) — como um arquivo é dividido em blocos e
   replicado entre os DataNodes de um cluster.
2. **MapReduce** (`src/mapreduce_wordcount.py`) — um job real de contagem
   de palavras, usando o modelo `mapper -> combiner -> reducer`, rodando
   localmente através da biblioteca `mrjob` (que simula o comportamento
   de um cluster Hadoop, sem precisar instalar um cluster de verdade).

Você **não precisa instalar Hadoop** para fazer este lab. Tudo roda de
forma simulada/local, mas usando os mesmos conceitos e (no caso do
MapReduce) a mesma API que seria usada em um cluster real.

## O que você precisa fazer

Abra os dois arquivos abaixo e complete todos os trechos marcados com
`TODO` e `raise NotImplementedError(...)`:

- `src/hdfs_blocks.py`
- `src/mapreduce_wordcount.py`

Cada função tem uma explicação detalhada em português no próprio
docstring, com exemplos de entrada e saída esperada.

## Como rodar os testes localmente (usando Docker)

O ambiente completo do lab está encapsulado em um container Docker.
Você **não precisa instalar Python nem dependências** na sua máquina —
basta ter o Docker instalado.

```bash
# 1. Entre na pasta do lab
cd aula-02-hadoop

# 2. Construa a imagem Docker
docker build -t lab-aula-02 .

# 3. Rode os testes
docker run --rm lab-aula-02
```

Se todos os testes passarem, sua PR também vai passar no CI/CD do
GitHub.

### Modo desenvolvimento (monta o código local no container)

Para não precisar rebuildar a imagem a cada alteração no código:

```bash
docker run --rm -v $(pwd)/src:/lab/src lab-aula-02
```

Assim você edita os arquivos em `src/` no seu editor favorito e roda
os testes instantaneamente no container.

## Alternativa: rodar sem Docker

Se preferir rodar diretamente na sua máquina:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Bônus (opcional, não é corrigido automaticamente)

Depois de terminar, tente rodar o job manualmente contra o arquivo de
exemplo em `data/sample_log.txt` e veja o resultado no terminal:

```bash
docker run --rm lab-aula-02 python src/mapreduce_wordcount.py data/sample_log.txt
```

Compare o resultado com o que você esperava — essa é uma boa forma de
"debugar" um job MapReduce antes mesmo de rodar em um cluster real.

## Como entregar

1. Faça um **fork** do repositório do professor.
2. Crie uma **branch** com o nome `aula-02-SEURA`.
3. Complete os TODOs em `src/`.
4. Teste localmente com Docker (veja acima).
5. Faça **commit + push** para o seu fork.
6. Abra uma **Pull Request** para a branch `main` do repositório original.
7. O GitHub Actions vai rodar automaticamente a correção dentro de um
   container Docker — aguarde o resultado (✅ ou ❌) na PR.
