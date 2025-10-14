from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Novel(Base):
    __tablename__ = "novels"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    setting_types = relationship("SettingType", back_populates="novel", cascade="all, delete-orphan", order_by="SettingType.order_index")
    setting_entries = relationship("SettingEntry", back_populates="novel", cascade="all, delete-orphan")

class SettingType(Base):
    __tablename__ = "setting_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    order_index = Column(Integer, nullable=False, default=0)

    novel = relationship("Novel", back_populates="setting_types")
    entries = relationship("SettingEntry", back_populates="setting_type", cascade="all, delete-orphan", order_by="SettingEntry.order_index")

class SettingEntry(Base):
    __tablename__ = "setting_entries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    setting_type_id = Column(Integer, ForeignKey("setting_types.id"))
    order_index = Column(Integer, nullable=False, default=0)

    novel = relationship("Novel", back_populates="setting_entries")
    setting_type = relationship("SettingType", back_populates="entries")
    fields = relationship("SettingField", back_populates="entry", cascade="all, delete-orphan", lazy="joined", order_by="SettingField.order_index")

class SettingField(Base):
    __tablename__ = "setting_fields"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    entry_id = Column(Integer, ForeignKey("setting_entries.id"))
    order_index = Column(Integer, nullable=False, default=0)

    entry = relationship("SettingEntry", back_populates="fields")

