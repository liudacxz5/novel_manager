from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 导入在 database.py 中创建的 Base
from .database import Base

class Novel(Base):
    """小说模型"""
    __tablename__ = "novels"  # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    author = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 建立与 SettingEntry 的一对多关系
    settings = relationship("SettingEntry", back_populates="novel", cascade="all, delete-orphan")

class Category(Base):
    """设定分类模型"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)

    # 建立与 SettingEntry 的一对多关系
    settings = relationship("SettingEntry", back_populates="category")

class SettingEntry(Base):
    """设定条目模型"""
    __tablename__ = "setting_entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(200)) # 标签，用逗号分隔
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 外键，关联到 novels 表的 id
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    # 外键，关联到 categories 表的 id
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # 建立与 Novel 的多对一关系
    novel = relationship("Novel", back_populates="settings")
    # 建立与 Category 的多对一关系
    category = relationship("Category", back_populates="settings")
