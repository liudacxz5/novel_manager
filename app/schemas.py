from pydantic import BaseModel
from typing import Optional, List

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Field Schemas ---
class SettingFieldBase(BaseModel):
    key: str
    value: Optional[str] = None

class SettingFieldCreate(SettingFieldBase):
    pass

class SettingField(SettingFieldBase):
    id: int
    entry_id: int
    order_index: int
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
    order_index: int
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
    order_index: int
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
    owner_id: int
    setting_types: List[SettingType] = []
    class Config:
        from_attributes = True

