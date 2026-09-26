from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .auth import get_current_user

# 1. Importamos todos los routers
from .routers import customers, documents, companies, users, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Facturación")

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    # Pon los puertos donde suele arrancar tu React en local
    allow_origins=["http://localhost:5173", "http://localhost:3000"], 
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
app.include_router(auth.router)

app.include_router(customers.router, dependencies=[Depends(get_current_user)])
app.include_router(documents.router, dependencies=[Depends(get_current_user)])

@app.get("/")
def read_root():
    return {"estado": "Activo", "mensaje": "API estructurada modularmente funcionando."}