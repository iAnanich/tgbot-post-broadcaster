from bot import dbadapter


class BotData:
    DB_SESSION = "db_session"
    DB_SESSION_MAKER = "db_session_maker"

    @classmethod
    def get_db_session(cls, bot_data: dict) -> dbadapter.Session:
        return bot_data[cls.DB_SESSION]

    @classmethod
    def get_db_session_maker(cls, bot_data: dict) -> dbadapter.sessionmaker:
        return bot_data[cls.DB_SESSION_MAKER]
