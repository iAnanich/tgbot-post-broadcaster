import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

env = environ.Env()
env.read_env(env_file=ENV_FILE)

LOG_LEVEL = env.str('LOG_LEVEL', default='INFO')

TGBOT_APIKEY = env.str('TGBOT_APIKEY')

ADMIN_USERNAMES = env.str('TGBOT_ADMIN_USERNAMES').split(',')

DB_URI = env.str('DB_URI', default='sqlite:///db.sqlite')
