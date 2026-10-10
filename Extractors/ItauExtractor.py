import os
import pandas as pd
from datetime import datetime
from Models.ExtratoItau import ExtratoItau
from Util.Util import Util

class ItauExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.util = Util()

    def extract_to_models(self):
        """
        Lê a planilha, trata os dados e retorna uma lista de instâncias do modelo ExtratoItau.
        """
        # A planilha do Itaú gerada pelo FileConverter costuma ter o cabeçalho real na segunda linha
        df = pd.read_excel(self.file_path, header=1)
        
        # Pega o nome do arquivo para o campo de controle
        arquivo_origem = os.path.basename(self.file_path)

        lancamentos = []
        for index, row in df.iterrows():
            # Usando .iloc para acessar pelas posições (0=data, 1=descrição, 2=valor, 3=saldo)
            
            if len(row) < 4:
                continue
                
            data_str = row.iloc[0]
            descricao = row.iloc[1]
            valor_str = row.iloc[2]
            saldo_str = row.iloc[3]

            # Linhas vazias ou sem descrição são ignoradas
            if pd.isna(data_str) or pd.isna(descricao):
                continue
            
            # Faz o parse da Data (DD/MM/YYYY)
            try:
                if hasattr(data_str, 'date'):  # Caso o Pandas já tenha feito o parse automático
                    data_lancamento = data_str.date() if not isinstance(data_str, pd.Timestamp) else data_str.date()
                else:
                    data_lancamento = datetime.strptime(str(data_str).strip()[:10], "%d/%m/%Y").date()
            except ValueError:
                # Linha não tem formato de data válido, então ignoramos
                continue

            # Faz o parse dos valores
            valor = self.util.converter_para_float(valor_str)
            saldo = self.util.converter_para_float(saldo_str)
            
            # Monta o objeto final do SQLAlchemy
            lancamento = ExtratoItau(
                data_lancamento=data_lancamento,
                descricao=str(descricao).strip(),
                valor=valor,
                saldo=saldo,
                arquivo_origem=arquivo_origem
            )
            lancamentos.append(lancamento)
            
        return lancamentos
