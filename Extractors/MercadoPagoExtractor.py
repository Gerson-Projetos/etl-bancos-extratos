import os
import re
from datetime import datetime
import pandas as pd
from Models.ExtratoMercadoPago import ExtratoMercadoPago
from Util.Util import Util


class MercadoPagoExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.util = Util()

    def extract_to_models(self):
        """
        Lê o arquivo do extrato do Mercado Pago (.pdf ou .xlsx), trata os dados
        e retorna uma lista de instâncias do modelo ExtratoMercadoPago.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")

        extensao = self.file_path.split('.')[-1].lower()

        if extensao == 'pdf':
            return self._extract_from_pdf()
        elif extensao in ['xlsx', 'xls']:
            return self._extract_from_excel()
        else:
            raise ValueError(f"Extensão de arquivo '.{extensao}' não suportada para Mercado Pago.")

    def _extract_from_pdf(self):
        """
        Extrai transações diretamente do arquivo PDF do Mercado Pago utilizando pdfplumber.
        Suporta descrições com quebras de linha e colunas estruturadas.
        """
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("A biblioteca 'pdfplumber' é necessária para processar PDFs. Instale usando: pip install pdfplumber")

        arquivo_origem = os.path.basename(self.file_path)
        date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')
        lancamentos = []

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue

                # Identifica cabeçalho da tabela se existir na página
                header_words = [w for w in words if w['text'] == 'Data' and w['x0'] < 80]
                header_top = header_words[0]['top'] if header_words else 0

                # Busca retângulos divisores horizontais (linhas de separação das linhas da tabela)
                dividers = [r['top'] for r in page.rects if r['height'] < 2 and r['width'] > 50 and r['top'] > header_top]
                dividers = sorted(list(set([round(d, 1) for d in dividers])))

                ranges = []
                if len(dividers) >= 2:
                    for i in range(len(dividers) - 1):
                        ranges.append((dividers[i], dividers[i + 1]))
                else:
                    # Fallback caso não haja divisores gráficos: agrupa pelas posições verticais das datas
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

                    # Faixas horizontais padrão do extrato Mercado Pago:
                    # Data: x < 83
                    # Descrição: 83 <= x < 192
                    # ID da operação: 192 <= x < 266
                    # Valor: 266 <= x < 339
                    # Saldo: x >= 339
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

                    # Ignora se não houver data ou descrição
                    if not data_str or not desc_str:
                        continue

                    match_date = re.search(r'\d{2}-\d{2}-\d{4}', data_str)
                    if not match_date:
                        continue

                    try:
                        data_lancamento = datetime.strptime(match_date.group(0), "%d-%m-%Y").date()
                    except ValueError:
                        continue

                    valor = self.util.converter_para_float(val_str)
                    saldo = self.util.converter_para_float(saldo_str)
                    id_operacao = id_str if id_str else None

                    lancamento = ExtratoMercadoPago(
                        data_lancamento=data_lancamento,
                        descricao=desc_str,
                        id_operacao=id_operacao,
                        valor=valor,
                        saldo=saldo,
                        arquivo_origem=arquivo_origem
                    )
                    lancamentos.append(lancamento)

        return lancamentos

    def _extract_from_excel(self):
        """
        Lê a planilha Excel gerada para o Mercado Pago, trata os dados e retorna instâncias de ExtratoMercadoPago.
        """
        df = pd.read_excel(self.file_path)
        arquivo_origem = os.path.basename(self.file_path)

        # Se a primeira linha contiver nomes de colunas como texto (ou header=None)
        if len(df) > 0 and 'data' not in [str(c).lower() for c in df.columns]:
            first_row_vals = [str(x).lower() for x in df.iloc[0].values]
            if any('data' in v for v in first_row_vals):
                df = pd.read_excel(self.file_path, header=1)

        lancamentos = []
        for index, row in df.iterrows():
            if len(row) < 4:
                continue

            data_str = row.iloc[0]
            descricao = row.iloc[1]

            # Se houver 5 colunas: Data, Descrição, ID, Valor, Saldo
            if len(row) >= 5:
                id_operacao_raw = row.iloc[2]
                valor_str = row.iloc[3]
                saldo_str = row.iloc[4]
            else:
                id_operacao_raw = None
                valor_str = row.iloc[2]
                saldo_str = row.iloc[3]

            if pd.isna(data_str) or pd.isna(descricao):
                continue

            # Faz o parse da Data (DD-MM-YYYY ou DD/MM/YYYY)
            try:
                if hasattr(data_str, 'date'):
                    data_lancamento = data_str.date() if not isinstance(data_str, pd.Timestamp) else data_str.date()
                else:
                    d_clean = str(data_str).strip()[:10]
                    if '-' in d_clean:
                        data_lancamento = datetime.strptime(d_clean, "%d-%m-%Y").date()
                    else:
                        data_lancamento = datetime.strptime(d_clean, "%d/%m/%Y").date()
            except ValueError:
                continue

            valor = self.util.converter_para_float(valor_str)
            saldo = self.util.converter_para_float(saldo_str)
            
            id_operacao = str(id_operacao_raw).strip() if pd.notna(id_operacao_raw) and str(id_operacao_raw).strip() != '' else None
            # Trata casos em que o ID vira float no pandas (ex: 1738003634321.0)
            if id_operacao and id_operacao.endswith('.0'):
                id_operacao = id_operacao[:-2]

            lancamento = ExtratoMercadoPago(
                data_lancamento=data_lancamento,
                descricao=str(descricao).strip(),
                id_operacao=id_operacao,
                valor=valor,
                saldo=saldo,
                arquivo_origem=arquivo_origem
            )
            lancamentos.append(lancamento)

        return lancamentos
