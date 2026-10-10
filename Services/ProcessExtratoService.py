from sqlalchemy.ext.asyncio import session
import os
from Conn.Database import get_db_session, Database

# Import Itaú
from Extractors.ItauExtractor import ItauExtractor
from Loaders.ItauLoader import ItauLoader


class ProcessExtratoService:
    def __init__(self):
        # 1. Garante que as tabelas existem no banco sempre que iniciarmos o serviço
        Database().create_tables()

    def process_file(self, banco: str, file_name: str):
        """
        Processa um arquivo específico chamando as classes do banco informado.
        """
        caminho_arquivo = f'./arquivos/processados/{file_name}'
        
        if not os.path.exists(caminho_arquivo):
            print(f"Erro: Arquivo não encontrado: {caminho_arquivo}")
            return
            
        print(f"Iniciando extração do banco '{banco.upper()}' no arquivo '{file_name}'...")
        
        with get_db_session() as session:
            # Escolhe o Extrator e o Loader baseado no nome do banco

            extractor, loader = self.__seleciona_banco(banco, caminho_arquivo, session)

            lancamentos = extractor.extract_to_models()
            inseridos = loader.load_to_database(lancamentos)
            session.commit()

            print(f"-> Foram encontrados {len(lancamentos)} registros válidos no arquivo.")
            
            if inseridos == 0:
                print(f"-> NENHUM dado novo foi inserido (todos já existiam no banco de dados).")
            elif inseridos < len(lancamentos):
                ignorados = len(lancamentos) - inseridos
                print(f"-> {inseridos} novos dados inseridos com sucesso! ({ignorados} duplicados ignorados).")
            else:
                print(f"-> {inseridos} novos dados foram enviados para o Postgres com sucesso!\n")


    def __seleciona_banco(self, banco: str, caminho_arquivo: str, session: object):
        if banco.lower() == 'itau':
            return ItauExtractor(caminho_arquivo), ItauLoader(session)

        elif banco.lower() == 'mercado_pago':
            # return MercadoPagoExtractor(), MercadoPagoLoader()
            raise ValueError(f"Banco '{banco}' ainda não implementado.")
        else:
            raise ValueError(f"Banco '{banco}' não suportado.")


    def process_all_files(self):
        """
        Método inteligente: Varre a pasta de arquivos processados,
        descobre qual é o banco pelo prefixo do nome do arquivo e processa todos de uma vez.
        """
        pasta = './arquivos/processados/'
        if not os.path.exists(pasta):
            print(f"Pasta {pasta} não existe.")
            return
            
        arquivos = [f for f in os.listdir(pasta) if f.endswith('.xlsx')]
        if not arquivos:
            print("Nenhum arquivo .xlsx encontrado para processamento.")
            return
            
        print(f"Encontrados {len(arquivos)} arquivos para processar. Iniciando lotes...")
        
        for file_name in arquivos:
            # Identifica o banco pelo prefixo (ex: 'itau_extrato_01.xlsx' -> 'itau')
            if file_name.lower().startswith('itau'):
                self.process_file('itau', file_name)
            elif file_name.lower().startswith('mercado_pago'):
                self.process_file('mercado_pago', file_name)
            else:
                print(f"Ignorando '{file_name}': Prefixo de banco desconhecido.")
