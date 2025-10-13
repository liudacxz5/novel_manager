from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()


@router.post("/settings/", response_model=schemas.SettingEntry)
def create_setting(setting: schemas.SettingEntryCreate, db: Session = Depends(get_db)):
    return crud.create_setting_entry(db=db, entry=setting)


@router.get("/settings/{setting_id}", response_model=schemas.SettingEntry)
def read_setting(setting_id: int, db: Session = Depends(get_db)):
    db_setting = crud.get_setting_entry(db, entry_id=setting_id)
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return db_setting