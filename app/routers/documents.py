from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import date

from app import models

from .. import crud, schemas
from ..database import SessionLocal
from ..auth import get_current_user 

router = APIRouter(prefix="/documents", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    company_id = current_user.get("id_company")
    
    # 1. Total Cobrado (Aislado por empresa)
    total_revenue = db.query(func.sum(models.Document.total_amount))\
        .filter(
            models.Document.type == "INVOICE", 
            models.Document.status == "PAID",
            models.Document.id_company == company_id
        ).scalar() or 0.0
        
    # 2. Balance Pendiente (Aislado por empresa)
    outstanding_balance = db.query(func.sum(models.Document.total_amount))\
        .filter(
            models.Document.type == "INVOICE", 
            models.Document.status == "PENDING",
            models.Document.id_company == company_id
        ).scalar() or 0.0
        
    # 3. Presupuestos Pendientes (Aislado por empresa)
    pending_quotes = db.query(func.count(models.Document.id))\
        .filter(
            models.Document.type == "QUOTE", 
            models.Document.status == "SENT",
            models.Document.id_company == company_id
        ).scalar() or 0
        
    # 4. Total Clientes (Aislado por empresa)
    total_customers = db.query(func.count(models.Customer.id))\
        .filter(models.Customer.id_company == company_id)\
        .scalar() or 0
    
    return {
        "totalRevenue": total_revenue,
        "outstandingBalance": outstanding_balance,
        "pendingQuotes": pending_quotes,
        "totalCustomers": total_customers
    }

@router.post("/", response_model=schemas.Document)
def create_document(
    document: schemas.DocumentCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # <-- REQUERIMOS USUARIO
):
    company_id = current_user.get("id_company")
    
   
    document.id_company = company_id
    
    # Verificar que el cliente existe Y pertenece a la empresa
    customer = crud.get_customer(db, customer_id=document.id_customer)
    if not customer or customer.id_company != company_id:
        raise HTTPException(status_code=404, detail="El cliente indicado no existe o no pertenece a tu empresa")
    
    return crud.create_document(db=db, document=document)

@router.get("/{document_id}", response_model=schemas.Document)
def read_document(
    document_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    db_document = crud.get_document(db, document_id=document_id)
    
    if not db_document or db_document.id_company != company_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado o acceso denegado")
        
    return db_document

@router.delete("/{document_id}")
def delete_document(
    document_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    db_document = crud.get_document(db, document_id=document_id)
    if not db_document or db_document.id_company != company_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado o acceso denegado")
    
    crud.delete_document(db, document_id=document_id)
    return {"detail": "Documento eliminado con éxito"}

@router.put("/{document_id}", response_model=schemas.Document)
def update_document(
    document_id: int, 
    document: schemas.DocumentCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    # Comprobamos propiedad antes de actualizar
    db_document = crud.get_document(db, document_id=document_id)
    if not db_document or db_document.id_company != company_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado o acceso denegado")
        
    # Forzamos la empresa en los datos entrantes por seguridad
    document.id_company = company_id
    
    updated_document = crud.update_document(db, document_id=document_id, document=document)
    return updated_document

@router.patch("/{document_id}/status", response_model=schemas.Document)
def update_document_status(
    document_id: int, 
    status_data: schemas.DocumentStatusUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    db_document = crud.get_document(db, document_id=document_id)
    if not db_document or db_document.id_company != company_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado o acceso denegado")
    
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    company_id = current_user.get("id_company")
    
    # CANDADO PRINCIPAL: Empezamos filtrando obligatoriamente por la empresa
    query = db.query(models.Document).filter(models.Document.id_company == company_id)

    # 1. Filtro por tipo
    if doc_type:
        query = query.filter(models.Document.type == doc_type.upper())

    # 2. Filtro de Estado
    if status:
        query = query.filter(models.Document.status == status.upper())

    # 3. Filtro de Cantidad
    if amount_op and amount_val is not None:
        if amount_op == '>':
            query = query.filter(models.Document.total_amount > amount_val)
        elif amount_op == '<':
            query = query.filter(models.Document.total_amount < amount_val)
        elif amount_op == '=':
            query = query.filter(models.Document.total_amount == amount_val)

    # 4. Filtro de Fecha
    if date_op and date_val:
        if date_op == '>=':
            query = query.filter(models.Document.issue_date >= date_val)
        elif date_op == '<=':
            query = query.filter(models.Document.issue_date <= date_val)
        elif date_op == '=':
            query = query.filter(models.Document.issue_date == date_val)

    # 5. Búsqueda de texto
    if search:
        search_term = f"%{search}%"
        query = query.join(models.Customer).filter(
            or_(
                models.Document.number.ilike(search_term),
                models.Customer.name.ilike(search_term)
            )
        )

    query = query.order_by(models.Document.issue_date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()