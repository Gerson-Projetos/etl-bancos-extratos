from google.oauth2 import service_account
# from google.auth.transport.requests import Request
import os.path

class GoogleApi:
    _path = os.path.dirname(os.path.realpath(__file__))
    
    def __init__(self) -> None:
        self.__creds = None
        self.__scope = [
            # 'https://www.googleapis.com/auth/spreadsheets.readonly',
            # 'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        self.__auth()

    def __auth(self):
        # Caminho para o arquivo JSON da conta de serviço
        service_account_file = f'{self._path}/../creds.json'
        
        if not os.path.exists(service_account_file):
            raise FileNotFoundError(
                f"Arquivo da conta de serviço não encontrado em: {service_account_file}\n"
                "Por favor, baixe o JSON da conta de serviço do Google Cloud Console e "
                "salve como 'creds.json' no diretório do projeto."
            )

        # Carrega as credenciais da conta de serviço
        self.__creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=self.__scope
        )

    @property
    def credentials(self):
        return self.__creds