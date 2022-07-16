from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import  declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from config import host, DB_USER, passwd, database, port
import datetime


conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(DB_USER, passwd, host, port, database)
engine = create_engine(conn)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tlg_id = Column(Integer)
    status = Column(String(20), nullable=True)
    def __repr__(self):
        return "<User ('%s', '%s')>" % (self.id, self.tlg_id)





class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_number = Column(String(50))
    u_id = Column(Integer, ForeignKey("users.id"))
    sum = Column(Float(20), default=0)
    date_add = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "('%s', '%s','%s', '%s', '%s')" % (self.id, self.u_id, self.check_number, self.sum,self.date_add)


class Winner(Base):
    __tablename__ = 'winners'
    id = Column(Integer, primary_key=True, autoincrement=True)
    u_id = Column(Integer, ForeignKey("users.id"))
    date_add = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Winner ('%s', '%s', '%s')>" % (self.id, self.u_id, self.date_add)

Base.metadata.create_all(engine)