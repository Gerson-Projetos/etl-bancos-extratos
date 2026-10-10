from sqlalchemy.orm import Session
from typing import List, Type
from sqlalchemy.dialects.postgresql import insert

class DatabaseLoader:
    def __init__(self, session: Session):
        self.session = session

    def _load_postgres(self, records: List[object], model_class: Type, unique_constraint: str) -> int:
        """
        Insere múltiplos registros de uma vez só no banco PostgreSQL, ignorando os
        que já existem baseados na constraint única (Ex: hash_transacao).
        """
        if not records:
            return 0
            
        dados = []
        for r in records:
            # Força a geração da constraint/hash 
            if hasattr(r, 'gerar_hash'):
                r.gerar_hash()
                
            # Extrai os atributos do objeto para um dicionário
            row_dict = {}
            for c in model_class.__table__.columns:
                val = getattr(r, c.name)
                # Ignora a coluna de Chave Primária
                if c.primary_key and val is None:
                    continue
                row_dict[c.name] = val
                
            dados.append(row_dict)
            
        # Monta a query pro Postgres
        stmt = insert(model_class).values(dados)
        
        # Diz ao banco para ignorar em caso de conflito 
        stmt = stmt.on_conflict_do_nothing(index_elements=[unique_constraint])
        
        # Forçamos o Postgres a retornar o 'id' das linhas que ele inseriu.
        stmt = stmt.returning(model_class.id)
        resultado = self.session.execute(stmt)
        
        #  traz o número de inserções reais.
        linhas_inseridas = len(resultado.fetchall())
        return linhas_inseridas

