import os
import sys

from config import Config

if Config('db_path') is None:
    raise AttributeError('Wait! You need to fill a valid database address into the config.cfg "db_path" field\n'
                         'Example: \ndb_path = sqlite:///database/save.db\n'
                         '(Also you can fill in the above example directly,'
                         ' bot will automatically create a SQLite database in the "./database/save.db")')

from database import BotDBUtil, session
from database.tables import DBVersion

import asyncio
import traceback
import aioconsole

from bot import init_bot
from core.builtins import PrivateAssets, EnableDirtyWordCheck
from core.types import MsgInfo, AutoSession
from core.console.template import Template as MessageSession
from core.parser.message import parser
from core.utils.bot import init_async
from core.logger import Logger

query_dbver = session.query(DBVersion).first()
if query_dbver is None:
    session.add_all([DBVersion(value=str(BotDBUtil.database_version))])
    session.commit()
    query_dbver = session.query(DBVersion).first()

if (current_ver := int(query_dbver.value)) < (target_ver := BotDBUtil.database_version):
    print(f'Updating database from {current_ver} to {target_ver}...')
    from database.update import update_database

    update_database()
    print('Database updated successfully! Please restart the program.')
    sys.exit()

EnableDirtyWordCheck.status = True
PrivateAssets.set(os.path.abspath(os.path.dirname(__file__) + '/assets'))


async def console_scheduler():
    await init_async()


async def console_command():
    try:
        m = await aioconsole.ainput('> ')
        asyncio.create_task(console_command())
        await send_command(m)
    except KeyboardInterrupt:
        print('Exited.')
        exit()
    except Exception:
        Logger.error(traceback.format_exc())


async def send_command(msg, interactions=None):
    Logger.info('-------Start-------')
    returns = await parser(MessageSession(target=MsgInfo(targetId='TEST|Console|0',
                                                         senderId='TEST|0',
                                                         senderName='',
                                                         targetFrom='TEST|Console',
                                                         senderFrom='TEST', clientName='TEST', messageId=0,
                                                         replyId=None),
                                          session=AutoSession(message=msg, target='TEST|Console|0', sender='TEST|0',
                                                              auto_interactions=interactions)))
    # print(returns)
    Logger.info('----Process end----')
    return returns


if __name__ == '__main__':
    init_bot()
    loop = asyncio.get_event_loop()
    loop.create_task(console_scheduler())
    loop.create_task(console_command())
    loop.run_forever()
