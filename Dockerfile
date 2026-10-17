FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências de sistema necessárias para o psycopg2 e o cron
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements primeiro, para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto para dentro do container
COPY . .

# Garante permissões, pastas de arquivos e normalização de quebra de linha do entrypoint
RUN mkdir -p /app/arquivos/baixados /app/arquivos/processados \
    && chmod +x /app/entrypoint.sh \
    && sed -i 's/\r$//' /app/entrypoint.sh

# Entrypoint gerencia o cron e variáveis de ambiente
ENTRYPOINT ["/app/entrypoint.sh"]

# Mantém o daemon do cron rodando em primeiro plano
CMD ["cron", "-f"]
