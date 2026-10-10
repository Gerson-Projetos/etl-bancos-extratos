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

O projeto foi organizado para separar claramente as responsabilidades:

```text
etl-bancos-extratos/
│
├── Conn/                   # Configurações de Conexão (SQLAlchemy, PostgreSQL)
├── Extractors/             # Lógica de extração e higienização dos dados (.xlsx -> Objetos)
├── Loaders/                # Classes responsáveis por injetar dados no Banco de Dados
├── Models/                 # Modelos ORM e Tabelas do Banco de Dados (ex: ExtratoItau)
├── Services/               # Orquestração (GoogleDrive, FileConverter, Pipeline do ETL)
├── Util/                   # Funções globais e utilitárias (conversões de moeda, checagem)
├── arquivos/               # Pastas temporárias locais (baixados/, processados/)
├── main.py                 # Arquivo principal que engatilha o pipeline
└── requirements.txt        # Dependências do projeto (Pandas, SQLAlchemy, Google APIs, etc)
```

## Como Funciona o Pipeline (main.py)

1. **Mapeamento e Download**: O script consulta a tabela de `contas` para descobrir todas as tabelas de extrato ativas. O `GoogleDriveService` entra em ação, cruza os arquivos da nuvem com os do banco de dados e faz o download apenas das novidades.
2. **Converter**: O `FileConverterService` pega os PDFs recém-baixados e os transforma em planilhas XLSX.
3. **Extrair & Carregar**: O `ProcessExtratoService` entra na pasta, identifica qual extrato pertence a qual banco através do nome do arquivo (ex: `itau_extrato...`), aciona o `ItauExtractor` para extrair os dados e o `ItauLoader` para persisti-los no PostgreSQL.
4. **Limpeza**: Exclui os arquivos temporários armazenados na máquina local.

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
   Crie um arquivo `.env` na raiz do projeto com as seguintes informações:
   ```env
   # PostgreSQL Connection
   DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco

   # Google Drive
   DRIVE_ID=id_da_sua_pasta_no_google_drive
   ```

4. **Credenciais do Google API:**
   - Acesse o [Google Cloud Console](https://console.cloud.google.com/).
   - Crie um projeto e certifique-se de ativar a **Google Drive API**.
   - Crie a sua credencial (Service Account ou OAuth Client ID). **Atenção:** Se usar uma Conta de Serviço (Service Account), você precisará ir na sua pasta do Google Drive e **compartilhá-ela (permissão de Leitor)** com o e-mail gerado pela Service Account.
   - Baixe o seu arquivo de credenciais, renomeie para `client_secret.json` ou `creds.json` e coloque-o na raiz do projeto (ambos estão protegidos no `.gitignore`).

5. **Execute Localmente:**
   ```bash
   python main.py
   ```

### Executando com Docker 🐳

Se preferir não instalar o Python e as dependências na sua máquina, você pode rodar todo o pipeline de forma isolada usando o Docker:

1. **Pré-requisito:** Ter o [Docker](https://www.docker.com/) instalado.
2. Certifique-se de ter configurado o `.env` e gerado as credenciais do Google API (`client_secret.json` e `creds.json`) na raiz do projeto. Esses arquivos serão mapeados via volumes para o container.
3. **Suba o container:**
   ```bash
   docker compose up --build
   ```

O Docker criará um ambiente leve com a versão correta do Python, instalará pacotes de sistema e bibliotecas, rodará o `main.py` de ponta a ponta e, por fim, o container será encerrado com sucesso ao concluir os processos do ETL.

## Adicionando um Novo Banco

A arquitetura do sistema torna a expansão muito fácil. Para adicionar um novo banco (ex: Banco do Brasil):
1. Crie o Modelo (`Models/ExtratoBB.py`).
2. Crie o Extrator (`Extractors/BBExtractor.py`).
3. Crie o Loader que herda de DatabaseLoader (`Loaders/BBLoader.py`).
4. Adicione o gatilho no dicionário do `ProcessExtratoService.py`.
5. Cadastre o banco e o nome da tabela alvo na tabela `contas` do PostgreSQL (isso fará o script monitorá-lo dinamicamente).

