FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências de sistema necessárias para o psycopg2 (banco de dados)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements primeiro, para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto para dentro do container
COPY . .

# Garante que as pastas de arquivos existem
RUN mkdir -p /app/arquivos/baixados /app/arquivos/processados

# Comando que será executado quando o container rodar
CMD ["python", "main.py"]
