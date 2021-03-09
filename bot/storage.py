from bot import dbadapter


class BotData:
    DB_SESSION = 'db_session'

    @classmethod
    def get_db_session(cls, bot_data: dict) -> dbadapter.Session:
        return bot_data[cls.DB_SESSION]
