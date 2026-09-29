from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError 
from typing import List, Optional

from app.auth import get_current_user

from .. import crud, schemas, models
from ..database import SessionLocal

from sqlalchemy import or_, desc, asc

router = APIRouter(prefix="/customers", tags=["Customers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    company_id = current_user.get("id_company")
    
    # Comprobamos el CIF SOLO dentro de los clientes de esta empresa
    db_customer = db.query(models.Customer).filter(
        models.Customer.cif == customer.cif,
        models.Customer.id_company == company_id
    ).first()
    
    if db_customer:
        raise HTTPException(status_code=400, detail="El CIF/NIF ya está registrado en tu empresa")
    
    # Creamos el cliente pasándole el id_company al CRUD
    # (Asegúrate de que tu schemas.CustomerCreate o tu función crud.create_customer acepten id_company)
    new_customer = models.Customer(**customer.dict(), id_company=company_id)
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/", response_model=List[schemas.Customer])
def get_customers(
    search: Optional[str] = None,
    tab: str = "All",
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # <--- Requerimos el usuario activo
):
    company_id = current_user.get("id_company")
    query = db.query(models.Customer).filter(models.Customer.id_company == company_id)

    # 1. BÚSQUEDA TEXTO LIBRE (Search)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Customer.name.ilike(search_term),
                models.Customer.cif.ilike(search_term),
                models.Customer.email.ilike(search_term),
                models.Customer.city.ilike(search_term)
            )
        )

    # 2. PESTAÑAS (Tabs)
    if tab == "Active":
        # Clientes que tienen al menos un documento creado
        query = query.join(models.Document, models.Customer.id == models.Document.id_customer).distinct()
    elif tab == "Debtors":
        # Clientes que tienen al menos una factura PENDING
        query = query.join(models.Document, models.Customer.id == models.Document.id_customer)\
                     .filter(models.Document.type == "INVOICE", models.Document.status == "PENDING").distinct()

    # 3. ORDENACIÓN COLUMNAS (Sorting)
    # Mapeamos los nombres del frontend a las columnas reales de la BD
    sort_column_map = {
        "name": models.Customer.name,
        "cif": models.Customer.cif,
        "city": models.Customer.city,
        "created_at": models.Customer.created_at
    }
    
    sort_col = sort_column_map.get(sort_by, models.Customer.created_at)
    
    if sort_desc:
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    return query.all()

@router.get("/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.put("/{customer_id}", response_model=schemas.Customer)
def update_customer(customer_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Actualiza la información de un cliente existente."""
    
    db_customer = crud.update_customer(db, customer_id=customer_id, customer_data=customer)
    
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    # Buscamos el cliente asegurándonos de que es de su empresa
    db_customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id,
        models.Customer.id_company == company_id
    ).first()
    
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found or access denied")

    try:
        db.delete(db_customer)
        db.commit()
        return {"detail": "Cliente eliminado correctamente"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene documentos.")