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
                    print("Tentando extração tabular estruturada para PDFs sem bordas explícitas...")
                    import re
                    date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')
                    with pdfplumber.open(input_path) as pdf:
                        todas_as_linhas.append(['Data', 'Descrição', 'ID da operação', 'Valor', 'Saldo'])
                        for page in pdf.pages:
                            words = page.extract_words()
                            if not words:
                                continue
                            header_words = [w for w in words if w['text'] == 'Data' and w['x0'] < 80]
                            header_top = header_words[0]['top'] if header_words else 0
                            dividers = [r['top'] for r in page.rects if r['height'] < 2 and r['width'] > 50 and r['top'] > header_top]
                            dividers = sorted(list(set([round(d, 1) for d in dividers])))
                            ranges = []
                            if len(dividers) >= 2:
                                for i in range(len(dividers) - 1):
                                    ranges.append((dividers[i], dividers[i + 1]))
                            else:
                                date_words = [w for w in words if date_pattern.match(w['text']) and w['x0'] < 80 and w['top'] > header_top]
                                date_words.sort(key=lambda w: w['top'])
                                for i, dw in enumerate(date_words):
                                    top_b = date_words[i - 1]['top'] + 15 if i > 0 else header_top + 10
                                    bot_b = date_words[i + 1]['top'] - 10 if i < len(date_words) - 1 else page.height - 80
                                    ranges.append((top_b, bot_b))
                            for top_bound, bottom_bound in ranges:
                                row_words = [w for w in words if top_bound <= w['top'] < bottom_bound]
                                if not row_words:
                                    continue
                                data_words = [w for w in row_words if w['x0'] < 83]
                                desc_words = [w for w in row_words if 83 <= w['x0'] < 192]
                                id_words = [w for w in row_words if 192 <= w['x0'] < 266]
                                val_words = [w for w in row_words if 266 <= w['x0'] < 339]
                                saldo_words = [w for w in row_words if w['x0'] >= 339]
                                data_str = " ".join(w['text'] for w in sorted(data_words, key=lambda w: (w['top'], w['x0']))).strip()
                                desc_str = " ".join(w['text'] for w in sorted(desc_words, key=lambda w: (w['top'], w['x0']))).strip()
                                id_str = " ".join(w['text'] for w in sorted(id_words, key=lambda w: (w['top'], w['x0']))).strip()
                                val_str = " ".join(w['text'] for w in sorted(val_words, key=lambda w: (w['top'], w['x0']))).strip()
                                saldo_str = " ".join(w['text'] for w in sorted(saldo_words, key=lambda w: (w['top'], w['x0']))).strip()
                                if data_str and desc_str and re.search(r'\d{2}-\d{2}-\d{4}', data_str):
                                    todas_as_linhas.append([data_str, desc_str, id_str, val_str, saldo_str])

                if not todas_as_linhas or (len(todas_as_linhas) == 1 and todas_as_linhas[0][0] == 'Data'):
                    raise ValueError("Nenhuma tabela legível encontrada neste PDF.")
                
                # (A primeira linha lida vira o cabeçalho)
                df = pd.DataFrame(todas_as_linhas[1:], columns=todas_as_linhas[0]) if len(todas_as_linhas) > 1 else pd.DataFrame(todas_as_linhas)
                
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
