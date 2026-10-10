from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from Conn.Database import Base

class Conta(Base):
    __tablename__ = 'contas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    banco = Column(String(100), nullable=False)           # Ex: 'Itau', 'Mercado Pago', 'Clear'
    descricao = Column(String(255), nullable=True)        # Ex: 'Conta corrente principal'
    tbl_extrato = Column(String(100), nullable=True)      # Ex: 'extrato_itau', 'extrato_mercado_pago'
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Conta(banco='{self.banco}', tbl_extrato='{self.tbl_extrato}')>"
