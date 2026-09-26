from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/companies", tags=["Companies"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Company)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    db_company = crud.get_company_by_cif(db, cif=company.cif)
    if db_company:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este CIF")
    return crud.create_company(db=db, company=company)

@router.get("/{company_id}", response_model=schemas.Company)
def read_company(company_id: int, db: Session = Depends(get_db)):
    db_company = crud.get_company(db, company_id=company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_company

@router.put("/companies/{company_id}")
def update_company(company_id: int, company: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not db_company:
        # Si no existe, la creamos forzando el ID
        db_company = models.Company(id=company_id, **company.model_dump())
        db.add(db_company)
    else:
        # Si existe, la actualizamos
        for key, value in company.model_dump().items():
            setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company