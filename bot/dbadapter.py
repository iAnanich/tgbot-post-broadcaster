from typing import Optional

from sqlalchemy import Column, Integer, BigInteger, Boolean, String
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from . import settings

Base = declarative_base()


def create_all_tables(db_uri: Optional[str] = None) -> None:
    engine = create_engine(db_uri or settings.DB_URI)
    Base.metadata.create_all(engine)


def init_sessionmaker(db_uri: Optional[str] = None) -> sessionmaker:
    engine = create_engine(db_uri or settings.DB_URI)
    return sessionmaker(bind=engine)


def make_session(db_uri: Optional[str] = None) -> Session:
    engine = create_engine(db_uri or settings.DB_URI)
    return sessionmaker(bind=engine)()


class ReceiverGroup(Base):
    __tablename__ = 'receivergroup'

    class Default:
        ENABLED = False

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    enabled = Column(Boolean, default=Default.ENABLED)
    title = Column(String(length=255), nullable=True)

    @property
    def is_enabled(self) -> bool:
        return self.enabled

    @property
    def is_disabled(self) -> bool:
        return not self.enabled

    @classmethod
    def get_by_chat_id(cls, chat_id: int, *, session: Session) -> 'ReceiverGroup' or None:
        try:
            return session.query(cls).filter(cls.chat_id == chat_id).first()
        except OperationalError as exc:
            return None

    @classmethod
    def get_or_create(cls, chat_id: int, title: str,
                      *, session: Session) -> 'ReceiverGroup':
        obj = cls.get_by_chat_id(chat_id=chat_id, session=session)
        if obj is not None:
            return obj
        new_obj = cls(chat_id=chat_id, title=title)
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

    def update_title(self, title: str) -> bool:
        if title != self.title:
            self.title = title
            return True
        # if passed old value - do nothing
        return False

    def __repr__(self) -> str:
        return f'<ReceiverGroup chat_id={self.chat_id} [{"x" if self.enabled else " "}]>'

    def to_dict(self) -> dict:
        d = {
            'chat_id': self.chat_id,
            'enabled': self.enabled,
            'title': self.title,
        }
        return d

    @classmethod
    def from_dict(cls, d: dict, *, session: Optional[Session]) -> 'ReceiverGroup':
        obj = cls(
            chat_id=d['chat_id'],
            enabled=d.get('enabled', False),
            title=d.get('title', None),
        )
        if session:
            session.add(obj)
        return obj

    @classmethod
    def dump_all_to_serializable(cls, *, session: Session) -> [dict, ...]:
        return [obj.to_dict() for obj in session.query(cls).all()]

    @classmethod
    def load_from_serializable(cls, serializable: [dict, ...],
                               *, session: Optional[Session]) -> ['ReceiverGroup', ...]:
        return [cls.from_dict(obj_dict, session=session) for obj_dict in serializable]
