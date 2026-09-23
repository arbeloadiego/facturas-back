from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

# 1. Importamos todos los routers
from .routers import customers, documents, companies, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Facturación")

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción aquí pondrías la URL de tu React
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)
# -----------------------------

# 2. Conectamos las rutas a la aplicación principal
app.include_router(customers.router)
app.include_router(documents.router)
app.include_router(companies.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"estado": "Activo", "mensaje": "API estructurada modularmente funcionando."}