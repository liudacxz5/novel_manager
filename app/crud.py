from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Dict

# --- Novel CRUD ---
def get_novel(db: Session, novel_id: int):
    return db.query(models.Novel).filter(models.Novel.id == novel_id).first()

def get_novels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Novel).offset(skip).limit(limit).all()

def create_novel(db: Session, novel: schemas.NovelCreate):
    db_novel = models.Novel(**novel.model_dump())
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel

def update_novel(db: Session, novel_id: int, novel_update: schemas.NovelUpdate):
    db_novel = get_novel(db, novel_id)
    if db_novel:
        update_data = novel_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_novel, key, value)
        db.commit()
        db.refresh(db_novel)
    return db_novel

def delete_novel(db: Session, novel_id: int):
    db_novel = get_novel(db, novel_id)
    if db_novel:
        db.delete(db_novel)
        db.commit()
    return db_novel


# --- Setting Type CRUD ---
def get_setting_type(db: Session, type_id: int):
    return db.query(models.SettingType).filter(models.SettingType.id == type_id).first()

def get_setting_types_by_novel(db: Session, novel_id: int):
    return db.query(models.SettingType).filter(models.SettingType.novel_id == novel_id).order_by(models.SettingType.name).all()

def create_setting_type(db: Session, setting_type: schemas.SettingTypeCreate, novel_id: int):
    db_type = models.SettingType(**setting_type.model_dump(), novel_id=novel_id)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


# --- Setting Entry & Field CRUD ---
def get_setting_entry(db: Session, entry_id: int):
    return db.query(models.SettingEntry).filter(models.SettingEntry.id == entry_id).first()

def get_setting_entry_by_name_and_novel(db: Session, novel_id: int, entry_name: str):
    return db.query(models.SettingEntry).filter(
        models.SettingEntry.novel_id == novel_id,
        models.SettingEntry.name == entry_name
    ).first()

def create_setting_entry(db: Session, entry: schemas.SettingEntryCreate, novel_id: int, type_id: int):
    db_entry = models.SettingEntry(**entry.model_dump(), novel_id=novel_id, setting_type_id=type_id)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def update_setting_entry_with_fields(db: Session, entry_id: int, name: str, fields_data: List[Dict[str, str]]):
    db_entry = get_setting_entry(db, entry_id)
    if not db_entry:
        return None

    db_entry.name = name

    existing_fields_map = {str(field.id): field for field in db_entry.fields}
    processed_field_ids = set()

    for index, field_data in enumerate(fields_data):
        field_id = field_data.get("id")
        key = field_data.get("key")
        value = field_data.get("value")

        if not key:
            continue

        if field_id and field_id in existing_fields_map:
            field_to_update = existing_fields_map[field_id]
            field_to_update.key = key
            field_to_update.value = value
            field_to_update.order_index = index
            processed_field_ids.add(field_id)
        else:
            new_field = models.SettingField(key=key, value=value, entry_id=entry_id, order_index=index)
            db.add(new_field)

    for field_id, field_obj in existing_fields_map.items():
        if field_id not in processed_field_ids:
            db.delete(field_obj)

    db.commit()
    db.refresh(db_entry)
    return db_entry

def delete_setting_entry(db: Session, entry_id: int):
    db_entry = get_setting_entry(db, entry_id)
    if db_entry:
        db.delete(db_entry)
        db.commit()
    return db_entry

