from sqlalchemy import Column, String

from database.orm import Session
from database.orm_base import Base

table_prefix = 'module_phigros_'
db = Session
session = db.session
engine = db.engine


class PgrBindInfo(Base):
    __tablename__ = table_prefix + 'PgrBindInfo'
    targetId = Column(String(512), primary_key=True)
    sessiontoken = Column(String(512))
    username = Column(String(512))


Session.create()
