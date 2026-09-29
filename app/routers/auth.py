from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import SessionLocal

router = APIRouter(tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. RUTA PARA REGISTRAR AL PRIMER USUARIO
@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Comprobar si el email ya existe
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Encriptar la contraseña antes de guardarla
    hashed_password = auth.get_password_hash(user.password)
    
    # Crear el usuario en la base de datos
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_pass=hashed_password,
        name=user.name,
        surname=user.surname
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. RUTA PARA INICIAR SESIÓN (LOGIN)
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Buscamos al usuario
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    # 2. Comprobamos la contraseña
    if not user or not auth.verify_password(form_data.password, user.hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_company = db.query(models.UserCompany).filter(models.UserCompany.id_user == user.id).first()
    company_id = user_company.id_company if user_company else None
    
    access_token = auth.create_access_token(
        data={
            "sub": user.email, 
            "id": user.id,
            "id_company": company_id  
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}