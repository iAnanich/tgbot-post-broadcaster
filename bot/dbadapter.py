from sqlalchemy import Column, Integer, BigInteger, Boolean
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from . import settings

Base = declarative_base()


class ReceiverGroup(Base):
    __tablename__ = 'receivergroup'

    class Default:
        ENABLED = False

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    enabled = Column(Boolean, default=Default.ENABLED)

    @classmethod
    def get_by_chat_id(cls, chat_id: int, *, session: Session) -> 'ReceiverGroup' or None:
        try:
            return session.query(cls).filter(cls.chat_id == chat_id).first()
        except OperationalError as exc:
            return None

    @classmethod
    def get_or_create(cls, chat_id: int, *, session: Session) -> 'ReceiverGroup':
        obj = cls.get_by_chat_id(chat_id=chat_id, session=session)
        if obj is not None:
            return obj
        new_obj = cls(chat_id=chat_id)
        session.add(new_obj)
        return new_obj

    @classmethod
    def list_enabled_chat_ids(cls, *, session: Session) -> [int, ...]:
        query = session.query(cls.chat_id).filter(cls.enabled == True)
        return [chat_id for chat_id, in query]

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def __repr__(self) -> str:
        return f'<ReceiverGroup chat_id={self.chat_id} [{"x" if self.enabled else " "}]>'


def create_all_tables(uri: str = settings.DB_URI):
    engine = create_engine(uri)
    Base.metadata.create_all(engine)


def init_sessionmaker(uri: str = settings.DB_URI) -> sessionmaker:
    engine = create_engine(uri)
    return sessionmaker(bind=engine)


def make_session(uri: str = settings.DB_URI) -> Session:
    engine = create_engine(uri)
    return sessionmaker(bind=engine)()
