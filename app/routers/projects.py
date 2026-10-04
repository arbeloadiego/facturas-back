from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models
from app.auth import get_current_user
from .. import schemas
from ..database import SessionLocal

router = APIRouter(prefix="/projects", tags=["Projects"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    # 1. Verificamos que el cliente asociado al proyecto existe y es de esta empresa
    customer = db.query(models.Customer).filter(
        models.Customer.id == project.id_customer,
        models.Customer.id_company == company_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe o no pertenece a tu empresa.")

    # 2. Creamos el proyecto inyectando el id_company desde el token por seguridad
    new_project = models.Project(
        **project.model_dump(),
        id_company=company_id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=List[schemas.Project])
def get_projects(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    # Devolvemos solo los proyectos de la empresa logueada
    projects = db.query(models.Project).filter(models.Project.id_company == company_id).all()
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.id_company == company_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project_data: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    db_project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.id_company == company_id
    ).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    # Extraemos solo los campos que se han enviado en la petición para no sobreescribir con nulos
    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
        
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}/documents", response_model=List[schemas.Document])
def get_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("id_company")
    
    # Validamos que el usuario tiene acceso al proyecto
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.id_company == company_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    # Buscamos todas las facturas y presupuestos asociados a este proyecto
    documents = db.query(models.Document).filter(
        models.Document.id_project == project_id,
        models.Document.id_company == company_id
    ).all()
    
    return documents

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    company_id = int(current_user["id_company"])
    
    # 1. Buscamos el proyecto
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.id_company == company_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado o acceso denegado")
        
    # 2. Desvinculamos las facturas/presupuestos asociados (para no borrarlos)
    db.query(models.Document).filter(models.Document.id_project == project_id).update({"id_project": None})
    
    # 3. Borramos el proyecto
    db.delete(project)
    db.commit()
    
    return {"detail": "Proyecto eliminado con éxito"}