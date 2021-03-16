import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from . import dbadapter
from . import handlers
from . import settings
from .storage import BotData

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""

    filter_admins = Filters.user(username=settings.ADMIN_USERNAMES)
    filter_groups = Filters.chat_type.supergroup | Filters.chat_type.group
    filter_channel = Filters.chat_type.channel & Filters.sender_chat(settings.SOURCE_CHANNEL)
    filter_posts = filter_channel & Filters.regex(settings.POST_REGEX)

    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TGBOT_APIKEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    # ----
    dispatcher.add_handler(CommandHandler("help", handlers.command_help))
    dispatcher.add_handler(CommandHandler("debug", handlers.command_debug))
    # Private commands
    dispatcher.add_handler(CommandHandler("start", handlers.command_start, filters=Filters.chat_type.private))
    # ----
    # Group commands
    dispatcher.add_handler(
        CommandHandler(
            "start", handlers.command_start,
            filters=filter_admins & filter_groups,
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            "enable", handlers.command_enable,
            filters=filter_admins & filter_groups,
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            "disable", handlers.command_disable,
            filters=filter_admins & filter_groups,
        )
    )

    # Handle channel posts
    dispatcher.add_handler(
        MessageHandler(
            filters=filter_posts,
            callback=handlers.handler_broadcast_post,
        )
    )

    # Initialize DB
    session_maker = dbadapter.init_sessionmaker()
    dispatcher.bot_data[BotData.DB_SESSION_MAKER] = session_maker

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
