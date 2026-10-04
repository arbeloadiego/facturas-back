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

def update_customer(db: Session, customer_id: int, customer_data: schemas.CustomerCreate):
    # 1. Buscamos el cliente en la base de datos
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    
    if db_customer:
        # 2. Actualizamos los campos usando los datos que vienen de React
        # Convertimos el esquema a diccionario (usa .dict() si usas Pydantic v1)
        update_data = customer_data.model_dump(exclude_unset=True) 
        
        for key, value in update_data.items():
            setattr(db_customer, key, value)
            
        # 3. Guardamos los cambios
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

def get_document(db: Session, document_id: int, company_id: int):
    return db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.id_company == company_id # Bloqueo de seguridad
    ).first()

def get_documents(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Document).filter(
        models.Document.id_company == company_id # Solo trae los de su empresa
    ).offset(skip).limit(limit).all()

def create_document(db: Session, document: schemas.DocumentCreate):
    # (Este se queda igual porque el id_company ya viene dentro del documentCreate)
    document_data = document.model_dump(exclude={"items"})
    db_document = models.Document(**document_data)
    
    for item in document.items:
        db_item = models.DocumentItem(**item.model_dump())
        db_document.items.append(db_item) 
        
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def delete_document(db: Session, document_id: int, company_id: int):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.id_company == company_id # Bloqueo de seguridad
    ).first()
    
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document

def update_document(db: Session, document_id: int, company_id: int, document: schemas.DocumentCreate):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.id_company == company_id # Bloqueo de seguridad
    ).first()
    
    if not db_document:
        return None

    document_data = document.model_dump(exclude={"items"})
    for key, value in document_data.items():
        setattr(db_document, key, value)
        
    db.query(models.DocumentItem).filter(models.DocumentItem.id_document == document_id).delete()
    
    for item in document.items:
        db_item = models.DocumentItem(**item.model_dump(), id_document=document_id)
        db.add(db_item)
        
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