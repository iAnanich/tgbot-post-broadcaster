import logging
from typing import Optional, Set, Iterable

from sqlalchemy import Column, Integer, BigInteger, Boolean, String, JSON, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from . import settings

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

# Init SQLAlchemy base for declarative models
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
    __tablename__ = "receivergroup"

    class Default:
        ENABLED = False

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    enabled = Column(Boolean, default=Default.ENABLED)
    title = Column(String(length=255), nullable=True)
    tags = Column(JSON, default=[])

    @property
    def is_enabled(self) -> bool:
        return self.enabled

    @property
    def is_disabled(self) -> bool:
        return not self.enabled

    @property
    def tags_set(self) -> Set[str]:
        return set(t.lower() for t in self.tags)

    @classmethod
    def get_by_chat_id(
        cls, chat_id: int, *, session: Session
    ) -> "ReceiverGroup" or None:
        try:
            return session.query(cls).filter(cls.chat_id == chat_id).first()
        except OperationalError as exc:
            return None

    @classmethod
    def get_or_create(
        cls, chat_id: int, title: str, *, session: Session
    ) -> "ReceiverGroup":
        obj = cls.get_by_chat_id(chat_id=chat_id, session=session)
        if obj is not None:
            return obj
        new_obj = cls(chat_id=chat_id, title=title)
        logger.info(
            f"Creating new {cls.__class__.__name__}#{new_obj.id} for chatID={chat_id}"
        )
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
            logger.info(f"Changing title of chatID={self.chat_id}")
            return True
        # if passed old value - do nothing
        return False

    def set_tags(self, tags: Iterable[str]) -> bool:
        if set(tags) != self.tags_set:
            sortable = list(tags)
            try:
                sortable.sort()
            except Exception as exc:
                logger.warning(f"Tags sorting failed due to error: {exc}")
            self.tags = sortable
            logger.info(f"Changing tags of chatID={self.chat_id}")
            return True
        # if passed old value - do nothing
        return False

    def add_tags(self, tags: Iterable[str]) -> bool:
        change_to = self.tags_set.union(set(tags))
        return self.set_tags(tags=change_to)

    def remove_tags(self, tags: Iterable[str]) -> bool:
        change_to = self.tags_set.difference(set(tags))
        return self.set_tags(tags=change_to)

    def update_tags(
        self, tags_to_add: Iterable[str], tags_to_remove: Iterable[str]
    ) -> bool:
        set_to = self.tags_set.union(set(tags_to_add)).difference(set(tags_to_remove))
        return self.set_tags(tags=set_to)

    def __repr__(self) -> str:
        return (
            f'<ReceiverGroup chat_id={self.chat_id} [{"x" if self.enabled else " "}]>'
        )

    def to_dict(self) -> dict:
        d = {
            "chat_id": self.chat_id,
            "enabled": self.enabled,
            "title": self.title,
            "tags": list(self.tags),
        }
        return d

    @classmethod
    def from_dict(cls, d: dict, *, session: Optional[Session]) -> "ReceiverGroup":
        obj = cls(
            chat_id=d["chat_id"],
            enabled=d.get("enabled", False),
            title=d.get("title", None),
            tags=d.get("tags", []),
        )
        if session:
            session.add(obj)
        return obj

    @classmethod
    def dump_all_to_serializable(cls, *, session: Session) -> [dict, ...]:
        return [obj.to_dict() for obj in session.query(cls).all()]

    @classmethod
    def load_from_serializable(
        cls, serializable: [dict, ...], *, session: Optional[Session]
    ) -> ["ReceiverGroup", ...]:
        return [cls.from_dict(obj_dict, session=session) for obj_dict in serializable]
