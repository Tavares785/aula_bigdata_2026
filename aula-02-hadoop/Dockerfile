FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Ambiente para o Lab da Aula 02 - Hadoop & MapReduce"

WORKDIR /lab

# Instalar dependencias do sistema (necessario para algumas libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo do lab
COPY . .

# Comando padrao: rodar os testes
CMD ["pytest", "-v", "--tb=short"]
