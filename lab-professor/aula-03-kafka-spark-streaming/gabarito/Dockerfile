FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Perfil B (gabarito): Python 3.10 + Java + Spark - paridade com os labs Spark (aula-03, aula-05, aula-06, aula-07)"

WORKDIR /lab

# Instalar Java (necessario para o Spark) - mesma dependencia de sistema dos labs de perfil Spark
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    procps \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo do gabarito
COPY . .

# Comando padrao: rodar os testes do gabarito
CMD ["pytest", "-v", "--tb=short"]
