from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import crud, schemas, models
from ..database import SessionLocal
from ..auth import create_access_token, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    new_user = crud.create_user(db=db, user=user)
    
    access_token = create_access_token(
        data={"sub": new_user.email, "id_company": None}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "message": "Usuario creado con éxito"
    }

class UserUpdate(BaseModel):
    name: str
    surname: str
    username: str

@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Sacamos el email del token
    user_email = current_user.get("sub")
    
    # Buscamos al usuario
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return user

@router.put("/me")
def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizamos solo los campos permitidos
    user.name = user_data.name
    user.surname = user_data.surname
    user.username = user_data.username
    
    db.commit()
    db.refresh(user)
    return user