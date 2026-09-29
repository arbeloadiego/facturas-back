from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app import models
from app.auth import get_current_user, get_user_without_company, create_access_token

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/companies", tags=["Companies"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 1. ESQUEMA PARA EL ONBOARDING ---
# Lo definimos aquí para asegurarnos de que acepta todos los campos del Wizard de React
class CompanyOnboarding(BaseModel):
    name: str
    legal_name: str | None = None
    cif: str
    email: str | None = None
    telephone: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    country: str | None = "España"
    currency: str | None = "EUR"
    iban: str | None = None
    swift_bic: str | None = None

# --- 2. RUTA DE ONBOARDING (LA QUE DABA ERROR 404) ---
@router.post("/onboarding")
def create_company_onboarding(
    company_data: CompanyOnboarding, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_user_without_company) 
):
    # Obtenemos el email del usuario logueado desde su token actual
    user_email = current_user.get("sub")
    
    # 1. Buscamos al usuario en la base de datos
    db_user = db.query(models.User).filter(models.User.email == user_email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Comprobamos si el CIF ya existe por si acaso
    existing_company = db.query(models.Company).filter(models.Company.cif == company_data.cif).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este CIF")

    # 3. Creamos la nueva empresa
    new_company = models.Company(
        name=company_data.name,
        legal_name=company_data.legal_name,
        cif=company_data.cif,
        email=company_data.email,
        telephone=company_data.telephone,
        website=company_data.website,
        address=company_data.address,
        city=company_data.city,
        province=company_data.province,
        postal_code=company_data.postal_code,
        country=company_data.country,
        currency=company_data.currency,
        iban=company_data.iban,
        swift_bic=company_data.swift_bic
    )
    
    try:
        # Guardamos la empresa
        db.add(new_company)
        db.flush() # Hace un guardado temporal para conseguir el ID de la empresa
        
        # 4. VINCULAMOS LA EMPRESA AL USUARIO
        db_user.id_company = new_company.id
        db.commit()
        db.refresh(new_company)
        
        # 5. CREAMOS EL NUEVO TOKEN (Ahora incluye el id_company)
        new_token = create_access_token(
            data={"sub": db_user.email, "id_company": new_company.id}
        )
        
        # Devolvemos el token nuevo a React
        return {
            "message": "Empresa configurada con éxito", 
            "new_token": new_token
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error interno: {e}") # Para que lo veas en la consola si falla
        raise HTTPException(status_code=500, detail="Error al guardar la empresa en la base de datos.")


# --- 3. TUS RUTAS EXISTENTES ---

@router.post("/", response_model=schemas.Company)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    db_company = crud.get_company_by_cif(db, cif=company.cif)
    if db_company:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este CIF")
    return crud.create_company(db=db, company=company)

@router.get("/me", response_model=schemas.Company)
def get_my_company(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
    return company

@router.put("/me", response_model=schemas.Company)
def update_my_company(
    company_data: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    for key, value in company_data.dict().items():
        setattr(company, key, value)
        
    db.commit()
    db.refresh(company)
    return company