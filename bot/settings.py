import os
from typing import FrozenSet, List

import environ


def parse_tags(tags_string: str) -> FrozenSet[str]:
    splitted: List[str] = tags_string.split(',')
    # remove empty items
    tags = (
        # TODO: deprecate support for #t1,#t2 format (# char)
        t[1:] if t.startswith('#') else t
        for t in splitted
        if t
    )
    # to lower
    tags = (t.lower() for t in tags)
    return frozenset(tags)


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

DISPLAY_ALL_TAGS = env.bool('TGBOT_DISPLAY_ALL_TAGS', default=False)

ADMIN_USERNAMES = env.str('TGBOT_ADMIN_USERNAMES').split(',')
SOURCE_CHANNEL = env.int('TGBOT_SOURCE_CHANNEL')
LOG_REPLIES = env.bool('TGBOT_LOG_REPLIES', default=False)

POST_EXTENDING_TAGS = parse_tags(env.str('TGBOT_POST_EXTENDING_TAGS', default=env.str('TGBOT_POST_TAGS', default='')))  # TODO: deprecate TGBOT_POST_TAGS
POST_RESTRICTIVE_TAGS = parse_tags(env.str('TGBOT_POST_RESTRICTIVE_TAGS', default=''))
ALL_TAGS = POST_EXTENDING_TAGS | POST_RESTRICTIVE_TAGS
