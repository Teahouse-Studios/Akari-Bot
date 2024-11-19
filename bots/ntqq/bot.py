import os
import re
import sys

import botpy
from botpy.message import C2CMessage, DirectMessage, GroupMessage, Message

from bots.ntqq.info import *
from bots.ntqq.message import MessageSession, FetchTarget
from core.bot_init import init_async, load_prompt
from core.builtins import PrivateAssets, Url
from core.config import config
from core.parser.message import parser
from core.constants.path import assets_path
from core.constants.info import Info
from core.types import MsgInfo, Session

PrivateAssets.set(os.path.join(assets_path, 'private', 'ntqq'))
Info.dirty_word_check = config('enable_dirty_check', False)
Url.disable_mm = False
qq_appid = str(config("qq_bot_appid", cfg_type=(int, str), table_name='bot_ntqq'))
qq_secret = config("qq_bot_secret", cfg_type=str, secret=True, table_name='bot_ntqq_secret')


class MyClient(botpy.Client):
    async def on_ready(self):
        await init_async()
        await load_prompt(FetchTarget)

    async def on_at_message_create(self, message: Message):
        message.content = re.sub(r'<@(.*?)>', '', message.content).strip()
        reply_id = None
        if message.message_reference:
            reply_id = message.message_reference.message_id
        prefix = None
        require_enable_modules = True
        msg = MessageSession(
            MsgInfo(
                target_id=f'{target_guild_prefix}|{message.guild_id}|{message.channel_id}',
                sender_id=f'{sender_tiny_prefix}|{message.author.id}',
                target_from=target_guild_prefix,
                sender_from=sender_prefix,
                sender_prefix=message.author.id[:6],
                client_name=client_name,
                message_id=message.id,
                reply_id=reply_id),
            Session(
                message=message,
                target=f'{message.guild_id}|{message.channel_id}',
                sender=message.author.id))
        if not message.content:
            message.content = '/help'
        if message.content.strip().startswith('/'):
            prefix = ['/']
            require_enable_modules = False
        await parser(msg, prefix=prefix, require_enable_modules=require_enable_modules)

    async def on_message_create(self, message: Message):
        reply_id = None
        if message.message_reference:
            reply_id = message.message_reference.message_id
        prefix = None
        require_enable_modules = True
        msg = MessageSession(
            MsgInfo(
                target_id=f'{target_guild_prefix}|{message.guild_id}|{message.channel_id}',
                sender_id=f'{sender_tiny_prefix}|{message.author.id}',
                target_from=target_guild_prefix,
                sender_from=sender_prefix,
                sender_prefix=message.author.id[:6],
                client_name=client_name,
                message_id=message.id,
                reply_id=reply_id),
            Session(
                message=message,
                target=f'{message.guild_id}|{message.channel_id}',
                sender=message.author.id))
        if message.content.strip().startswith('/'):
            prefix = ['/']
            require_enable_modules = False
        await parser(msg, prefix=prefix, require_enable_modules=require_enable_modules)

    async def on_group_at_message_create(self, message: GroupMessage):
        message.content = re.sub(r'<@(.*?)>', '', message.content).strip()
        reply_id = None
        if message.message_reference:
            reply_id = message.message_reference.message_id
        prefix = None
        require_enable_modules = True
        msg = MessageSession(
            MsgInfo(
                target_id=f'{target_group_prefix}|{message.group_openid}',
                sender_id=f'{sender_prefix}|{message.author.member_openid}',
                target_from=target_group_prefix,
                sender_from=sender_prefix,
                sender_prefix=message.author.member_openid[:6],
                client_name=client_name,
                message_id=message.id,
                reply_id=reply_id),
            Session(
                message=message,
                target=message.group_openid,
                sender=message.author.member_openid))
        if not message.content:
            message.content = '/help'
        if message.content.strip().startswith('/'):
            prefix = ['/']
            require_enable_modules = False
        await parser(msg, prefix=prefix, require_enable_modules=require_enable_modules)

    async def on_direct_message_create(self, message: DirectMessage):
        reply_id = None
        if message.message_reference:
            reply_id = message.message_reference.message_id
        prefix = None
        require_enable_modules = True
        msg = MessageSession(
            MsgInfo(
                target_id=f'{target_direct_prefix}|{message.guild_id}',
                sender_id=f'{sender_tiny_prefix}|{message.author.id}',
                target_from=target_direct_prefix,
                sender_from=sender_prefix,
                sender_prefix=message.author.id[:6],
                client_name=client_name,
                message_id=message.id,
                reply_id=reply_id),
            Session(
                message=message,
                target=message.guild_id,
                sender=message.author.id))
        if message.content.strip().startswith('/'):
            prefix = ['/']
            require_enable_modules = False
        await parser(msg, prefix=prefix, require_enable_modules=require_enable_modules)

    async def on_c2c_message_create(self, message: C2CMessage):
        reply_id = None
        if message.message_reference:
            reply_id = message.message_reference.message_id
        prefix = None
        require_enable_modules = True
        msg = MessageSession(
            MsgInfo(
                target_id=f'{target_c2c_prefix}|{message.author.user_openid}',
                sender_id=f'{sender_prefix}|{message.author.user_openid}',
                target_from=target_c2c_prefix,
                sender_from=sender_prefix,
                sender_prefix=message.author.user_openid[:6],
                client_name=client_name,
                message_id=message.id,
                reply_id=reply_id),
            Session(
                message=message,
                target=message.author.user_openid,
                sender=message.author.user_openid))
        if message.content.strip().startswith('/'):
            prefix = ['/']
            require_enable_modules = False
        await parser(msg, prefix=prefix, require_enable_modules=require_enable_modules)


if config("enable", False, cfg_type=bool, table_name='bot_ntqq'):
    intents = botpy.Intents.none()
    intents.public_guild_messages = True
    intents.public_messages = True
    intents.direct_message = True
    if config('qq_private_bot', False, table_name='bot_ntqq'):
        intents.guild_messages = True

    client = MyClient(intents=intents)

    Info.client_name = client_name
    if 'subprocess' in sys.argv:
        Info.subprocess = True

    client.run(appid=qq_appid, secret=qq_secret)