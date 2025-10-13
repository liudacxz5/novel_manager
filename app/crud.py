from sqlalchemy.orm import Session
from app import models, schemas


# Novel CRUD operations
def get_novel(db: Session, novel_id: int):
    return db.query(models.Novel).filter(models.Novel.id == novel_id).first()


def get_novels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Novel).offset(skip).limit(limit).all()


def create_novel(db: Session, novel: schemas.NovelCreate):
    db_novel = models.Novel(**novel.dict())
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel


def update_novel(db: Session, novel_id: int, novel: schemas.NovelUpdate):
    db_novel = db.query(models.Novel).filter(models.Novel.id == novel_id).first()
    if db_novel:
        update_data = novel.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_novel, key, value)
        db.commit()
        db.refresh(db_novel)
    return db_novel


def delete_novel(db: Session, novel_id: int):
    db_novel = db.query(models.Novel).filter(models.Novel.id == novel_id).first()
    if db_novel:
        db.delete(db_novel)
        db.commit()
    return db_novel


# Category CRUD operations
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# Setting Entry CRUD operations
def get_setting_entry(db: Session, entry_id: int):
    return db.query(models.SettingEntry).filter(models.SettingEntry.id == entry_id).first()


def get_setting_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SettingEntry).offset(skip).limit(limit).all()


def create_setting_entry(db: Session, entry: schemas.SettingEntryCreate):
    db_entry = models.SettingEntry(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry