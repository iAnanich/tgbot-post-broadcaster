import logging
import time
from contextlib import contextmanager
from typing import Set, Iterable

import telegram
from telegram import Update, Message
from telegram.ext import CallbackContext

from . import settings, storage
from .dbadapter import ReceiverGroup

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

HELP = '''
Post Broadcaster Bot is dedicated to sharing posts from channels with multiple groups.

Add bot to group chat and use /start command.
Note: bot only obeys pre-defined admins.

Other commands:
/enable - enable broadcasting to this chat (disabled by default)
/disable - disable broadcasting to this chat
/status - display group chat status
/tags - modify tag subscriptions
/help - display this message
'''


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
        logger.debug(f'Command /start from {update.effective_chat.id} chat.')
        chat = update.effective_chat

        with db_session_from_context(context) as db_session:
            rg = ReceiverGroup.get_or_create(
                chat_id=chat.id,
                title=chat.title,
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
    logger.debug(f'Command /debug from {update.effective_chat.id} chat.')
    chat = update.effective_chat

    reply_md = (
        f'Chat ID: `{chat.id}`\n'
        f'Chat type: `{chat.type}`\n'
        f'Chat title: `{chat.title}`\n'
    )
    if chat.type in {chat.GROUP, chat.SUPERGROUP}:
        try:
            with db_session_from_context(context) as db_session:
                rg = ReceiverGroup.get_by_chat_id(
                    chat_id=chat.id,
                    session=db_session,
                )
                rg: ReceiverGroup
                is_enabled = rg.enabled
        except Exception as exc:
            reply_md += f'Could not retrieve group chat data.'
        else:
            if rg:
                reply_md += f'Broadcasting enabled: `{is_enabled}`\n'
            else:
                reply_md += f'No data for this group chat.'

    update.message.reply_markdown(reply_md)


def command_status(update: Update, context: CallbackContext) -> None:
    logger.debug(f'Command /status from {update.effective_chat.id} chat.')
    chat = update.effective_chat

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat.id,
            session=db_session,
        )
        rg: ReceiverGroup

        if not rg:
            reply_md = 'Use command /start to initialize the bot.'
        else:
            # Enabled/disabled
            if rg.enabled:
                reply_md = (
                    'Broadcasting to this group chat is enabled.\n'
                    'Use command /disable to disable it.\n'
                )
            else:
                reply_md = (
                    'Broadcasting to this group chat is disabled.\n'
                    'Use command /enable to enable it.\n'
                )

            # Tag subscriptions
            if rg.tags:
                reply_md += f'\nSubscribed to tags: ' + ' '.join(f'#{t}' for t in rg.tags) + '\n'
            else:
                reply_md += '\nNo active subscriptions.'
            reply_md += 'Use command /tags to manage tag subscriptions.'

            # update chat data
            if rg.update_title(title=chat.title):
                db_session.add(rg)

    update.message.reply_markdown(reply_md)


def command_enable(update: Update, context: CallbackContext) -> None:
    """Connect current group to channel via it's short name."""
    logger.debug(f'Command /enable from {update.effective_chat.id} chat.')
    chat = update.effective_chat

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat.id,
            session=db_session,
        )
        rg: ReceiverGroup
        if not rg:
            reply_msg = 'Use command /start first.'
        else:
            if rg.is_enabled:
                reply_msg = 'Broadcasting to this group chat already enabled.'
            else:
                rg.enable()
                db_session.add(rg)
                reply_msg = 'Broadcasting to this group chat successfully enabled.'

            # update chat data
            if rg.update_title(title=chat.title):
                db_session.add(rg)

    update.effective_message.reply_text(reply_msg)


def command_disable(update: Update, context: CallbackContext) -> None:
    """Disable broadcasting to current group from channel."""
    logger.debug(f'Command /disable from {update.effective_chat.id} chat.')
    chat = update.effective_chat

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat.id,
            session=db_session,
        )
        rg: ReceiverGroup
        if not rg:
            reply_msg = 'Use command /start first.'
        else:
            if rg.is_disabled:
                reply_msg = 'Broadcasting to this group chat already disabled.'
            else:
                rg.disable()
                db_session.add(rg)
                reply_msg = 'Broadcasting to this group chat successfully disabled.'

            # update chat data
            if rg.update_title(title=chat.title):
                db_session.add(rg)

    update.effective_message.reply_text(reply_msg)


def command_tags(update: Update, context: CallbackContext) -> None:
    """Manage group chat tags."""
    logger.debug(f'Command /tags from {update.effective_chat.id} chat.')
    chat = update.effective_chat

    with db_session_from_context(context) as db_session:
        rg = ReceiverGroup.get_by_chat_id(
            chat_id=chat.id,
            session=db_session,
        )
        rg: ReceiverGroup
        if not rg:
            reply_msg = 'Use command /start first.'
            update.effective_message.reply_text(reply_msg)
            return

        followup_reply_md = ''
        if context.args:
            tags_to_add = set(t[1:] for t in context.args if t.startswith('+'))
            not_allowed_tags = tags_to_add.difference(settings.ALL_TAGS)
            tags_to_remove = set(t[1:] for t in context.args if t.startswith('-'))

            tags_changed = rg.update_tags(
                tags_to_add=tags_to_add.intersection(settings.ALL_TAGS),
                tags_to_remove=tags_to_remove,
            )
            if tags_changed:
                db_session.add(rg)
                reply_md = 'Updated subscription tags to:\n'
                reply_md += '\n'.join(
                    f'{i + 1}) `{t}`' for i, t in enumerate(rg.tags)
                ) + '\n'
                if not_allowed_tags:
                    reply_md += 'These tags where provided, but are not allowed:\n'
                    reply_md += '`' + ' '.join(f'{t}' for t in not_allowed_tags) + '`'
            elif not_allowed_tags:
                reply_md = 'All provided tags are not allowed.'
            else:
                reply_md = 'No changes detected.'
        else:
            if rg.tags:
                reply_md = f'Active subscription tags:\n'
                reply_md += '\n'.join(
                    f'{i + 1}) `{t}`' for i, t in enumerate(rg.tags)
                ) + '\n'
            else:
                reply_md = 'No active subscription tags.\n'
            reply_md += '\n'
            reply_md += 'To change subscription tags, pass them to this ' + \
                        'command in the following format: `/tags +TagIWantToAdd -TagIWantToRemove`\n'
            reply_md += '\n'

            if rg.tags:
                followup_reply_md += 'List of other allowed tags:\n'
            else:
                followup_reply_md += 'List of all allowed tags:\n'
            other_tags = list(settings.ALL_TAGS.difference(rg.tags_set))
            other_tags.sort()
            followup_reply_md += '`' + ' '.join(
                f'{t}' for t in other_tags
            ) + '`'

        # update chat data
        if rg.update_title(title=chat.title):
            db_session.add(rg)

    reply = update.effective_message.reply_markdown(reply_md)
    if followup_reply_md and settings.DISPLAY_ALL_TAGS:
        reply.reply_markdown(followup_reply_md)


def _forward_post(receiver_group: ReceiverGroup, *, update: Update, context: CallbackContext):
    source_chat = update.effective_chat
    post = update.effective_message
    logger.debug(
        f'Preparing to forward message {source_chat.id}/{post.message_id} '
        f'to chat {receiver_group.chat_id} "{receiver_group.title}"'
    )
    try:
        context.bot.forward_message(
            chat_id=receiver_group.chat_id,
            from_chat_id=source_chat.id,
            message_id=post.message_id,
        )
    except telegram.error.BadRequest as bad_request:
        logger.warning(
            f'Attempt to forward message to chat {receiver_group.chat_id} failed due to '
            f'BadRequest error: {bad_request}'
        )
    except Exception as exc:
        logger.exception(f'Unhandled error during attempt ot forward message: {exc}')
    else:
        logger.info(
            f'Successfully forwarded post {post.link} to chat "{receiver_group.title}"'
        )


def _extract_hashtags(message: Message, allowed_hashtags: Set[str]) -> Iterable[str]:
    hashtag_entities = frozenset(filter(lambda e: e.type == 'hashtag', message.entities))

    for e in hashtag_entities:
        # telegram.messageentity.MessageEntity's offset field is for UTF-16 encoding.
        # Therefore, we need to apply offset in UTF-16 encoding. But the hashtag itself is OK for UTF-8.
        # Remove "#" char at the beginning of the entity
        hashtag = message.text.encode('utf-16')[2 * (e.offset + 1):2 * (e.offset + e.length + 1)].decode('utf-16')[1:]
        if hashtag not in allowed_hashtags:
            continue
        yield hashtag


def handler_broadcast_post(update: Update, context: CallbackContext) -> None:
    """Broadcast post from channel to connected groups."""
    post = update.effective_message
    logger.debug(f'Post #{post.message_id} in {update.effective_chat.id} channel.')

    forwards: int = 0

    extending_tags = frozenset(
        t.lower() for t in _extract_hashtags(
            message=post,
            allowed_hashtags=settings.POST_EXTENDING_TAGS,
        )
        )
    restrictive_tags = frozenset(
        t.lower() for t in _extract_hashtags(
            message=post,
            allowed_hashtags=settings.POST_RESTRICTIVE_TAGS,
        )
        )

    with db_session_from_context(context) as db_session:
        enabled_groups = list(db_session.query(ReceiverGroup).filter(ReceiverGroup.enabled == True))

        # update chat titles for later use
        if settings.AUTOUPDATE_CHAT_TITLES:
            for rg in enabled_groups:
                actual_title = context.bot.get_chat(rg.chat_id)
                if rg.update_title(actual_title):
                    db_session.add(rg)

        filtered_receiver_groups = (
            rg for rg in enabled_groups
            if restrictive_tags <= rg.tags_set and extending_tags & rg.tags_set
        )
        for rg in filtered_receiver_groups:
            if settings.SLOW_MODE:
                time.sleep(settings.SLOW_MODE_DELAY)

            forwards += 1
            _forward_post(receiver_group=rg, update=update, context=context)

    if forwards > 0:
        logger.info(f'Post #{post.message_id} from {update.effective_chat.id} channel forwarded into {forwards} chats.')
    else:
        logger.info(f'Received post #{post.message_id} from {update.effective_chat.id} channel was not forwarded anywhere!')
