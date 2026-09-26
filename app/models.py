from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Asegúrate de importar Base desde tu archivo database.py
from .database import Base

# --- 1. TABLAS INTERMEDIAS Y ENTIDADES DÉBILES ---

class UserCompany(Base):
    __tablename__ = "user_company"
    
    id_user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    id_company = Column(Integer, ForeignKey("company.id"), primary_key=True)
    user_role = Column(String, default="viewer")
    
    # Relaciones
    user = relationship("User", back_populates="company_roles")
    company = relationship("Company", back_populates="user_roles")

class UserTelephone(Base):
    __tablename__ = "user_telephones"
    
    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    telephone = Column(String, nullable=False)
    
    user = relationship("User", back_populates="telephones")

class CompanyTelephone(Base):
    __tablename__ = "company_telephones"
    
    id = Column(Integer, primary_key=True, index=True)
    id_company = Column(Integer, ForeignKey("company.id"), nullable=False)
    telephone = Column(String, nullable=False)
    
    company = relationship("Company", back_populates="telephones")


# --- 2. USUARIOS Y EMPRESAS (Access & Emitter) ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_pass = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    company_roles = relationship("UserCompany", back_populates="user", cascade="all, delete-orphan")
    telephones = relationship("UserTelephone", back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "company"
    
    id = Column(Integer, primary_key=True, index=True)
    cif = Column(String, unique=True, nullable=False, index=True)
    
    name = Column(String, nullable=False)
    legal_name = Column(String)
    logo_url = Column(String)
    website = Column(String, nullable=True)
    email = Column(String)
    telephone = Column(String, nullable=True)
    
    address = Column(String)
    city = Column(String)
    postal_code = Column(String)
    province = Column(String)
    country = Column(String, default="Spain")
    
    currency = Column(String, default="EUR")
    iban = Column(String)
    swift_bic = Column(String)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    user_roles = relationship("UserCompany", back_populates="company", cascade="all, delete-orphan")
    telephones = relationship("CompanyTelephone", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company")


# --- 3. CLIENTES Y DOCUMENTOS (Receivers & Documents) ---

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    cif = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    telephone = Column(String, nullable=True)
    address = Column(String)
    city = Column(String)
    postal_code = Column(String)
    country = Column(String, default="Spain")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relaciones
    documents = relationship("Document", back_populates="customer")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False, index=True) # INVOICE o QUOTE
    number = Column(String, unique=True, nullable=False, index=True)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date)
    status = Column(String, default="PENDING")
    total_amount = Column(Float, default=0.0)
    
    id_company = Column(Integer, ForeignKey("company.id"), nullable=False)
    id_customer = Column(Integer, ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relaciones
    company = relationship("Company", back_populates="documents")
    customer = relationship("Customer", back_populates="documents")
    items = relationship("DocumentItem", back_populates="document", cascade="all, delete-orphan")


class DocumentItem(Base):
    __tablename__ = "document_items"
    
    id = Column(Integer, primary_key=True, index=True)
    id_document = Column(Integer, ForeignKey("documents.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=21.0)
    
    # Relaciones
    document = relationship("Document", back_populates="items")