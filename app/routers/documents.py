from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/documents", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@router.get("/", response_model=List[schemas.Document])
def read_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_documents(db, skip=skip, limit=limit)