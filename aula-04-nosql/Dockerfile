FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Ambiente para o Lab da Aula 04 - NoSQL (MongoDB com mongomock)"

WORKDIR /lab

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo do lab
COPY . .

# Comando padrao: rodar os testes
CMD ["pytest", "-v", "--tb=short"]
