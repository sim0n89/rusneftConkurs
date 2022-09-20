from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, BigInteger
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
    tlg_id = Column(BigInteger)
    status = Column(String(20), nullable=True)
    def __repr__(self):
        return "<User ('%s', '%s')>" % (self.id, self.tlg_id)





class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_number = Column(String(50))
    u_id = Column(Integer, ForeignKey("users.id"))
    sum = Column(Integer, default=0)
    date_add = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "('%s', '%s','%s', '%s', '%s')" % (self.id, self.u_id, self.check_number, self.sum,self.date_add)

class Votes(Base):
    __tablename__='votes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_add = Column(DateTime, default=datetime.datetime.now())
    theme = Column(String(255))
    quest1 = Column(String(255))
    quest2 = Column(String(255))
    quest3 = Column(String(255))
    quest4= Column(String(255))
    quest5= Column(String(255))
    quest6= Column(String(255))
    quest7= Column(String(255))
    quest8= Column(String(255))
    quest9= Column(String(255))
    quest10= Column(String(255))


    def __repr__(self):
        return "('%s', '%s','%s', '%s', '%s', '%s','%s', '%s', '%s',  '%s', '%s')" % (self.id, self.theme, self.quest1, self.quest2, self.quest3, self.quest4, self.quest5, self.quest6, self.quest7, self.quest8, self.quest9)


class UserVote(Base):
    __tablename__ = 'userVote'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_add = Column(DateTime, default=datetime.datetime.now())
    tg_id = Column(BigInteger)
    chat_id = Column(String(50))
    message_id = Column(BigInteger)

    def __repr__(self):
        return "('%s', '%s','%s', '%s', '%s')" % (self.id, self.date_add, self.tg_id, self.chat_id, self.message_id)

class Winner(Base):
    __tablename__ = 'winners'
    id = Column(Integer, primary_key=True, autoincrement=True)
    u_id = Column(Integer, ForeignKey("users.id"))
    date_add = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Winner ('%s', '%s', '%s')>" % (self.id, self.u_id, self.date_add)

Base.metadata.create_all(engine)