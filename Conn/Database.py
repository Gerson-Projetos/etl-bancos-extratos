import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

Base = declarative_base()

class Database:
    _instance = None

    _db_user = None
    _db_password = None
    _db_host = None
    _db_port = None
    _db_database = None
    _db_schema = None
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.set_database()
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Inicializa a conexão com o banco de dados PostgreSQL"""
        self.set_database()
        if not self._db_database or not self._db_user:
            raise ValueError("As variáveis de ambiente 'DB_DATABASE' e 'DB_USERNAME' precisam estar definidas no .env")

        try:
            # Configuração do schema se estiver definido
            connect_args = {}
            if self._db_schema:
                connect_args = {'options': f'-csearch_path={self._db_schema}'}

            # create_engine cria a interface com o banco de dados
            self.engine = create_engine(self.database_url, connect_args=connect_args, echo=False)
            
            # sessionmaker cria uma fábrica de sessões
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            print(f"Conectado ao banco de dados com sucesso.")
        except SQLAlchemyError as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def get_session(self):
        """Retorna uma nova sessão de banco de dados"""
        return self.SessionLocal()

    def create_tables(self):
        """Cria todas as tabelas registradas no Base no banco de dados"""
        if self._db_schema:
            from sqlalchemy import text, create_engine
            # Criar a engine temporária com AUTOCOMMIT para garantir a criação do schema
            engine_temp = create_engine(self.database_url, isolation_level="AUTOCOMMIT")
            with engine_temp.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self._db_schema}"))
            engine_temp.dispose()
            
        Base.metadata.create_all(bind=self.engine)


    """Define as variaveis do banco de dados"""
    def set_database(self):
        self._db_user = os.getenv("DB_USERNAME").strip() if os.getenv("DB_USERNAME") else None
        self._db_password = os.getenv("DB_PASSWORD").strip() if os.getenv("DB_PASSWORD") else None
        self._db_host = os.getenv("DB_HOST", "localhost").strip()
        self._db_port = os.getenv("DB_PORT", "5432").strip()
        self._db_database = os.getenv("DB_DATABASE").strip() if os.getenv("DB_DATABASE") else None
        self._db_schema = os.getenv("DB_SCHEMA").strip() if os.getenv("DB_SCHEMA") else None
        
        # Encodar a senha é necessário se houver caracteres especiais
        pwd_encoded = quote_plus(self._db_password) if self._db_password else ""
        self.database_url = f"postgresql://{self._db_user}:{pwd_encoded}@{self._db_host}:{self._db_port}/{self._db_database}"


# Exemplo de uso como Context Manager para gerenciar sessões de forma segura
class get_db_session:
    """
    Context manager para gerenciar a sessão do banco de dados.
    Uso:
        with get_db_session() as session:
            session.query(Modelo).all()
    """
    def __init__(self):
        self.db = Database()
        self.session = self.db.get_session()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
