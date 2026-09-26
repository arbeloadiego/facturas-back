from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List

# ==========================================
# 1. SCHEMAS PARA CLIENTES (Customers)
# ==========================================
class CustomerBase(BaseModel):
    cif: str
    name: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Spain"

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. SCHEMAS PARA EMPRESAS (Companies)
# ==========================================
class CompanyBase(BaseModel):
    cif: str
    name: str
    legal_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    country: str = "Spain"
    currency: str = "EUR"
    # Añadidos para que coincidan con el frontend (Settings.jsx)
    telephone: Optional[str] = None
    website: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

# NUEVO: Esquema para actualizar la empresa
class CompanyUpdate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. SCHEMAS PARA USUARIOS (Users)
# ==========================================
class UserBase(BaseModel):
    username: str
    email: str
    name: str
    surname: str

class UserCreate(UserBase):
    password: str  # Solo de entrada, nunca se devuelve

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. SCHEMAS PARA DOCUMENTOS Y LÍNEAS (Documents & Items)
# ==========================================
class DocumentItemBase(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    tax_rate: float = 21.0

class DocumentItemCreate(DocumentItemBase):
    pass

class DocumentItem(DocumentItemBase):
    id: int
    id_document: int

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    type: str  # "INVOICE" o "QUOTE"
    number: str
    issue_date: date
    due_date: Optional[date] = None
    status: str = "PENDING"
    total_amount: float = 0.0
    id_company: int
    id_customer: int

class DocumentCreate(DocumentBase):
    items: List[DocumentItemCreate]

class Document(DocumentBase):
    id: int
    created_at: datetime
    items: List[DocumentItem] = []
    
    customer: Optional[Customer] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentStatusUpdate(BaseModel):
    status: str