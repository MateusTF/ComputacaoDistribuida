# Imagem única para os 4 serviços Python; o docker-compose escolhe qual servidor iniciar.
# Python 3.11: o Spyne (SOAP) ainda não funciona no 3.12+.
FROM python:3.11-slim
WORKDIR /app
COPY python/requirements.txt python/requirements.txt
RUN pip install --no-cache-dir -r python/requirements.txt
COPY contratos/ contratos/
COPY python/ python/
WORKDIR /app/python
ENV PYTHONUNBUFFERED=1
