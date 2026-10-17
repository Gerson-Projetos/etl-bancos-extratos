
import os
import argparse
import dotenv
dotenv.load_dotenv()

def getArquivosProcessados():
    from Util.Util import Util
    return Util().getArquivosProcessados()
    
def dowloadExtratos(ignorados: list = None):
    from Services.GoogleDriveService import GoogleDriveData
    drive = GoogleDriveData()
    drive.download_files_from_folder(os.getenv('DRIVE_ID'), './arquivos/baixados', ignored_files_basenames=ignorados)

def converteArquivos():
    from Services.FileConverterService import FileConverter
    if not os.path.exists('./arquivos/baixados'):
        os.makedirs('./arquivos/baixados')
    arquivos = os.listdir('./arquivos/baixados')
    if not arquivos:
        print("Nenhum arquivo encontrado em './arquivos/baixados' para conversão.")
        return
    for file_name in arquivos:
        FileConverter.to_xlsx(f'./arquivos/baixados/{file_name}', './arquivos/processados/')

def deletaArquivosBaixados():
    if os.path.exists('./arquivos/baixados'):
        for file_name in os.listdir('./arquivos/baixados'):
            os.remove(f'./arquivos/baixados/{file_name}')

def deletaArquivosProcessados():
    if os.path.exists('./arquivos/processados'):
        for file_name in os.listdir('./arquivos/processados'):
            os.remove(f'./arquivos/processados/{file_name}')

def runEtl(banco: str = None):
    from Services.ProcessExtratoService import ProcessExtratoService
    service = ProcessExtratoService()
    if banco:
        pasta = './arquivos/processados/'
        if not os.path.exists(pasta):
            print(f"Pasta {pasta} não existe.")
            return
        arquivos = [f for f in os.listdir(pasta) if f.endswith(('.xlsx', '.pdf')) and f.lower().startswith(banco.lower())]
        if not arquivos:
            print(f"Nenhum arquivo encontrado para o banco '{banco}'.")
            return
        for f in arquivos:
            service.process_file(banco, f)
    else:
        service.process_all_files()

def cleanArquivos():
    deletaArquivosBaixados()
    deletaArquivosProcessados()
    

def main(etapa: str = 'todos', sem_limpeza: bool = False, sem_download: bool = False, banco: str = None):
    """
    Executa o fluxo completo ou etapas específicas do pipeline de ETL.
    """
    etapa = etapa.lower() if etapa else 'todos'

    if etapa == 'verificar':
        print("\n--- ETAPA 1: Verificação de Arquivos Processados ---")
        arquivos = getArquivosProcessados()
        print(f"Total de arquivos já registrados no banco: {len(arquivos)}")
        for a in arquivos:
            print(f"  - {a}")
        return

    if etapa == 'download':
        print("\n--- ETAPA 2: Download de Extratos ---")
        ignorados = getArquivosProcessados()
        dowloadExtratos(ignorados)
        return

    if etapa == 'converter':
        print("\n--- ETAPA 3: Conversão de Arquivos ---")
        converteArquivos()
        return

    if etapa == 'etl':
        print("\n--- ETAPA 4: Execução do ETL (Extração e Carga) ---")
        runEtl(banco=banco)
        return

    if etapa == 'limpar':
        print("\n--- ETAPA 5: Limpeza de Arquivos Temporários ---")
        cleanArquivos()
        print("Arquivos temporários locais limpos com sucesso.")
        return

    # Fluxo Completo (com opções de teste)
    print("\n=======================================================")
    print("           Iniciando Pipeline ETL Bancos Extratos       ")
    print("=======================================================")

    # 1. Pega os arquivos que já foram extraídos
    arquivos_ignorados = getArquivosProcessados()
    if arquivos_ignorados:
        print(f"O sistema encontrou {len(arquivos_ignorados)} arquivo(s) já registrado(s) no Banco. Eles não serão baixados novamente.")

    # 2. Download (opcional via flag --sem-download)
    if not sem_download:
        dowloadExtratos(arquivos_ignorados)
    else:
        print("[INFO] Etapa de download ignorada (--sem-download). Usando arquivos locais existentes.")

    # 3. Conversão
    converteArquivos()

    # 4. ETL
    runEtl(banco=banco)

    # 5. Limpeza (opcional via flag --sem-limpeza)
    if not sem_limpeza:
        cleanArquivos()
    else:
        print("[INFO] Etapa de limpeza ignorada (--sem-limpeza). Os arquivos foram mantidos nas pastas locais.")

    print("\n=======================================================")
    print("           Pipeline finalizado com sucesso!             ")
    print("=======================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline ETL de Extratos Bancários")
    parser.add_argument(
        "--etapa", "-e",
        choices=["todos", "verificar", "download", "converter", "etl", "limpar"],
        default="todos",
        help="Executa apenas uma etapa específica do pipeline (padrão: todos)"
    )
    parser.add_argument(
        "--sem-limpeza", "--no-clean",
        action="store_true",
        help="Executa o pipeline completo sem deletar as pastas baixados e processados ao final"
    )
    parser.add_argument(
        "--sem-download", "--no-download",
        action="store_true",
        help="Executa conversão e carga sem baixar novamente do Google Drive"
    )
    parser.add_argument(
        "--banco", "-b",
        type=str,
        default=None,
        help="Filtra a execução do ETL apenas para o banco informado (ex: itau, mercado_pago)"
    )
    args = parser.parse_args()
    main(etapa=args.etapa, sem_limpeza=args.sem_limpeza, sem_download=args.sem_download, banco=args.banco)