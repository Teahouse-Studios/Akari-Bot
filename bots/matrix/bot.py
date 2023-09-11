import asyncio
import os
import sys
from time import strftime

import nio

from bots.matrix import client
from bots.matrix.client import bot
from bots.matrix.info import client_name
from bots.matrix.message import MessageSession, FetchTarget
from core.builtins import PrivateAssets, Url
from core.logger import Logger
from core.parser.message import parser
from core.types import MsgInfo, Session
from core.utils.bot import load_prompt, init_async
from core.utils.info import Info

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
    if event.sender == client.user or event.prev_membership == event.membership:
        pass
    # is_direct = (room.member_count == 1 or room.member_count == 2) and room.join_rule == 'invite'
    # if not is_direct:
    #     resp = await bot.room_get_state_event(room.room_id, 'm.room.member', client.user)
    #     if 'prev_content' in resp.__dict__ and 'is_direct' in resp.__dict__[
    #             'prev_content'] and resp.__dict__['prev_content']['is_direct']:
    #         is_direct = True
    if room.member_count == 1 and event.membership == 'leave':
        resp = await bot.room_leave(room.room_id)
        if resp is nio.ErrorResponse:
            Logger.error(f"Error leaving empty room {room.room_id}: {str(resp)}")
        else:
            Logger.info(f"Left empty room {room.room_id}")


async def on_message(room: nio.MatrixRoom, event: nio.RoomMessageFormatted):
    if event.source['content']['msgtype'] == 'm.notice':
        # https://spec.matrix.org/v1.7/client-server-api/#mnotice
        return
    is_room = room.member_count != 2 or room.join_rule != 'invite'
    target_id = room.room_id if is_room else event.sender
    reply_id = None
    if 'm.relates_to' in event.source['content'] and 'm.in_reply_to' in event.source['content']['m.relates_to']:
        reply_id = event.source['content']['m.relates_to']['m.in_reply_to']['event_id']
    sender_name = (await bot.get_displayname(event.sender)).displayname

    msg = MessageSession(MsgInfo(target_id=f'Matrix|{target_id}',
                                 sender_id=f'Matrix|{event.sender}',
                                 target_from=f'Matrix',
                                 sender_from='Matrix',
                                 sender_name=sender_name,
                                 client_name=client_name,
                                 message_id=event.event_id,
                                 reply_id=reply_id),
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

    # E2EE setup
    if bot.olm:
        if bot.should_query_keys:
            Logger.info("querying matrix E2E encryption keys")
            await bot.keys_query()
        if bot.should_upload_keys:
            Logger.info("uploading matrix E2E encryption keys")
            await bot.keys_upload()
        megolm_backup_path = os.path.join(client.store_path_megolm_backup, f"restore.txt")
        if os.path.exists(megolm_backup_path):
            pass_path = os.path.join(client.store_path_megolm_backup, f"restore-passphrase.txt")
            assert os.path.exists(pass_path)
            Logger.info(f"importing megolm keys backup from {megolm_backup_path}")
            with open(pass_path) as f:
                passphrase = f.read()
            await bot.import_keys(megolm_backup_path, passphrase)
            Logger.info(f"megolm backup imported")

    await init_async()
    await load_prompt(FetchTarget)

    Logger.info(f"starting sync loop")
    await bot.sync_forever(timeout=30000, full_state=True, set_presence='online')
    Logger.info(f"sync loop stopped")

    if bot.olm:
        if client.megolm_backup_passphrase:
            backup_date = strftime('%Y-%m')
            backup_path = os.path.join(client.store_path_megolm_backup, f"akaribot-megolm-backup-{backup_date}.txt")
            old_backup_path = os.path.join(
                client.store_path_megolm_backup,
                f"akaribot-megolm-backup-{backup_date}-old.txt")
            if os.path.exists(backup_path):
                if os.path.exists(old_backup_path):
                    os.remove(old_backup_path)
                os.rename(backup_path, old_backup_path)
            Logger.info(f"saving megolm keys backup to {backup_path}")
            await bot.export_keys(backup_path, client.megolm_backup_passphrase)
            Logger.info(f"megolm backup exported")


if bot:
    if 'subprocess' in sys.argv:
        Info.subprocess = True
    asyncio.run(start())
