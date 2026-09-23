from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import clientes, facturas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Facturación")

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción aquí pondrías la URL de tu React. Con "*" permitimos todo por ahora.
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)
# -----------------------------

app.include_router(clientes.router)
app.include_router(facturas.router)

@app.get("/")
def read_root():
    return {"estado": "Activo", "mensaje": "API estructurada modularmente funcionando."}