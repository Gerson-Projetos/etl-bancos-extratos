from sqlalchemy.orm import Session
from typing import List
from Loaders.DatabaseLoader import DatabaseLoader
from Models.ExtratoItau import ExtratoItau
# from sqlalchemy import text


class ItauLoader(DatabaseLoader):

    def __init__(self, session: Session):
        # Passa a sessão para a classe pai (DatabaseLoader)
        super().__init__(session)

    def load_to_database(self, records: List[ExtratoItau]) -> int:
        """
        Aqui você pode adicionar lógicas extras, como validações
        """
       #garantir que só estamos inserindo ExtratoItau
        valid_records = [r for r in records if isinstance(r, ExtratoItau)]
        
        if len(valid_records) != len(records):
            print(f"Aviso: {(len(records) - len(valid_records))} registros foram ignorados pois não são do tipo ExtratoItau.")

        return self._load_postgres(valid_records, ExtratoItau, unique_constraint='hash_transacao')
