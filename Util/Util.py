import re
import datetime as dt
import pandas as pd

class Util:

    __bancos = {'itau':'extrato_itau'}

    def __init__(self) -> None:
        pass

    def getArquivosProcessados(self, banco) -> list:
        """
        Consulta o banco de dados e retorna a lista de arquivos (nomes base) 
        que já foram processados e inseridos na tabela extrato_itau.
        """
        from Conn.Database import get_db_session
        from sqlalchemy import text

        if banco not in self.__bancos:
            return []
            
        tbl = self.__bancos[banco]
        try:
            with get_db_session() as session:
                resultado = session.execute(text(f"SELECT DISTINCT arquivo_origem FROM {tbl} WHERE arquivo_origem IS NOT NULL;"))
                # Remove a extensão para comparar a raiz do nome do arquivo
                arquivos = [row[0].rsplit('.', 1)[0] for row in resultado.fetchall()]
                return arquivos
        except Exception as e:
            print(f"Aviso ao verificar arquivos processados no banco: {e}")
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
    




    