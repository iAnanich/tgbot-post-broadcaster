import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

env = environ.Env()
env.read_env(env_file=ENV_FILE)

LOG_LEVEL = env.str('LOG_LEVEL', default='INFO')

DB_URI = env.str('DB_URI', default='sqlite:///db.sqlite')

TGBOT_APIKEY = env.str('TGBOT_APIKEY')

SLOW_MODE = env.bool('TGBOT_SLOW_MODE', default=True)
SLOW_MODE_DELAY = env.float('TGBOT_SLOW_MODE_DELAY', default=0.1)

AUTOUPDATE_CHAT_TITLES = env.bool('TGBOT_AUTOUPDATE_CHAT_TITLES', default=False)

ADMIN_USERNAMES = env.str('TGBOT_ADMIN_USERNAMES').split(',')
SOURCE_CHANNEL = env.int('TGBOT_SOURCE_CHANNEL')

POST_REGEX = env.str('TGBOT_POST_REGEX') or ''
POST_TAGS = frozenset(
    t[1:] if t.startswith('#') else t
    for t in env.str('TGBOT_POST_TAGS', default='').split(',')
    if t
)
