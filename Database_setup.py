import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    # description = Column(String(200))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Items(Base):
    __tablename__ = 'items'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(200))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'category_id': self.category_id,
            'description': self.description,
        }


engine = create_engine('sqlite:///itemsdb.db')


Base.metadata.create_all(engine)
