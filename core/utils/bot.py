import asyncio
import logging
import os
import traceback
from configparser import ConfigParser
from os.path import abspath

import ujson as json

from core.builtins import PrivateAssets, Secret
from core.exceptions import ConfigFileNotFound
from core.loader import load_modules, ModulesManager
from core.logger import Logger
from core.scheduler import Scheduler
from core.utils.http import get_url
from core.utils.ip import IP

bot_version = 'v4.0.11'


async def init_async() -> None:
    load_modules()
    version = os.path.abspath(PrivateAssets.path + '/version')
    with open(version, 'w') as write_version:
        try:
            write_version.write(os.popen('git rev-parse HEAD', 'r').read()[0:6])
        except Exception as e:
            write_version.write(bot_version)
    
    tag = os.path.abspath(PrivateAssets.path + '/version_tag')
    with open(tag, 'w') as write_tag:
        try:
            write_tag.write(os.popen('git tag -l', 'r').read().split('\n')[-2])
        except Exception as e:
            write_tag.write(bot_version)

    gather_list = []
    Modules = ModulesManager.return_modules_list()
    for x in Modules:
        if schedules := Modules[x].schedule_list.set:
            for schedule in schedules:
                Scheduler.add_job(func=schedule.function, trigger=schedule.trigger, misfire_grace_time=30,
                                  max_instance=1)
    await asyncio.gather(*gather_list)
    Scheduler.start()
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    await load_secret()


async def load_secret():
    config_filename = 'config.cfg'
    config_path = abspath('./config/' + config_filename)
    cp = ConfigParser()
    cp.read(config_path)
    section = cp.sections()
    if len(section) == 0:
        raise ConfigFileNotFound(config_path) from None
    options = cp.options('secret')
    for option in options:
        value = cp.get('secret', option)
        if value.upper() not in ['', 'TRUE', 'FALSE']:
            Secret.add(value.upper())

    async def append_ip():
        try:
            Logger.info('Fetching IP information...')
            ip = await get_url('https://api.ip.sb/geoip', timeout=10, fmt='json')
            if ip:
                Secret.add(ip['ip'])
                IP.country = ip['country']
                IP.address = ip['ip']
            Logger.info('Successfully fetched IP information.')
        except Exception:
            Logger.info('Failed to get IP information.')
            Logger.error(traceback.format_exc())

    asyncio.create_task(append_ip())


async def load_prompt(bot) -> None:
    author_cache = os.path.abspath(PrivateAssets.path + '/cache_restart_author')
    loader_cache = os.path.abspath(PrivateAssets.path + '/.cache_loader')
    if os.path.exists(author_cache):
        open_author_cache = open(author_cache, 'r')
        author = json.loads(open_author_cache.read())['ID']
        open_loader_cache = open(loader_cache, 'r')
        m = await bot.fetch_target(author)
        if m:
            if (read := open_loader_cache.read()) != '':
                await m.sendDirectMessage(m.parent.locale.t('error.loader.load.failed', err_msg=read))
            else:
                await m.sendDirectMessage(m.parent.locale.t('error.loader.load.success'))
            open_loader_cache.close()
            open_author_cache.close()
            os.remove(author_cache)
            os.remove(loader_cache)


__all__ = ['init_async', 'load_prompt']
