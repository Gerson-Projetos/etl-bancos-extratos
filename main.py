
import os   
import dotenv
dotenv.load_dotenv()

def getArquivosProcessados():
    from Util.Util import Util
    util = Util()
    
    bancos = ['itau', 'mercado_pago']
    arquivos = []
  
    for banco in bancos:
        arquivos.extend(util.getArquivosProcessados(banco))
    return arquivos
    
def dowloadExtratos(ignorados: list = None):
    from Services.GoogleDriveService import GoogleDriveData
    drive = GoogleDriveData()
    drive.download_files_from_folder(os.getenv('DRIVE_ID'), './arquivos/baixados', ignored_files_basenames=ignorados)

def converteArquivos():
    from Services.FileConverterService import FileConverter
    for file_name in os.listdir('./arquivos/baixados'):
        FileConverter.to_xlsx(f'./arquivos/baixados/{file_name}', './arquivos/processados/')

def deletaArquivosBaixados():
    for file_name in os.listdir('./arquivos/baixados'):
        os.remove(f'./arquivos/baixados/{file_name}')

def deletaArquivosProcessados():
    for file_name in os.listdir('./arquivos/processados'):
        os.remove(f'./arquivos/processados/{file_name}')

def runEtl():
    from Services.ProcessExtratoService import ProcessExtratoService
    service = ProcessExtratoService()
    service.process_all_files()

def cleanArquivos():
    deletaArquivosBaixados()
    deletaArquivosProcessados()
    

def main():

    
    # 1. Pega os arquivos que já estão salvos no Banco de Dados usando o Util
    arquivos_ignorados = getArquivosProcessados()
    if arquivos_ignorados:
        print(f"O sistema encontrou {len(arquivos_ignorados)} arquivo(s) já registrado(s) no Banco. Eles não serão baixados novamente.")

    # 2. Baixa apenas os novos
    dowloadExtratos(arquivos_ignorados)
    converteArquivos()
    runEtl()
    cleanArquivos()


if __name__ == "__main__":
    main()