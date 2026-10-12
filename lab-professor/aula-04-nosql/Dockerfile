FROM python:3.10-slim

LABEL maintainer="Professor - Big Data UNIFAAT"
LABEL description="Gabarito (professor) - Aula 04 NoSQL (MongoDB/mongomock) - Perfil A: Python 3.10 puro"

WORKDIR /lab

# Dependencias de sistema (Perfil A): a base padrao nao requer pacotes
# extras de sistema (paridade com o Dockerfile do lab da aula-04).

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo do gabarito (gabarito/, exemplos/)
COPY . .

# Comando padrao: rodar os testes do gabarito
CMD ["pytest", "-v", "--tb=short"]
