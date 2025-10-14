from sqlalchemy.orm import Session
from . import models, schemas, auth
from typing import List, Dict

# --- User CRUD ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Novel CRUD ---
def get_novel(db: Session, novel_id: int, owner_id: int):
    return db.query(models.Novel).filter(models.Novel.id == novel_id, models.Novel.owner_id == owner_id).first()

def get_novels_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Novel).filter(models.Novel.owner_id == owner_id).order_by(models.Novel.title).offset(skip).limit(limit).all()

def create_novel(db: Session, novel: schemas.NovelCreate, owner_id: int):
    db_novel = models.Novel(**novel.model_dump(), owner_id=owner_id)
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel

def update_novel(db: Session, novel_id: int, novel_update: schemas.NovelUpdate, owner_id: int):
    db_novel = get_novel(db, novel_id, owner_id)
    if db_novel:
        update_data = novel_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_novel, key, value)
        db.commit()
        db.refresh(db_novel)
    return db_novel

def delete_novel(db: Session, novel_id: int, owner_id: int):
    db_novel = get_novel(db, novel_id, owner_id)
    if db_novel:
        db.delete(db_novel)
        db.commit()
    return db_novel

# --- Setting Type CRUD ---
def get_setting_type(db: Session, type_id: int):
    return db.query(models.SettingType).filter(models.SettingType.id == type_id).first()

def get_setting_type_by_name(db: Session, novel_id: int, name: str):
    return db.query(models.SettingType).filter_by(novel_id=novel_id, name=name).first()

def get_setting_types_by_novel(db: Session, novel_id: int):
    return db.query(models.SettingType).filter(models.SettingType.novel_id == novel_id).order_by(models.SettingType.order_index).all()

def create_setting_type(db: Session, setting_type: schemas.SettingTypeCreate, novel_id: int):
    max_order = db.query(models.SettingType).filter_by(novel_id=novel_id).count()
    db_type = models.SettingType(**setting_type.model_dump(), novel_id=novel_id, order_index=max_order)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def reorder_setting_types(db: Session, novel_id: int, type_ids: List[int]):
    for index, type_id in enumerate(type_ids):
        db.query(models.SettingType).filter_by(id=type_id, novel_id=novel_id).update({"order_index": index})
    db.commit()

# --- Setting Entry & Field CRUD ---
def get_setting_entry(db: Session, entry_id: int):
    return db.query(models.SettingEntry).filter(models.SettingEntry.id == entry_id).first()

def get_setting_entry_by_name_and_novel(db: Session, novel_id: int, entry_name: str):
    return db.query(models.SettingEntry).filter(
        models.SettingEntry.novel_id == novel_id,
        models.SettingEntry.name == entry_name
    ).first()

def get_setting_entry_by_name_and_type(db: Session, type_id: int, name: str):
    return db.query(models.SettingEntry).filter_by(setting_type_id=type_id, name=name).first()

def create_setting_entry(db: Session, entry: schemas.SettingEntryCreate, novel_id: int, type_id: int):
    max_order = db.query(models.SettingEntry).filter_by(setting_type_id=type_id).count()
    db_entry = models.SettingEntry(**entry.model_dump(), novel_id=novel_id, setting_type_id=type_id, order_index=max_order)
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
    submitted_field_ids = set()

    for i, field_data in enumerate(fields_data):
        field_id = field_data.get("id")
        key = field_data.get("key")
        value = field_data.get("value")

        if not key: continue

        if field_id and field_id in existing_fields_map:
            submitted_field_ids.add(field_id)
            field_to_update = existing_fields_map[field_id]
            field_to_update.key = key
            field_to_update.value = value
            field_to_update.order_index = i
        else:
            new_field = models.SettingField(key=key, value=value, entry_id=entry_id, order_index=i)
            db.add(new_field)

    for field_id, field_obj in existing_fields_map.items():
        if field_id not in submitted_field_ids:
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

def reorder_setting_entries(db: Session, type_id: int, entry_ids: List[int]):
    for index, entry_id in enumerate(entry_ids):
        db.query(models.SettingEntry).filter_by(id=entry_id, setting_type_id=type_id).update({"order_index": index})
    db.commit()

def create_setting_field(db: Session, key: str, value: str, entry_id: int):
    max_order = db.query(models.SettingField).filter_by(entry_id=entry_id).count()
    db_field = models.SettingField(key=key, value=value, entry_id=entry_id, order_index=max_order)
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field

