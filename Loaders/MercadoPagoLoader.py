from sqlalchemy.orm import Session
from typing import List
from Loaders.DatabaseLoader import DatabaseLoader
from Models.ExtratoMercadoPago import ExtratoMercadoPago


class MercadoPagoLoader(DatabaseLoader):

    def __init__(self, session: Session):
        # Passa a sessão para a classe pai (DatabaseLoader)
        super().__init__(session)

    def load_to_database(self, records: List[ExtratoMercadoPago]) -> int:
        """
        Insere os registros de extrato do Mercado Pago no banco PostgreSQL,
        garantindo unicidade pelo campo hash_transacao.
        """
        valid_records = [r for r in records if isinstance(r, ExtratoMercadoPago)]
        
        if len(valid_records) != len(records):
            print(f"Aviso: {(len(records) - len(valid_records))} registros foram ignorados pois não são do tipo ExtratoMercadoPago.")

        return self._load_postgres(valid_records, ExtratoMercadoPago, unique_constraint='hash_transacao')
