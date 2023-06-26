import json
import os
from typing import Optional

from telegram import Bot

from . import dbadapter
from . import settings


def dump_to_json(fn: str, db_uri: Optional[str] = None):
    db_session = dbadapter.make_session(db_uri=db_uri)
    serializable = {
        "ReceiverGroup": dbadapter.ReceiverGroup.dump_all_to_serializable(
            session=db_session
        ),
    }

    fp = os.path.join(settings.BASE_DIR, fn)
    json.dump(serializable, open(fp, "w"))


def load_from_json(fn: str, db_uri: Optional[str] = None):
    fp = os.path.join(settings.BASE_DIR, fn)
    serializable = json.load(open(fp))

    db_session = dbadapter.make_session(db_uri=db_uri)
    try:
        dbadapter.ReceiverGroup.load_from_serializable(
            serializable=serializable["ReceiverGroup"],
            session=db_session,
        )
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
    finally:
        db_session.close()


def update_group_titles(db_uri: Optional[str] = None):
    db_session = dbadapter.make_session(db_uri=db_uri)
    bot = Bot(settings.TGBOT_APIKEY)
    try:
        for rg in db_session.query(dbadapter.ReceiverGroup).all():
            rg: dbadapter.ReceiverGroup
            try:
                chat = bot.get_chat(rg.chat_id)
                rg.update_title(title=chat.title)
            except Exception as exc:
                pass
            else:
                db_session.add(rg)
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
    finally:
        db_session.close()
