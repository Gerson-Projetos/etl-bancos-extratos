# 🏦 ETL Bancos Extratos

Um pipeline ETL (Extract, Transform, Load) construído em Python para automatizar o fluxo de ponta a ponta de extratos bancários. O sistema baixa arquivos do Google Drive, converte extratos em PDF para planilhas, extrai os dados, remove duplicidades usando hashes criptográficos e insere tudo em um banco de dados PostgreSQL .

## Principais Funcionalidades

- **Integração com Google Drive**: Conecta-se à API do Google Drive para varrer pastas e baixar extratos automaticamente.
- **Conversão de Arquivos**: Módulo para converter PDFs originais dos bancos para formato XLSX para fácil manipulação (usando bibliotecas como `tabula` e `pandas`).
- **Prevenção de Duplicidade (Inteligente)**: Verifica no banco de dados quais arquivos já foram baixados, poupando tempo e banda ao não baixar o que já foi processado.
- **Mapeamento Dinâmico de Contas**: Utiliza uma tabela central de `contas` (`Models/Conta.py`) no banco de dados para registrar e gerenciar de onde vem os dados. A verificação de arquivos processados varre automaticamente todas as contas cadastradas, tornando o sistema escalável sem precisar mexer no código principal.
- **Hashing de Transações**: Usa `hashlib.sha256` em cada transação (data + descrição + valor) para criar uma "impressão digital" da operação financeira.
- **Bulk Insert Otimizado**: Utiliza o comando nativo do PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` através do SQLAlchemy, processando milhares de registros instantaneamente.
- **Arquitetura Modular (SOLID)**: Totalmente escalável para aceitar novos bancos sem mexer no que já está funcionando.

## Estrutura do Projeto

O projeto foi organizado seguindo princípios de arquitetura modular e SOLID para separar claramente as responsabilidades:

```text
etl-bancos-extratos/
│
├── Conn/                           # Conexão com Banco de Dados
│   └── Database.py                 # Conexão SQLAlchemy e gerenciador de sessão (get_db_session)
│
├── Extractors/                     # Extratores de Dados Bancários
│   ├── ItauExtractor.py            # Extração de extratos do Itaú (.xlsx)
│   └── MercadoPagoExtractor.py     # Extração de extratos do Mercado Pago (.pdf e .xlsx)
│
├── Loaders/                        # Carga de Dados no Banco
│   ├── DatabaseLoader.py           # Classe base para bulk insert com ON CONFLICT DO NOTHING
│   ├── ItauLoader.py               # Loader específico do Itaú com validação de tipo
│   └── MercadoPagoLoader.py        # Loader específico do Mercado Pago
│
├── Models/                         # Modelos ORM (SQLAlchemy)
│   ├── Conta.py                    # Cadastro de contas e mapeamento das tabelas de extrato
│   ├── ExtratoItau.py              # Tabela 'extrato_itau' com hash SHA-256 anti-duplicidade
│   └── ExtratoMercadoPago.py       # Tabela 'extrato_mercado_pago' com hash SHA-256
│
├── Services/                       # Serviços e Orquestração
│   ├── FileConverterService.py     # Conversão de PDFs/CSVs para XLSX (com fallback tabular)
│   ├── GoogleApiService.py         # Autenticação base nas APIs do Google
│   ├── GoogleDriveService.py       # Download e listagem de extratos no Google Drive
│   └── ProcessExtratoService.py    # Roteamento inteligente de bancos e execução do pipeline
│
├── Util/                           # Utilitários Globais
│   └── Util.py                     # Tratamento de moedas, conversões e verificação de processados
│
├── arquivos/                       # Pastas temporárias locais
│   ├── baixados/                   # Extratos baixados do Drive (PDFs/CSVs/XLSX)
│   └── processados/                # Extratos convertidos prontos para o ETL
│
├── tests/                          # Testes Automatizados
│   ├── __init__.py
│   └── test_etapas_unit.py         # Testes unitários (Modelos, Hashes, Conversores)
│
├── test_etapas.py                  # Diagnóstico interativo e teste individual das 5 etapas
├── main.py                         # Ponto de entrada com flags CLI (--etapa, --sem-limpeza)
├── entrypoint.sh                   # Script de entrada Docker para cron e variáveis de ambiente
├── Dockerfile                      # Imagem Docker com Python 3.12, dependências e daemon do cron
├── docker-compose.yml              # Stack completa (ETL + Postgres) com rede isolada e subnet
├── docker-compose.etl-only.yml     # Stack standalone do ETL para conexões a bancos externos
├── requirements.txt                # Dependências Python (Pandas, pdfplumber, SQLAlchemy, etc)
└── .env.example                    # Modelo de configuração de variáveis de ambiente
```

## Como Funciona o Pipeline (main.py)

1. **Mapeamento e Download**: O script consulta a tabela de `contas` para descobrir todas as tabelas de extrato ativas. O `GoogleDriveService` entra em ação, cruza os arquivos da nuvem com os do banco de dados e faz o download apenas das novidades.
2. **Converter**: O `FileConverterService` pega os PDFs/CSVs recém-baixados e os transforma em planilhas XLSX estruturadas.
3. **Extrair & Carregar**: O `ProcessExtratoService` varre a pasta, identifica o banco pelo prefixo do nome do arquivo (ex: `itau...` ou `mercado_pago...`), aciona o respectivo extrator (`ItauExtractor` ou `MercadoPagoExtractor`) para extrair os dados e o loader (`ItauLoader` ou `MercadoPagoLoader`) para persisti-los no PostgreSQL com prevenção automática de duplicidades.
4. **Limpeza**: Exclui os arquivos temporários armazenados na máquina local (a menos que a flag `--sem-limpeza` seja informada).

## Configuração e Instalação

### Pré-requisitos
- Python 3.9+
- PostgreSQL
- Credenciais da API do Google (OAuth 2.0 Client IDs)

### Passos

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Gerson-Projetos/etl-bancos-extratos.git
   cd etl-bancos-extratos
   ```

2. **Crie o ambiente virtual e instale as dependências:**
   ```bash
   python -m venv venv
   # Ative o venv (Windows):
   .\venv\Scripts\activate
   # Instale os pacotes:
   pip install -r requirements.txt
   ```

3. **Configure as Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto com as seguintes informações (baseado no `.env.example`):
   ```env
   DRIVE_ID=seu_id_do_google_drive
   
   DB_DATABASE=sistemas
   DB_USERNAME=local
   DB_PASSWORD=sua_senha
   DB_PORT=5432
   DB_HOST=localhost
   DB_SCHEMA=financeiro
   ```

4. **Credenciais do Google API:**
   - Acesse o [Google Cloud Console](https://console.cloud.google.com/).
   - Crie um projeto e certifique-se de ativar a **Google Drive API**.
   - Crie a sua credencial (Service Account ou OAuth Client ID). **Atenção:** Se usar uma Conta de Serviço (Service Account), você precisará ir na sua pasta do Google Drive e **compartilhá-ela (permissão de Leitor)** com o e-mail gerado pela Service Account.
   - Baixe o seu arquivo de credenciais, renomeie para `client_secret.json` ou `creds.json` e coloque-o na raiz do projeto (ambos estão protegidos no `.gitignore`).

5. **Execute Localmente:**
   ```bash
   # Execução padrão do fluxo completo:
   python main.py
   ```

### 🧪 Testando e Executando Etapas Isoladas

Para facilitar o desenvolvimento, depuração e validação, você pode executar etapas específicas do pipeline ou rodar diagnósticos automáticos:

1. **Parâmetros no `main.py`:**
   ```bash
   # 1. Apenas verificar arquivos já registrados no banco:
   python main.py --etapa verificar

   # 2. Apenas baixar novos extratos do Google Drive:
   python main.py --etapa download

   # 3. Apenas converter arquivos baixados para XLSX:
   python main.py --etapa converter

   # 4. Apenas extrair e carregar dados no banco (pode filtrar por banco):
   python main.py --etapa etl
   python main.py --etapa etl --banco mercado_pago

   # 5. Executar fluxo completo SEM deletar os arquivos temporários (inspeção local):
   python main.py --sem-limpeza

   # 6. Executar conversão e carga usando arquivos locais existentes (sem baixar do Drive):
   python main.py --sem-download
   ```

2. **Utilitário de Diagnóstico Interativo (`test_etapas.py`):**
   ```bash
   # Menu interativo para testar qualquer etapa:
   python test_etapas.py

   # Diagnóstico completo de todas as etapas (Banco, Drive, Conversão, ETL, Limpeza):
   python test_etapas.py --todas

   # Testar uma etapa específica (1 a 5):
   python test_etapas.py --etapa 1
   ```

3. **Testes Unitários Automatizados:**
   ```bash
   python -m unittest discover tests
   ```

### Executando com Docker e Agendamento no Servidor 🐳
 
Para subir a aplicação em um servidor de produção ou homologação de forma automatizada e isolada:

1. **Pré-requisito:** Ter o [Docker](https://www.docker.com/) e o Docker Compose instalados no servidor.
2. Configure o seu arquivo `.env` (baseado no `.env.example`) e adicione as credenciais do Google API (`client_secret.json` e `creds.json`) na raiz do projeto.
3. **Configuração de Rede e Subnet**:
   - O `docker-compose.yml` provisiona uma rede bridge isolada chamada `etl-network` com subnet configurável via `.env` (`${NETWORK_SUBNET:-172.20.0.0/29}`) e gateway (`${NETWORK_GATEWAY:-172.20.0.1}`).
   - O banco PostgreSQL recebe o IP fixo `172.20.0.2`.
   - O serviço do ETL recebe o IP fixo configurável (`${NETWORK_IP:-172.20.0.3}`).
4. **Agendamento com Cron no Container**:
   - O container do ETL executa com um daemon do Cron interno (`cron -f`) e política `restart: unless-stopped`.
   - Por padrão, o agendamento dispara diariamente às 03:00 (`CRON_SCHEDULE=0 3 * * *`), ou conforme configurado no `.env`.
   - A flag `RUN_ON_STARTUP=true` realiza um disparo imediato do pipeline na subida do container antes de aguardar o próximo ciclo do cron.
   - Os logs do cron são roteados para o stdout do container, permitindo acompanhar tudo em tempo real via Docker.

5. **Comandos Úteis para o Servidor:**
   ```bash
   # Iniciar em segundo plano (detached) compilando as alterações:
   docker compose up -d --build

   # Acompanhar os logs do ETL e disparos do cron em tempo real:
   docker compose logs -f etl

   # Executar manualmente uma carga pontual no container em execução:
   docker compose exec etl python main.py

   # Parar os serviços:
   docker compose down
   ```

> **💡 Caso utilize um banco externo:** Use o arquivo `docker-compose.etl-only.yml`:
> ```bash
> docker compose -f docker-compose.etl-only.yml up -d --build
> ```

## Adicionando um Novo Banco

A arquitetura do sistema torna a expansão muito fácil. Para adicionar um novo banco (ex: Banco do Brasil):
1. Crie o Modelo (`Models/ExtratoBB.py`).
2. Crie o Extrator (`Extractors/BBExtractor.py`).
3. Crie o Loader que herda de DatabaseLoader (`Loaders/BBLoader.py`).
4. Adicione o gatilho no dicionário do `ProcessExtratoService.py`.
5. Cadastre o banco e o nome da tabela alvo na tabela `contas` do PostgreSQL (isso fará o script monitorá-lo dinamicamente).

