import asyncio
import os
from tracemalloc import start
from bots.matrix import client

from bots.matrix.client import bot
import nio

from core.builtins import PrivateAssets, Url
from core.logger import Logger
from core.parser.message import parser
from core.types import MsgInfo, Session
from core.utils.bot import load_prompt, init_async
from bots.matrix.message import MessageSession, FetchTarget

PrivateAssets.set(os.path.abspath(os.path.dirname(__file__) + "/assets"))
Url.disable_mm = True


async def on_sync(resp: nio.SyncResponse):
    with open(client.store_path_next_batch, 'w') as fp:
        fp.write(resp.next_batch)


async def on_invite(room: nio.MatrixRoom, event: nio.InviteEvent):
    Logger.info(f"Received room invitation for {room.room_id} ({room.name}) from {event.sender}")
    await bot.join(room.room_id)
    Logger.info(f"Joined room {room.room_id}")


async def on_room_member(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    Logger.info(f"Received m.room.member, {event.sender} : {event.prev_membership} -> {event.membership}")
    if event.sender == client.user:
        pass
    isDirect = (room.member_count == 1 or room.member_count == 2) and room.join_rule == 'invite'
    if not isDirect:
        resp = await bot.room_get_state_event(room.room_id, 'm.room.member', client.user)
        if 'prev_content' in resp.__dict__ and 'is_direct' in resp.__dict__[
                'prev_content'] and resp.__dict__['prev_content']['is_direct']:
            isDirect = True
    if isDirect and room.member_count == 1 and event.membership == 'leave':
        resp = await bot.room_leave(room.room_id)
        if resp is nio.ErrorResponse:
            Logger.error(f"Error leaving empty room {room.room_id}: {str(resp)}")
        else:
            Logger.info(f"Left empty room {room.room_id}")


async def on_message(room: nio.MatrixRoom, event: nio.RoomMessageFormatted):
    if event.source['content']['msgtype'] == 'm.notice':
        # https://spec.matrix.org/v1.7/client-server-api/#mnotice
        return
    isRoom = room.member_count != 2 or room.join_rule != 'invite'
    targetId = room.room_id if isRoom else event.sender
    replyId = None
    if 'm.relates_to' in event.source['content'] and 'm.in_reply_to' in event.source['content']['m.relates_to']:
        replyId = event.source['content']['m.relates_to']['m.in_reply_to']['event_id']
    senderName = (await bot.get_displayname(event.sender)).displayname

    msg = MessageSession(MsgInfo(targetId=f'Matrix|{targetId}',
                                 senderId=f'Matrix|{event.sender}',
                                 targetFrom=f'Matrix',
                                 senderFrom='Matrix',
                                 senderName=senderName,
                                 clientName='Matrix',
                                 messageId=event.event_id,
                                 replyId=replyId),
                         Session(message=event.source, target=room.room_id, sender=event.sender))
    asyncio.create_task(parser(msg))


async def start():
    # Logger.info(f"trying first sync")
    # sync = await bot.sync()
    # Logger.info(f"first sync finished in {sync.elapsed}ms, dropped older messages")
    # if sync is nio.SyncError:
    #     Logger.error(f"failed in first sync: {sync.status_code} - {sync.message}")
    try:
        with open(client.store_path_next_batch, 'r') as fp:
            bot.next_batch = fp.read()
            Logger.info(f"loaded next sync batch from storage: {bot.next_batch}")
    except FileNotFoundError:
        bot.next_batch = 0

    bot.add_response_callback(on_sync, nio.SyncResponse)
    bot.add_event_callback(on_invite, nio.InviteEvent)
    bot.add_event_callback(on_room_member, nio.RoomMemberEvent)
    bot.add_event_callback(on_message, nio.RoomMessageFormatted)

    await init_async()
    await load_prompt(FetchTarget)

    Logger.info(f"starting sync loop")
    await bot.sync_forever(timeout=30000, full_state=True, set_presence='online')
    Logger.error(f"sync loop stopped")

if bot:
    asyncio.run(start())
