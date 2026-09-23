from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Importamos los archivos que creamos en los pasos anteriores
from .. import crud, schemas
from ..database import SessionLocal

# Agrupamos todas estas rutas bajo el prefijo "/clientes"
router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

# Dependencia: Abre una sesión temporal con la Raspberry Pi y la cierra al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Crear un cliente nuevo (POST)
@router.post("/", response_model=schemas.ClienteResponse)
def create_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    # Primero comprobamos que no exista otro cliente con el mismo NIF
    db_cliente = crud.get_cliente_by_nif(db, nif=cliente.nif)
    if db_cliente:
        raise HTTPException(status_code=400, detail="El NIF ya está registrado")
    
    return crud.create_cliente(db=db, cliente=cliente)

# 2. Leer la lista de todos los clientes (GET)
@router.get("/", response_model=List[schemas.ClienteResponse])
def read_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clientes = crud.get_clientes(db, skip=skip, limit=limit)
    return clientes