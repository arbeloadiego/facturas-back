from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# ==========================================
# ESQUEMAS DE FACTURA
# ==========================================
class FacturaBase(BaseModel):
    concepto: str
    total: float

class FacturaCreate(FacturaBase):
    cliente_id: int

class FacturaResponse(FacturaBase):
    id: int
    cliente_id: int

    # Esto permite que Pydantic sepa leer el objeto que viene de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESQUEMAS DE CLIENTE
# ==========================================
class ClienteBase(BaseModel):
    nombre: str
    nif: str
    email: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass # Usa los mismos campos que ClienteBase sin añadir nada nuevo

class ClienteResponse(ClienteBase):
    id: int
    # Gracias a esto, al pedir un cliente, verás de golpe todas sus facturas
    facturas: List[FacturaResponse] = []

    model_config = ConfigDict(from_attributes=True)