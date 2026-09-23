from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/facturas", tags=["Facturas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.FacturaResponse)
def create_factura(factura: schemas.FacturaCreate, db: Session = Depends(get_db)):
    # Verificar que el cliente existe en la base de datos
    cliente = crud.get_cliente(db, cliente_id=factura.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente indicado no existe")
    
    return crud.create_factura(db=db, factura=factura)

@router.get("/", response_model=List[schemas.FacturaResponse])
def read_facturas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_facturas(db, skip=skip, limit=limit)