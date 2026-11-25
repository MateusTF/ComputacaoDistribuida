# Imagem única para os 4 serviços Node.js; o docker-compose escolhe qual servidor iniciar.
# Node 22.18+ executa TypeScript diretamente (type stripping), sem etapa de compilação.
FROM node:22-slim
WORKDIR /app/node
COPY node/package.json node/package-lock.json ./
RUN npm ci --omit=dev
COPY contratos/ /app/contratos/
COPY node/src/ ./src/
