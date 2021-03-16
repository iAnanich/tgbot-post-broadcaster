import logging
from contextlib import contextmanager

import telegram
from telegram import Update
from telegram.ext import CallbackContext

from . import settings
from . import storage
from .dbadapter import ReceiverGroup

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

# TODO
HELP = '''Post Broadcaster Bot is dedicated to sharing posts from channels with multiple groups.
Add bot to group chat and use /start command.'''


@contextmanager
def db_session_from_context(context: CallbackContext):
    """Provide a transactional scope around a series of operations."""
    session = storage.BotData.get_db_session_maker(context.bot_data)()
    try:
        yield session
        session.commit()
    except Exception as exc:
        logger.exception(f'Unexpected error in attempt to commit session: ')
        session.rollback()
        raise
    finally:
        session.close()


# Bot commands
# ============

def command_start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    if update.effective_chat.type == update.effective_chat.PRIVATE:
        update.message.reply_text(HELP)
    elif update.effective_chat.type in {update.effective_chat.GROUP, update.effective_chat.SUPERGROUP}:
        logger.debug(f'Command /start in {update.effective_chat.id} group.')
        chat_id = update.effective_chat.id

        with db_session_from_context(context) as db_session:
            rg = ReceiverGroup.get_or_create(
                chat_id=chat_id,
                session=db_session,
            )
            if rg.enabled:
                reply_msg = 'Post broadcasting already enabled.'
            else:
                reply_msg = (
                    'Greetings!\n'
                    'Use command /enable to enable post broadcasting to this group chat.'
                )

        update.message.reply_text(reply_msg)


def command_help(update: Update, context: CallbackContext) -> None:
    """Help user understand the bot."""
    update.message.reply_text(HELP)


def command_debug(update: Update, context: CallbackContext) -> None:
    """Display debug info."""
    text = (
        f'Chat ID: {update.effective_chat.id}'
        f'Chat type: {update.effective_chat.type}'
        f'Chat title: {update.effective_chat.title}'
    )
    update.message.reply_text(text)


def command_enable(update: Update, context: CallbackContext) -> None:
    """Connect current group to channel via it's short name."""
    logger.debug(f'Command /enable in {update.effective_chat.id} group.')
    chat_id = update.effective_chat.id

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat_id,
            session=db_session,
        )
        rg: ReceiverGroup
        if not rg:
            # This must not happen
            logger.warning(f'Someone managed to successfully call /enable before /start')
            reply_msg = 'Use command /start first.'
        elif rg.is_enabled:
            reply_msg = 'Broadcasting to this group chat already enabled.'
        else:
            rg.enable()
            db_session.add(rg)
            reply_msg = 'Broadcasting to this group chat successfully enabled.'

    update.effective_message.reply_text(reply_msg)


def command_disable(update: Update, context: CallbackContext) -> None:
    """Disable broadcasting to current group from channel."""
    logger.debug(f'Command /disable in {update.effective_chat.id} group.')
    chat_id = update.effective_chat.id

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat_id,
            session=db_session,
        )
        rg: ReceiverGroup
        if not rg:
            # This must not happen
            logger.warning(f'Someone managed to successfully call /disable before /start')
            reply_msg = 'Use command /start first.'
        elif rg.is_disabled:
            reply_msg = 'Broadcasting to this group chat already disabled.'
        else:
            rg.disable()
            db_session.add(rg)
            reply_msg = 'Broadcasting to this group chat successfully disabled.'

    update.effective_message.reply_text(reply_msg)


def handler_broadcast_post(update: Update, context: CallbackContext) -> None:
    """Broadcast post from channel to connected groups."""
    logger.debug(f'Post in {update.effective_chat.id} channel.')
    chat_id = update.effective_chat.id
    post_id = update.effective_message.message_id

    with db_session_from_context(context) as db_session:
        groups_broadcast_to = ReceiverGroup.list_enabled_chat_ids(session=db_session)

    logger.debug(
        f'Broadcasting post {post_id} '
        f'to {len(groups_broadcast_to)} group chats.'
    )
    for group_id in groups_broadcast_to:
        try:
            context.bot.forward_message(
                chat_id=group_id,
                from_chat_id=chat_id,
                message_id=post_id,
            )
        except telegram.error.BadRequest as bad_request:
            logger.warning(
                f'Attempt to forward message to {group_id} failed due to '
                f'BadRequest error: {bad_request}'
            )
        except Exception as exc:
            logger.exception(f'Unhandled error during attempt ot forward message:')
        else:
            logger.debug(
                f'Successfully forwarded message {post_id}'
                f' to chat {group_id}'
            )
