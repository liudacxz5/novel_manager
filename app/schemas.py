from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Novel schemas
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
    created_at: datetime

    class Config:
        from_attributes = True


# Category schemas
class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Setting Entry schemas
class SettingEntryBase(BaseModel):
    novel_id: int
    category_id: int
    title: str
    content: str
    tags: Optional[str] = None


class SettingEntryCreate(SettingEntryBase):
    pass


class SettingEntryUpdate(SettingEntryBase):
    pass


class SettingEntry(SettingEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True