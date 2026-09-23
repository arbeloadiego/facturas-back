from sqlalchemy.orm import Session
from . import models, schemas

# ==========================================
# OPERACIONES DE LECTURA (READ)
# ==========================================

def get_cliente(db: Session, cliente_id: int):
    # Busca un cliente por su número de ID interno
    return db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()

def get_cliente_by_nif(db: Session, nif: str):
    # Fundamental para comprobar si un cliente ya existe antes de crearlo
    return db.query(models.Cliente).filter(models.Cliente.nif == nif).first()

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    # Devuelve una lista de clientes con paginación (por defecto 100)
    return db.query(models.Cliente).offset(skip).limit(limit).all()


# ==========================================
# OPERACIONES DE ESCRITURA (CREATE)
# ==========================================

def create_cliente(db: Session, cliente: schemas.ClienteCreate):
    # 1. Transformamos el esquema de seguridad (Pydantic) en un modelo de base de datos (SQLAlchemy)
    db_cliente = models.Cliente(
        nombre=cliente.nombre, 
        nif=cliente.nif, 
        email=cliente.email
    )
    
    # 2. Añadimos el objeto a la "cinta transportadora"
    db.add(db_cliente)
    
    # 3. Guardamos los cambios físicamente en la Raspberry Pi
    db.commit()
    
    # 4. Refrescamos el objeto de Python para que obtenga su nuevo ID autogenerado por PostgreSQL
    db.refresh(db_cliente)
    
    return db_cliente


def create_factura(db: Session, factura: schemas.FacturaCreate):
    # Transforma los datos validados al modelo de la base de datos
    db_factura = models.Factura(
        cliente_id=factura.cliente_id,
        concepto=factura.concepto,
        total=factura.total
    )
    db.add(db_factura)
    db.commit()
    db.refresh(db_factura)
    return db_factura

def get_facturas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Factura).offset(skip).limit(limit).all()