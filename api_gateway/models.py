# Create models.py for the SQLAlchemy models to store requests and results.

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RequestData(Base):
    __tablename__ = 'request_data'

    id = Column(Integer, primary_key=True, index=True)
    request_hash = Column(String, index=True)
    status = Column(String, default="pending")

class Result(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True, index=True)
    request_hash = Column(String, index=True)
    result = Column(Text)