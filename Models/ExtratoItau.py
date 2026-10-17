import hashlib
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, event
from sqlalchemy.sql import func
from Conn.Database import Base

class ExtratoItau(Base):
    __tablename__ = 'extrato_itau'

    # Chave primária
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Colunas originais da planilha
    data_lancamento = Column(Date, nullable=False)
    descricao = Column(String(255), nullable=False) # 'lançamentos'
    valor = Column(Numeric(10, 2), nullable=True)   # 'valor (R$)'
    saldo = Column(Numeric(10, 2), nullable=True)   # 'saldo (R$)'
    
    # Colunas de controle (Boas práticas de ETL)
    arquivo_origem = Column(String(255), nullable=True) # Ex: 'itau_extrato_012026.xlsx'
    created_at = Column(DateTime, server_default=func.now())
    
    #  hash combinando (data + descricao + valor)
    hash_transacao = Column(String(64), unique=True, nullable=True)

    def gerar_hash(self):
        """
        Gera um hash SHA-256 único para a transação.
        """
        if self.data_lancamento and self.descricao and self.valor is not None:
            string_base = f"{self.data_lancamento.isoformat()}|{self.descricao.strip()}|{float(self.valor)}"
        elif self.data_lancamento and self.descricao and self.saldo is not None:
            string_base = f"{self.data_lancamento.isoformat()}|{self.descricao.strip()}|{float(self.saldo)}"
        else:
            string_base = f"{self.data_lancamento}|{self.descricao}|{self.id}"
            
        self.hash_transacao = hashlib.sha256(string_base.encode('utf-8')).hexdigest()
        return self.hash_transacao

    def __repr__(self):
        return f"<ExtratoItau(data='{self.data_lancamento}', descricao='{self.descricao}', valor={self.valor})>"
# ==========================================
# Lógica de Geração Automática do Hash
# ==========================================
@event.listens_for(ExtratoItau, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Gera um hash SHA-256 único para a transação antes de inseri-la no banco.
    Isso garante que o ETL não insira a mesma linha duas vezes.
    """
    # Delega a geração de hash para o método da classe
    target.gerar_hash()
