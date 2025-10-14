from pydantic import BaseModel
from typing import Optional, List

# --- Field Schemas ---
class SettingFieldBase(BaseModel):
    key: str
    value: Optional[str] = None

class SettingFieldCreate(SettingFieldBase):
    pass

class SettingField(SettingFieldBase):
    id: int
    entry_id: int
    class Config:
        from_attributes = True

# --- Entry Schemas ---
class SettingEntryBase(BaseModel):
    name: str

class SettingEntryCreate(SettingEntryBase):
    pass

class SettingEntry(SettingEntryBase):
    id: int
    novel_id: int
    setting_type_id: int
    fields: List[SettingField] = []
    class Config:
        from_attributes = True

# --- Type Schemas ---
class SettingTypeBase(BaseModel):
    name: str

class SettingTypeCreate(SettingTypeBase):
    pass

class SettingType(SettingTypeBase):
    id: int
    novel_id: int
    entries: List[SettingEntry] = []
    class Config:
        from_attributes = True

# --- Novel Schemas ---
class NovelBase(BaseModel):
    title: str
    author: Optional[str] = None
    description: Optional[str] = None

class NovelCreate(NovelBase):
    pass

class NovelUpdate(NovelBase):
    pass

class Novel(NovelBase):
    id: int
    setting_types: List[SettingType] = []
    class Config:
        from_attributes = True

