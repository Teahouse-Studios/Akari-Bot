import html
import logging
import os
import re
import sys

import orjson as json
from aiocqhttp import Event

from bots.aiocqhttp.client import bot
from bots.aiocqhttp.info import *
from bots.aiocqhttp.message import MessageSession, FetchTarget
from core.config import Config
from core.bot import load_prompt, init_async
from core.builtins import EnableDirtyWordCheck, PrivateAssets, Url
from core.parser.message import parser
from core.path import assets_path
from core.tos import tos_report
from core.types import MsgInfo, Session
from core.utils.i18n import Locale, default_locale
from core.utils.info import Info
from core.database import BotDBUtil

PrivateAssets.set(os.path.join(assets_path, 'private', 'aiocqhttp'))
EnableDirtyWordCheck.status = Config('enable_dirty_check', False)
Url.disable_mm = not Config('enable_urlmanager', False)
qq_account = str(Config("qq_account", cfg_type=(int, str)))
enable_listening_self_message = Config("qq_enable_listening_self_message", False)


@bot.on_startup
async def startup():
    await init_async()
    bot.logger.setLevel(logging.WARNING)


@bot.on_websocket_connection
async def _(event: Event):
    await load_prompt(FetchTarget)


ignore_ids = [2854196310]  # Q群管家


async def message_handler(event: Event):
    if event.detail_type == 'private':
        if event.sub_type == 'group':
            if Config('qq_disable_temp_session', True):
                return await bot.send(event, Locale(default_locale).t('qq.prompt.disable_temp_session'))
    if event.user_id in ignore_ids:
        return
    string_post = False
    if isinstance(event.message, str):
        string_post = True

    if string_post:
        match_json = re.match(r'\[CQ:json,data=(.*?)\]', event.message, re.MULTILINE | re.DOTALL)
        if match_json:
            load_json = json.loads(html.unescape(match_json.group(1)))
            if load_json['app'] == 'com.tencent.multimsg':
                event.message = f'[CQ:forward,id={load_json["meta"]["detail"]["resid"]}]'
    else:
        if event.message[0]["type"] == "json":
            load_json = json.loads(event.message[0]["data"]["data"])
            if load_json['app'] == 'com.tencent.multimsg':
                event.message = [{"type": "forward", "data": {"id": f"{load_json["meta"]["detail"]["resid"]}"}}]

    reply_id = None
    if string_post:
        match_reply = re.match(r'^\[CQ:reply,id=(-?\d+).*\].*', event.message)
        if match_reply:
            reply_id = int(match_reply.group(1))
    else:
        if event.message[0]["type"] == "reply":
            reply_id = int(event.message[0]["data"]["id"])

    prefix = None
    if string_post:
        if match_at := re.match(r'^\[CQ:at,qq=(\d+).*\](.*)', event.message):
            if match_at.group(1) == qq_account:
                event.message = match_at.group(2)
                if event.message in ['', ' ']:
                    event.message = 'help'
                prefix = ['']
    else:
        if event.message[0]["type"] == "at":
            if event.message[0]["data"]["qq"] == qq_account:
                event.message = event.message[1:]
                if not event.message:
                    event.message = [{"type": "text", "data": {"text": "help"}}]
                prefix = ['']

    target_id = f'{target_group_name}|{
        event.group_id}' if event.detail_type == 'group' else f'{target_private_name}|{
        event.user_id}'

    msg = MessageSession(MsgInfo(target_id=target_id,
                                 sender_id=f'{sender_name}|{event.user_id}',
                                 target_from=target_group_name if event.detail_type == 'group' else target_private_name,
                                 sender_from=sender_name,
                                 sender_name=event.sender['nickname'],
                                 client_name=client_name,
                                 message_id=event.message_id,
                                 reply_id=reply_id),
                         Session(message=event,
                                 target=event.group_id if event.detail_type == 'group' else event.user_id,
                                 sender=event.user_id))
    await parser(msg, running_mention=True, prefix=prefix)


if enable_listening_self_message:
    @bot.on('message_sent')
    async def _(event: Event):
        await message_handler(event)


@bot.on_message('group', 'private')
async def _(event: Event):
    await message_handler(event)


class GuildAccountInfo:
    tiny_id = None


@bot.on_message('guild')
async def _(event):
    if not GuildAccountInfo.tiny_id:
        profile = await bot.call_action('get_guild_service_profile')
        GuildAccountInfo.tiny_id = profile['tiny_id']
    tiny_id = event.user_id
    if tiny_id == GuildAccountInfo.tiny_id:
        return
    reply_id = None
    match_reply = re.match(r'^\[CQ:reply,id=(-?\d+).*\].*', event.message)
    if match_reply:
        reply_id = int(match_reply.group(1))
    msg = MessageSession(MsgInfo(target_id=f'{target_guild_name}|{event.guild_id}|{event.channel_id}',
                                 sender_id=f'{sender_tiny_name}|{event.user_id}',
                                 target_from=target_guild_name,
                                 sender_from=sender_tiny_name,
                                 sender_name=event.sender['nickname'],
                                 client_name=client_name,
                                 message_id=event.message_id,
                                 reply_id=reply_id),
                         Session(message=event,
                                 target=f'{event.guild_id}|{event.channel_id}',
                                 sender=event.user_id))
    await parser(msg, running_mention=True)


@bot.on('request.friend')
async def _(event: Event):
    sender_info = BotDBUtil.SenderInfo(f'{sender_name}|{event.user_id}')
    if sender_info.is_super_user or sender_info.is_in_allow_list:
        return {'approve': True}
    if not Config('qq_allow_approve_friend', False):
        await bot.send_private_msg(user_id=event.user_id,
                                   message=Locale(default_locale).t('qq.prompt.disable_friend_request'))
    else:
        if sender_info.is_in_block_list:
            return {'approve': False}
        return {'approve': True}


@bot.on('request.group.invite')
async def _(event: Event):
    sender_info = BotDBUtil.SenderInfo(f'{sender_name}|{event.user_id}')
    if sender_info.is_super_user or sender_info.is_in_allow_list:
        return {'approve': True}
    if not Config('qq_allow_approve_group_invite', False):
        await bot.send_private_msg(user_id=event.user_id,
                                   message=Locale(default_locale).t('qq.prompt.disable_group_invite'))
    else:
        if BotDBUtil.GroupBlockList.check(f'{target_group_name}|{event.group_id}'):
            return {'approve': False}
        return {'approve': True}


@bot.on_notice('group_ban')
async def _(event: Event):
    if event.user_id == int(qq_account):
        unfriendly_actions = BotDBUtil.UnfriendlyActions(target_id=event.group_id,
                                                         sender_id=event.operator_id)
        sender_info = BotDBUtil.SenderInfo(f'{sender_name}|{str(event.operator_id)}')
        unfriendly_actions.add('mute', str(event.duration))
        result = unfriendly_actions.check_mute()
        if event.duration >= 259200:
            result = True
        if result and not sender_info.is_super_user:
            reason = Locale(default_locale).t('tos.message.reason.mute')
            await tos_report(f'{sender_name}|{event.operator_id}', f'{target_group_name}|{event.group_id}', reason, banned=True)
            BotDBUtil.GroupBlockList.add(f'{target_group_name}|{event.group_id}')
            await bot.call_action('set_group_leave', group_id=event.group_id)
            sender_info.edit('isInAllowList', False)
            sender_info.edit('isInBlockList', True)
            await bot.call_action('delete_friend', friend_id=event.operator_id)


@bot.on_notice('group_decrease')
async def _(event: Event):
    if event.sub_type == 'kick_me':
        BotDBUtil.UnfriendlyActions(target_id=event.group_id, sender_id=event.operator_id).add('kick')
        sender_info = BotDBUtil.SenderInfo(f'{sender_name}|{event.operator_id}')
        if not sender_info.is_super_user:
            reason = Locale(default_locale).t('tos.message.reason.kick')
            await tos_report(f'{sender_name}|{event.operator_id}', f'{target_group_name}|{event.group_id}', reason, banned=True)
            BotDBUtil.GroupBlockList.add(f'{target_group_name}|{event.group_id}')
            sender_info.edit('isInAllowList', False)
            sender_info.edit('isInBlockList', True)
            await bot.call_action('delete_friend', friend_id=event.operator_id)


@bot.on_message('group')
async def _(event: Event):
    result = BotDBUtil.GroupBlockList.check(f'{target_group_name}|{event.group_id}')
    if result:
        res = Locale(default_locale).t('tos.message.in_group_blocklist')
        if Config('issue_url', cfg_type=str):
            res += '\n' + Locale(default_locale).t('tos.message.appeal', issue_url=Config('issue_url', cfg_type=str))
        await bot.send(event=event, message=res)
        await bot.call_action('set_group_leave', group_id=event.group_id)


qq_host = Config("qq_host", cfg_type=str)
if qq_host:
    argv = sys.argv
    Info.client_name = client_name
    if 'subprocess' in sys.argv:
        Info.subprocess = True
    host, port = qq_host.split(':')
    bot.run(host=host, port=port, debug=False)
