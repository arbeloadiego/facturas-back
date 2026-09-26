from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import date

from app import models

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/documents", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Calcula las métricas principales directamente en la base de datos"""
    
    # 1. Total Cobrado (Suma total_amount de INVOICE + PAID)
    total_revenue = db.query(func.sum(models.Document.total_amount))\
        .filter(models.Document.type == "INVOICE", models.Document.status == "PAID").scalar() or 0.0
        
    # 2. Balance Pendiente (Suma total_amount de INVOICE + PENDING)
    outstanding_balance = db.query(func.sum(models.Document.total_amount))\
        .filter(models.Document.type == "INVOICE", models.Document.status == "PENDING").scalar() or 0.0
        
    # 3. Presupuestos Pendientes (Cuenta IDs de QUOTE + SENT)
    pending_quotes = db.query(func.count(models.Document.id))\
        .filter(models.Document.type == "QUOTE", models.Document.status == "SENT").scalar() or 0
        
    # 4. Total Clientes (Cuenta IDs)
    total_customers = db.query(func.count(models.Customer.id)).scalar() or 0
    
    return {
        "totalRevenue": total_revenue,
        "outstandingBalance": outstanding_balance,
        "pendingQuotes": pending_quotes,
        "totalCustomers": total_customers
    }

@router.post("/", response_model=schemas.Document)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    # 1. Verificar que el cliente existe
    customer = crud.get_customer(db, customer_id=document.id_customer)
    if not customer:
        raise HTTPException(status_code=404, detail="El cliente indicado no existe")
        
    # 2. Verificar que la empresa emisora existe
    company = crud.get_company(db, company_id=document.id_company)
    if not company:
        raise HTTPException(status_code=404, detail="La empresa indicada no existe")
    
    return crud.create_document(db=db, document=document)

@router.get("/{document_id}", response_model=schemas.Document)
def read_document(document_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un documento específico por su ID"""
    db_document = crud.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return db_document

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Elimina un documento de la base de datos"""
    db_document = crud.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    crud.delete_document(db, document_id=document_id)
    return {"detail": "Documento eliminado con éxito"}

@router.put("/{document_id}", response_model=schemas.Document)
def update_document(document_id: int, document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """Actualiza un documento existente y sus líneas"""
    db_document = crud.update_document(db, document_id=document_id, document=document)
    if not db_document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return db_document

@router.patch("/{document_id}/status", response_model=schemas.Document)
def update_document_status(document_id: int, status_data: schemas.DocumentStatusUpdate, db: Session = Depends(get_db)):
    """Actualiza únicamente el estado de un documento (ej: de PENDING a PAID)"""
    db_document = crud.get_document(db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    db_document.status = status_data.status
    db.commit()
    db.refresh(db_document)
    return db_document

@router.get("/", response_model=List[schemas.Document])
def get_documents(
    doc_type: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = None,
    status: Optional[str] = None,
    amount_op: Optional[str] = None,
    amount_val: Optional[float] = None,
    date_op: Optional[str] = None,
    date_val: Optional[date] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Empezamos con una consulta que coge TODOS los documentos
    query = db.query(models.Document)

    # 1. Filtro por tipo (Factura o Presupuesto)
    if doc_type:
        query = query.filter(models.Document.type == doc_type.upper())

    # 2. Filtro de Estado
    if status:
        query = query.filter(models.Document.status == status.upper())

    # 3. Filtro de Cantidad (Dinámico según el operador)
    if amount_op and amount_val is not None:
        if amount_op == '>':
            query = query.filter(models.Document.total_amount > amount_val)
        elif amount_op == '<':
            query = query.filter(models.Document.total_amount < amount_val)
        elif amount_op == '=':
            query = query.filter(models.Document.total_amount == amount_val)

    # 4. Filtro de Fecha (Dinámico según el operador)
    if date_op and date_val:
        if date_op == '>=':
            query = query.filter(models.Document.issue_date >= date_val)
        elif date_op == '<=':
            query = query.filter(models.Document.issue_date <= date_val)
        elif date_op == '=':
            query = query.filter(models.Document.issue_date == date_val)

    # 5. Búsqueda de texto (Buscamos en el número de factura o hacemos un JOIN con el cliente)
    if search:
        search_term = f"%{search}%"
        # Hacemos JOIN con Customer para poder buscar por el nombre del cliente
        query = query.join(models.Customer).filter(
            or_(
                models.Document.number.ilike(search_term),
                models.Customer.name.ilike(search_term)
            )
        )

    # Ordenamos por fecha de más reciente a más antigua
    query = query.order_by(models.Document.issue_date.desc())

    if limit:
        query = query.limit(limit)

    # Finalmente, ejecutamos la consulta optimizada en PostgreSQL
    return query.all()