import pandas as pd
import os

class FileConverter:
    """
    Classe utilitária para converter diferentes tipos de arquivos (como CSV e XLS) para XLSX.
    """
    
    @staticmethod
    def to_xlsx(input_path: str, output_path: str = None, delimiter: str = ';') -> str:
        """
        Lê o arquivo e o converte para .xlsx.
        
        Args:
            input_path (str): O caminho do arquivo original (ex: arquivo.csv, arquivo.xls).
            output_path (str, optional): O caminho do arquivo de saída. Se não fornecido, 
                                         será salvo no mesmo diretório com extensão .xlsx.
            delimiter (str, optional): Delimitador usado caso o arquivo seja CSV. Padrão é ';'.
            
        Returns:
            str: O caminho do novo arquivo XLSX salvo.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
            
        # Pega o nome base do arquivo para montar a saída
        base_name = os.path.basename(input_path)
        name_without_ext, _ = os.path.splitext(base_name)
        
        # Define o caminho de saída se não for passado ou se for um diretório
        if not output_path:
            dir_name = os.path.dirname(input_path)
            output_path = os.path.join(dir_name, f"{name_without_ext}.xlsx")
        elif os.path.isdir(output_path) or not output_path.endswith('.xlsx'):
            # Cria a pasta caso não exista
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            output_path = os.path.join(output_path, f"{name_without_ext}.xlsx")
            
        extensao = input_path.split('.')[-1].lower()
        
        try:
            print(f"Lendo o arquivo {extensao.upper()}...")
            
            # Escolhe como abrir dependendo da extensão
            if extensao == 'csv':
                try:
                    df = pd.read_csv(input_path, delimiter=delimiter, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(input_path, delimiter=delimiter, encoding='latin1')
                    
            elif extensao in ['xls', 'xlsx']:
                # Se for xls, precisa da lib xlrd instalada; se for xlsx usa openpyxl
                df = pd.read_excel(input_path)
                
            elif extensao == 'pdf':
                try:
                    import pdfplumber
                except ImportError:
                    raise ImportError("A biblioteca 'pdfplumber' é necessária para ler PDFs. Instale usando: pip install pdfplumber")
                    
                print("Extraindo tabelas do PDF...")
                todas_as_linhas = []
                with pdfplumber.open(input_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        for table in tables:
                            todas_as_linhas.extend(table)
                            
                if not todas_as_linhas:
                    raise ValueError("Nenhuma tabela legível encontrada neste PDF.")
                
                # (A primeira linha lida vira a primeira linha de dados)
                df = pd.DataFrame(todas_as_linhas)
                
            else:
                raise ValueError(f"Formato de arquivo não suportado para conversão automática: .{extensao}")
                
            # Salva como Excel (.xlsx) 
            print(f"Convertendo para XLSX...")
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            print(f"Arquivo convertido com sucesso: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erro ao converter o arquivo {input_path}: {e}")
            raise
