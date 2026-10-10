import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from .GoogleApiService import GoogleApi

class GoogleDriveData(GoogleApi):
    def __init__(self) -> None:
        super().__init__()
        # Inicializa o serviço do Google Drive
        self.service = build('drive', 'v3', credentials=self.credentials)

    def download_file(self, file_id: str, file_path: str) -> None:
        """
        Baixa um arquivo do Google Drive.
        
        Args:
            file_id (str): O ID do arquivo no Google Drive (hash na URL).
            file_path (str): O caminho e nome onde o arquivo será salvo localmente.
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                print(f"Iniciando download do arquivo {file_id}...")
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Progresso: {int(status.progress() * 100)}%.")
                    
            print(f"Arquivo salvo com sucesso em: {file_path}")
            
        except Exception as e:
            print(f"Ocorreu um erro ao baixar o arquivo: {e}")

    def list_files_in_folder(self, folder_id: str) -> list:
        """
        Lista todos os arquivos dentro de uma pasta específica no Google Drive.
        
        Args:
            folder_id (str): O ID da pasta no Google Drive.
            
        Returns:
            list: Lista de dicionários contendo id e name dos arquivos.
        """
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            
            if not items:
                print('Nenhum arquivo encontrado na pasta.')
            return items
            
        except Exception as e:
            print(f"Ocorreu um erro ao listar os arquivos: {e}")
            return []

    def download_files_from_folder(self, folder_id: str, download_dir: str = './', ignored_files_basenames: list = None) -> None:
        """
        Baixa todos os arquivos de uma pasta do Google Drive.
        
        Args:
            folder_id (str): O ID da pasta no Google Drive.
            download_dir (str): O diretório local onde os arquivos serão salvos.
            ignored_files_basenames (list): Lista de nomes base (sem extensão) para não baixar novamente.
        """
        import os
        
        if ignored_files_basenames is None:
            ignored_files_basenames = []
            
        # Garante que o diretório de download existe
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        files = self.list_files_in_folder(folder_id)
        
        for file in files:
            file_id = file['id']
            file_name = file['name']
            
            # Pega o nome sem a extensão (ex: itau_extrato_012026.pdf -> itau_extrato_012026)
            file_basename = file_name.rsplit('.', 1)[0]
            
            if file_basename in ignored_files_basenames:
                print(f"Pulo: '{file_name}' ignorado pois já consta como processado no banco de dados.")
                continue
                
            file_path = os.path.join(download_dir, file_name)
            
            print(f"\nBaixando arquivo encontrado: {file_name}")
            self.download_file(file_id, file_path)

# Exemplo de uso:
# drive = GoogleDriveData()
# drive.download_file('1W2qWe2uTc2G7XBXYh84J8tGoXXIzm85Moew4yJSueW4', 'arquivo_baixado.xlsx')
