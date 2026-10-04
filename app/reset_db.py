from app.database import engine, Base
# Es crucial importar los modelos para que SQLAlchemy sepa qué tablas existen
from app import models 

def reset_database():
    print("⚠️️ Borrando TODAS las tablas de la base de datos...")
    Base.metadata.drop_all(bind=engine)

    print("✨ Creando las tablas desde cero (incluyendo la nueva de Proyectos y la columna id_project)...")
    Base.metadata.create_all(bind=engine)

    print("✅ ¡Base de datos limpia y lista para usar!")

if __name__ == "__main__":
    reset_database()