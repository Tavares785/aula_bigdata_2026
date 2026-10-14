FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Gabarito (professor) - Aula 02 Hadoop & MapReduce - Perfil A: Python 3.10 puro"

WORKDIR /lab

# Dependencias de sistema (paridade com o Dockerfile do lab da aula-02).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo do gabarito (gabarito/, exemplos/)
COPY . .

# Comando padrao: rodar os testes do gabarito
CMD ["pytest", "-v", "--tb=short"]
