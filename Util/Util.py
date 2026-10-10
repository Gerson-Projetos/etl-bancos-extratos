import re
import datetime as dt
import pandas as pd

class Util:

    def __init__(self) -> None:
        pass

    def getArquivosProcessados(self) -> list:
        """
        Consulta o banco de dados (tabela contas) para buscar todas as tabelas de extratos ativas,
        e retorna a lista global de arquivos (nomes base) que já foram processados.
        """
        from Conn.Database import get_db_session, Database
        from sqlalchemy import text
        from Models.Conta import Conta

        # Garante que a tabela 'contas' exista no banco antes de tentarmos consultá-la
        Database().create_tables()

        arquivos_processados = []
        try:
            with get_db_session() as session:
                # 1. Pega todas as contas que têm tabela de extrato configurada
                contas = session.query(Conta).all()
                
                # Se a tabela estiver vazia (primeira execução), inserimos os dados automaticamente
                if not contas:
                    print("Tabela 'contas' vazia. Inserindo dados iniciais...")
                    contas_iniciais = [
                        Conta(banco='Itau', descricao='Conta corrente', tbl_extrato='extrato_itau'),
                    ]
                    session.add_all(contas_iniciais)
                    session.commit()
                    contas = contas_iniciais
                
                # Filtra apenas as contas que possuem tbl_extrato configurada
                contas_validas = [c for c in contas if c.tbl_extrato]
                
                if not contas_validas:
                    return []
                
                # Usa 'set' para evitar consultar a mesma tabela de extrato duas vezes
                tabelas_extrato = set([c.tbl_extrato for c in contas_validas])
                
                for tbl in tabelas_extrato:
                    try:
                        resultado = session.execute(text(f"SELECT DISTINCT arquivo_origem FROM {tbl} WHERE arquivo_origem IS NOT NULL;"))
                        arquivos = [row[0].rsplit('.', 1)[0] for row in resultado.fetchall()]
                        arquivos_processados.extend(arquivos)
                    except Exception as e_tbl:
                        session.rollback()
                        
                return list(set(arquivos_processados))
        except Exception as e:
            print(f"Aviso ao verificar arquivos processados dinamicamente: {e}")
            return []
    
    def converter_para_float(self, valor):
        
        if pd.isna(valor) or str(valor).strip() == '':
            return None

        if isinstance(valor, str):
                # Remove R$, espaços, pontos (separadores de milhar) e substitui vírgula por ponto
            valor_limpo = valor.replace('R$', '').strip()  # Remove R$
            valor_limpo = valor_limpo.replace('.', '')         # Remove pontos (1.000 -> 1000)
            valor_limpo = valor_limpo.replace(',', '.')        # Substitui vírgula por ponto (104,90 -> 104.90)
        
        try:
           return float(valor_limpo)
        except ValueError:
            return None  # ou raise a exceção se preferir
    




    