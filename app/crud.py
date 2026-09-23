from sqlalchemy.orm import Session
from . import models, schemas

# ==========================================
# CUSTOMER OPERATIONS (Antiguos Clientes)
# ==========================================

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_cif(db: Session, cif: str):
    return db.query(models.Customer).filter(models.Customer.cif == cif).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    # model_dump() convierte el esquema de Pydantic directamente en un diccionario
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

# ==========================================
# COMPANY OPERATIONS (Empresas)
# ==========================================

def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_company_by_cif(db: Session, cif: str):
    return db.query(models.Company).filter(models.Company.cif == cif).first()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# ==========================================
# USER OPERATIONS (Usuarios)
# ==========================================

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # TODO: Más adelante implementaremos bcrypt para cifrar esto de verdad
    fake_hashed_password = user.password + "_hashed" 
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        name=user.name,
        surname=user.surname,
        hashed_pass=fake_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ==========================================
# DOCUMENT OPERATIONS (Facturas y Presupuestos)
# ==========================================

def get_document(db: Session, document_id: int):
    # Obtiene un documento (y gracias a las relationships en models.py, 
    # también traerá sus items asociados automáticamente)
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Document).offset(skip).limit(limit).all()

def create_document(db: Session, document: schemas.DocumentCreate):
    # 1. Extraemos los datos de la cabecera excluyendo la lista de items
    document_data = document.model_dump(exclude={"items"})
    
    # 2. Creamos la instancia de la cabecera (Factura o Presupuesto)
    db_document = models.Document(**document_data)
    
    # 3. Recorremos los items que nos manda el frontend y los añadimos
    for item in document.items:
        db_item = models.DocumentItem(**item.model_dump())
        # Magia de SQLAlchemy: Al hacer append, él solo rellenará el id_document
        db_document.items.append(db_item) 
        
    # 4. Guardamos todo en la base de datos en una sola transacción segura
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document

# ==========================================
# RELATIONSHIPS & TELEPHONES (Tablas extra)
# ==========================================

def assign_user_to_company(db: Session, id_user: int, id_company: int, role: str = "viewer"):
    # Crea el vínculo entre un usuario y una empresa con un rol específico
    db_user_company = models.UserCompany(
        id_user=id_user, 
        id_company=id_company, 
        user_role=role
    )
    db.add(db_user_company)
    db.commit()
    return db_user_company

def add_company_telephone(db: Session, id_company: int, telephone: str):
    db_telephone = models.CompanyTelephone(id_company=id_company, telephone=telephone)
    db.add(db_telephone)
    db.commit()
    db.refresh(db_telephone)
    return db_telephone