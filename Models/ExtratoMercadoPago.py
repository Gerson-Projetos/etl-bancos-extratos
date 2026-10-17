import hashlib
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, event
from sqlalchemy.sql import func
from Conn.Database import Base

class ExtratoMercadoPago(Base):
    __tablename__ = 'extrato_mercado_pago'

    # Chave primária
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Colunas originais do extrato
    data_lancamento = Column(Date, nullable=False)
    descricao = Column(String(500), nullable=False)
    id_operacao = Column(String(50), nullable=True)
    valor = Column(Numeric(10, 2), nullable=True)
    saldo = Column(Numeric(10, 2), nullable=True)
    
    # Colunas de controle (Boas práticas de ETL)
    arquivo_origem = Column(String(255), nullable=True) # Ex: 'mercado_pago__261012133456.pdf'
    created_at = Column(DateTime, server_default=func.now())
    
    # Hash único combinando dados da transação para evitar duplicidade
    hash_transacao = Column(String(64), unique=True, nullable=True)

    def gerar_hash(self):
        """
        Gera um hash SHA-256 único para a transação.
        Garante que transações duplicadas não sejam inseridas no banco.
        """
        if self.id_operacao and self.data_lancamento and self.valor is not None:
            string_base = f"{self.data_lancamento.isoformat()}|{self.descricao.strip()}|{self.id_operacao.strip()}|{float(self.valor)}"
        elif self.data_lancamento and self.descricao and self.valor is not None:
            string_base = f"{self.data_lancamento.isoformat()}|{self.descricao.strip()}|{float(self.valor)}"
        elif self.data_lancamento and self.descricao and self.saldo is not None:
            string_base = f"{self.data_lancamento.isoformat()}|{self.descricao.strip()}|{float(self.saldo)}"
        else:
            string_base = f"{self.data_lancamento}|{self.descricao}|{self.id_operacao}|{self.id}"
            
        self.hash_transacao = hashlib.sha256(string_base.encode('utf-8')).hexdigest()
        return self.hash_transacao

    def __repr__(self):
        return f"<ExtratoMercadoPago(data='{self.data_lancamento}', descricao='{self.descricao}', id_operacao='{self.id_operacao}', valor={self.valor})>"


# ==========================================
# Lógica de Geração Automática do Hash
# ==========================================
@event.listens_for(ExtratoMercadoPago, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Gera um hash SHA-256 único para a transação antes de inseri-la no banco.
    Isso garante que o ETL não insira a mesma linha duas vezes.
    """
    target.gerar_hash()
