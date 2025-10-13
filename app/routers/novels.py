from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()


@router.post("/novels/", response_model=schemas.Novel)
def create_novel(novel: schemas.NovelCreate, db: Session = Depends(get_db)):
    return crud.create_novel(db=db, novel=novel)


@router.get("/novels/{novel_id}", response_model=schemas.Novel)
def read_novel(novel_id: int, db: Session = Depends(get_db)):
    db_novel = crud.get_novel(db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return db_novel


@router.put("/novels/{novel_id}", response_model=schemas.Novel)
def update_novel(novel_id: int, novel: schemas.NovelUpdate, db: Session = Depends(get_db)):
    db_novel = crud.update_novel(db, novel_id=novel_id, novel=novel)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return db_novel


@router.delete("/novels/{novel_id}", response_model=schemas.Novel)
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    db_novel = crud.delete_novel(db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return db_novel