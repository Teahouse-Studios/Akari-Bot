import os
import platform
import jwt
import psutil
import time

from config import Config
from core.builtins import Bot, command_prefix, PrivateAssets
from core.component import module
from core.utils.i18n import get_available_locales, Locale, load_locale_file
from cpuinfo import get_cpu_info
from database import BotDBUtil
from datetime import datetime, timedelta

jwt_secret = Config('jwt_secret')

version = module('version', base=True, desc='{core.help.version}', developers=['OasisAkari', 'Dianliang233'])


@version.handle()
async def bot_version(msg: Bot.MessageSession):

    ver = os.path.abspath(PrivateAssets.path + '/version')
    tag = os.path.abspath(PrivateAssets.path + '/version_tag')
    open_version = open(ver, 'r')
    open_tag = open(tag, 'r')
    msgs = msg.locale.t('core.message.version', version_tag=open_tag.read(), commit=open_version.read())
    open_version.close()
    await msg.finish(msgs, msgs)


ping = module('ping', base=True, desc='{core.help.ping}', developers=['OasisAkari'])

started_time = datetime.now()


@ping.handle()
async def _(msg: Bot.MessageSession):
    checkpermisson = msg.checkSuperUser()
    result = "Pong!"
    if checkpermisson:
        timediff = str(datetime.now() - started_time)
        Boot_Start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time()))
        Cpu_usage = psutil.cpu_percent()
        RAM = int(psutil.virtual_memory().total / (1024 * 1024))
        RAM_percent = psutil.virtual_memory().percent
        Swap = int(psutil.swap_memory().total / (1024 * 1024))
        Swap_percent = psutil.swap_memory().percent
        Disk = int(psutil.disk_usage('/').used / (1024 * 1024 * 1024))
        DiskTotal = int(psutil.disk_usage('/').total / (1024 * 1024 * 1024))
        """
        try:
            GroupList = len(await app.groupList())
        except Exception:
            GroupList = msg.locale.t('core.message.ping.failed')
        try:
            FriendList = len(await app.friendList())
        except Exception:
            FriendList = msg.locale.t('core.message.ping.failed')
        """
        result += '\n' + msg.locale.t("core.message.ping.detail",
                                      system_boot_time=Boot_Start,
                                      bot_running_time=timediff,
                                      python_version=platform.python_version(),
                                      cpu_brand=get_cpu_info()['brand_raw'],
                                      cpu_usage=Cpu_usage,
                                      ram=RAM,
                                      ram_percent=RAM_percent,
                                      swap=Swap,
                                      swap_percent=Swap_percent,
                                      disk_space=Disk,
                                      disk_space_total=DiskTotal)
    await msg.finish(result)


admin = module('admin',
               base=True,
               required_admin=True,
               developers=['OasisAkari'],
               desc='{core.help.admin}'
               )


@admin.handle([
    'add <UserID> {{core.help.admin.add}}',
    'del <UserID> {{core.help.admin.del}}',
    'list {{core.help.admin.list}}'])
async def config_gu(msg: Bot.MessageSession):
    if 'list' in msg.parsed_msg:
        if msg.custom_admins:
            await msg.finish(msg.locale.t("core.message.admin.list") + '\n'.join(msg.custom_admins))
        else:
            await msg.finish(msg.locale.t("core.message.admin.list.none"))
    user = msg.parsed_msg['<UserID>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t('core.message.admin.invalid', target=msg.target.senderFrom))
    if 'add' in msg.parsed_msg:
        if user and user not in msg.custom_admins:
            if msg.data.add_custom_admin(user):
                await msg.finish(msg.locale.t('success'))
        else:
            await msg.finish(msg.locale.t("core.message.admin.already"))
    if 'del' in msg.parsed_msg:
        if user:
            if msg.data.remove_custom_admin(user):
                await msg.finish(msg.locale.t('success'))


@admin.handle('ban <UserID> {{core.help.admin.ban}}', 'unban <UserID> {{core.help.admin.unban}}')
async def config_ban(msg: Bot.MessageSession):
    user = msg.parsed_msg['<UserID>']
    if not user.startswith(f'{msg.target.senderFrom}|'):
        await msg.finish(msg.locale.t('core.message.admin.invalid', target=msg.target.senderFrom))
    if user == msg.target.senderId:
        await msg.finish(msg.locale.t("core.message.admin.ban.self"))
    if 'ban' in msg.parsed_msg:
        if user not in msg.options.get('ban', []):
            msg.data.edit_option('ban', msg.options.get('ban', []) + [user])
            await msg.finish(msg.locale.t('success'))
        else:
            await msg.finish(msg.locale.t("core.message.admin.ban.already"))
    if 'unban' in msg.parsed_msg:
        if user in (banlist := msg.options.get('ban', [])):
            banlist.remove(user)
            msg.data.edit_option('ban', banlist)
            await msg.finish(msg.locale.t('success'))
        else:
            await msg.finish(msg.locale.t("core.message.admin.ban.not_yet"))


locale = module('locale', base=True, developers=['Dianliang233', 'Light-Beacon'])


@locale.handle('{{core.help.locale}}')
async def _(msg: Bot.MessageSession):
    lang = msg.locale.t("language")
    avaliable_lang = msg.locale.t("message.delimiter").join(get_available_locales())
    await msg.finish(f"{msg.locale.t('core.message.locale')}{msg.locale.t('language')}\n{msg.locale.t('core.message.locale.set.prompt', langlist=avaliable_lang, prefix=command_prefix[0])}")


@locale.handle('<lang> {{core.help.locale.set}}', required_admin=True)
async def config_gu(msg: Bot.MessageSession):
    lang = msg.parsed_msg['<lang>']
    if lang in get_available_locales():
        if BotDBUtil.TargetInfo(msg.target.targetId).edit('locale', lang):
            await msg.finish(Locale(lang).t('success'))
    else:
        avaliable_lang = msg.locale.t("message.delimiter").join(get_available_locales())
        await msg.finish(msg.locale.t("core.message.locale.set.invalid", langlist=avaliable_lang))


@locale.handle('reload {{core.help.locale.reload}}', required_superuser=True)
async def reload_locale(msg: Bot.MessageSession):
    err = load_locale_file()
    if len(err) == 0:
        await msg.finish(msg.locale.t("success"))
    else:
        await msg.finish(msg.locale.t("core.message.locale.reload.failed", detail='\n'.join(err)))


whoami = module('whoami', developers=['Dianliang233'], base=True)


@whoami.handle('{{core.help.whoami}}')
async def _(msg: Bot.MessageSession):
    rights = ''
    if await msg.checkNativePermission():
        rights += '\n' + msg.locale.t("core.message.whoami.admin")
    elif await msg.checkPermission():
        rights += '\n' + msg.locale.t("core.message.whoami.botadmin")
    if msg.checkSuperUser():
        rights += '\n' + msg.locale.t("core.message.whoami.superuser")
    await msg.finish(msg.locale.t('core.message.whoami', senderid=msg.target.senderId, targetid=msg.target.targetId) + rights,
                     disable_secret_check=True)


tog = module('toggle', developers=['OasisAkari'], base=True, required_admin=True)


@tog.handle('typing {{core.help.toggle.typing}}')
async def _(msg: Bot.MessageSession):
    target = BotDBUtil.SenderInfo(msg.target.senderId)
    state = target.query.disable_typing
    if not state:
        target.edit('disable_typing', True)
        await msg.finish(msg.locale.t('core.message.toggle.typing.disable'))
    else:
        target.edit('disable_typing', False)
        await msg.finish(msg.locale.t('core.message.toggle.typing.enable'))


@tog.handle('check {{core.help.toggle.check}}')
async def _(msg: Bot.MessageSession):
    state = msg.options.get('typo_check')
    if state:
        msg.data.edit_option('typo_check', False)
        await msg.finish(msg.locale.t('core.message.toggle.check.enable'))
    else:
        msg.data.edit_option('typo_check', True)
        await msg.finish(msg.locale.t('core.message.toggle.check.disable'))


mute = module('mute', developers=['Dianliang233'], base=True, required_admin=True,
              desc='{core.help.mute}')


@mute.handle()
async def _(msg: Bot.MessageSession):
    state = msg.data.switch_mute()
    if state:
        await msg.finish(msg.locale.t('core.message.mute.enable'))
    else:
        await msg.finish(msg.locale.t('core.message.mute.disable'))


leave = module(
    'leave',
    developers=['OasisAkari'],
    base=True,
    required_admin=True,
    available_for='QQ|Group',
    alias='dismiss',
    desc='{core.help.leave}')


@leave.handle()
async def _(msg: Bot.MessageSession):
    confirm = await msg.waitConfirm(msg.locale.t('core.message.leave.confirm'))
    if confirm:
        await msg.sendMessage(msg.locale.t('core.message.leave.success'))
        await msg.call_api('set_group_leave', group_id=msg.session.target)


token = module('token', base=True, desc='{core.help.token}', developers=['Dianliang233'])


@token.handle('<code>')
async def _(msg: Bot.MessageSession):
    await msg.finish(jwt.encode({
        'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24 * 7),  # 7 days
        'iat': datetime.utcnow(),
        'senderId': msg.target.senderId,
        'code': msg.parsed_msg['<code>']
    }, bytes(jwt_secret, 'utf-8'), algorithm='HS256'))
