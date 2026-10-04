from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt

# Usamos ÚNICAMENTE python-jose para todo lo relacionado con JWT
from jose import jwt, JWTError 

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "tu_super_clave_secreta_muy_larga_y_dificil_de_adivinar"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña en texto plano con la encriptada en la BD"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """Encripta una contraseña nueva"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Genera el pasaporte (JWT Token) para el usuario"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    # Aquí ahora usa automáticamente jwt de jose
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verifica el token en cada petición al servidor y extrae la empresa"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Le decimos a Python que pueden ser str/int o None
        email: Optional[str] = payload.get("sub")
        id_company: Optional[int] = payload.get("id_company")
        
        if email is None:
            raise credentials_exception
            
    except JWTError: 
        raise credentials_exception
        
    if id_company is None:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu usuario no tiene ninguna empresa asignada."
        )
        
    return payload

def get_user_without_company(token: str = Depends(oauth2_scheme)):
    """Verifica el token, pero permite el paso a usuarios que aún no tienen empresa"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError: 
        raise credentials_exception
        
    return payload