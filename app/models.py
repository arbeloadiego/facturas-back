from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    nif = Column(String, unique=True, index=True, nullable=False)
    email = Column(String)

    # Esto no se guarda en la base de datos física. 
    # Es una ayuda de Python para poder ver todas las facturas de un cliente.
    facturas = relationship("Factura", back_populates="cliente")


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    concepto = Column(String, nullable=False)
    total = Column(Float, nullable=False)

    # Es una ayuda de Python para ver los datos del cliente desde una factura.
    cliente = relationship("Cliente", back_populates="facturas")