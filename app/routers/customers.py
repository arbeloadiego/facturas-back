from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = crud.get_customer_by_cif(db, cif=customer.cif)
    if db_customer:
        raise HTTPException(status_code=400, detail="El CIF/NIF ya está registrado")
    return crud.create_customer(db=db, customer=customer)

@router.get("/", response_model=List[schemas.Customer])
def get_customers(
    search: Optional[str] = None,
    tab: str = "All",
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(models.Customer)

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