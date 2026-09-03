FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Ambiente para o Lab da Aula 03 - Kafka e Spark Streaming"

WORKDIR /lab

# Instalar Java (necessario para o Spark)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    procps \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copiar codigo do lab
COPY . .

# Comando padrao: rodar os testes
CMD ["pytest", "-v", "--tb=short"]
