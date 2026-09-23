import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Cargar las variables secretas del archivo .env
load_dotenv()

# 2. Leer la contraseña y hacerla segura para la URL
mi_contrasena = os.getenv("DB_PASSWORD")
if not mi_contrasena:
    raise ValueError("No se ha encontrado DB_PASSWORD en el archivo .env")
    
password_segura = urllib.parse.quote_plus(mi_contrasena)

# 3. Construir la URL de conexión apuntando a la Raspberry Pi
DATABASE_URL = f"postgresql://admin_facturas:{password_segura}@db:5432/facturacion_produccion"

# 4. Inicializar el motor de la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base servirá como molde para crear nuestras tablas después
Base = declarative_base()