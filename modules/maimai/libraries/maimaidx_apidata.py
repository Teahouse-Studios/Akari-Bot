import os
import traceback
from typing import Optional, Union

import ujson as json
from langconv.converter import LanguageConverter
from langconv.language.zh import zh_cn

from config import Config
from core.builtins import Bot, Image, MessageChain, Plain
from core.exceptions import ConfigValueError
from core.logger import Logger
from core.utils.http import download, get_url, post_url
from core.utils.text import isint
from .maimaidx_mapping import *
from .maimaidx_music import get_cover_len5_id, Music, TotalList


cache_dir = os.path.abspath(Config('cache_path', './cache/'))
total_list = TotalList()


async def update_cover() -> bool:
    id_list = ['00000', '01000']
    for song in (await total_list.get()):
        id_list.append(song['id'])
    cover_dir = os.path.join(assets_path, "static", "mai", "cover")
    if not os.path.exists(cover_dir):
        os.makedirs(cover_dir)
    for id in id_list:
        cover_path = os.path.join(cover_dir, f'{get_cover_len5_id(id)}.png')
        if not os.path.exists(cover_path):
            try:
                url = f"https://www.diving-fish.com/covers/{get_cover_len5_id(id)}.png"
                await download(url, status_code=200, path=cover_dir, filename=f'{get_cover_len5_id(id)}.png', attempt=1)
                Logger.debug(f'Successfully download {get_cover_len5_id(id)}.png')
            except ValueError as e:
                if str(e).startswith('404'):
                    if Config('debug', False):
                        Logger.error(f'Failed to download {get_cover_len5_id(id)}.png')
            except Exception:
                Logger.error(traceback.format_exc())
                return False
    return True


async def update_alias() -> bool:
    try:
        url = "https://download.fanyu.site/maimai/alias.json"
        data = await get_url(url, 200, fmt='json')

        with open(song_alias_path, 'w') as file:
            json.dump(data, file)
    except Exception:
        Logger.error(traceback.format_exc())
        return False
    return True


async def get_info(music: Music, *details) -> MessageChain:
    info = [Plain(f"{music.id} - {music.title}{' (DX)' if music['type'] == 'DX' else ''}")]
    cover_path = os.path.join(cover_dir, f'{get_cover_len5_id(music.id)}.png')
    if os.path.exists(cover_path):
        info.append(Image(cover_path))
    else:
        cover_path = os.path.join(cover_dir, '00000.png')
        if os.path.exists(cover_path):
            info.append(Image(cover_path))
    if details:
        info.extend(details)
    return info


async def get_alias(msg: Bot.MessageSession, sid: str) -> list:
    if not os.path.exists(song_alias_path):
        await msg.finish(msg.locale.t("maimai.message.alias.file_not_found", prefix=msg.prefixes[0]))
    with open(song_alias_path, 'r') as file:
        data = json.load(file)

    result = []
    if sid in data:
        result = data[sid]  # 此处的列表是歌曲别名列表

    return result


async def search_by_alias(input_: str) -> list:
    result = []
    convinput = LanguageConverter.from_language(zh_cn).convert(input_)
    res = (await total_list.get()).filter(title=input_)
    for s in res:
        result.append(s['id'])
    if isint(input_):
        music = (await total_list.get()).by_id(input_)
        if music:
            result.append(input_)

    if not os.path.exists(song_alias_path):
        return list(set(result))

    with open(song_alias_path, 'r') as file:
        data = json.load(file)

    for sid, aliases in data.items():
        aliases = [alias.lower() for alias in aliases]
        if input_ in aliases or convinput in aliases:
            result.append(sid)  # 此处的列表是歌曲 ID 列表

    return list(set(result))


async def get_record(msg: Bot.MessageSession, payload: dict, use_cache: bool = True) -> Optional[str]:
    cache_path = os.path.join(cache_dir, f"{msg.target.sender_id.replace('|', '_')}_maimaidx_record.json")
    url = f"https://www.diving-fish.com/api/maimaidxprober/query/player"
    try:
        data = await post_url(url,
                              data=json.dumps(payload),
                              status_code=200,
                              headers={'Content-Type': 'application/json', 'accept': '*/*'},
                              fmt='json'
                              )
        if use_cache and data:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        return data
    except Exception as e:
        if str(e).startswith('400'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.user_unbound.qq"))
            else:
                await msg.finish(msg.locale.t("maimai.message.user_not_found"))
        elif str(e).startswith('403'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.forbidden.eula"))
            else:
                await msg.finish(msg.locale.t("maimai.message.forbidden"))
        else:
            Logger.error(traceback.format_exc())
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                await msg.send_message(msg.locale.t("maimai.message.use_cache"))
                return data
            except Exception:
                raise e
        else:
            raise e


async def get_song_record(msg: Bot.MessageSession, payload: dict, sid: Union[str, list[str]],
                          use_cache: bool = True) -> Optional[str]:
    if DEVELOPER_TOKEN:
        cache_path = os.path.join(cache_dir, f"{msg.target.sender_id.replace('|', '_')}_maimaidx_song_record.json")
        url = f"https://www.diving-fish.com/api/maimaidxprober/dev/player/record"
        try:
            payload.update({'music_id': sid})
            data = await post_url(url,
                                  data=json.dumps(payload),
                                  status_code=200,
                                  headers={'Content-Type': 'application/json',
                                           'accept': '*/*',
                                           'Developer-Token': DEVELOPER_TOKEN},
                                  fmt='json')
            if use_cache and data:
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        try:
                            backup_data = json.load(f)
                        except Exception:
                            backup_data = {}
                else:
                    backup_data = {}
                backup_data.update(data)
                with open(cache_path, 'w') as f:
                    json.dump(backup_data, f)
            return data
        except Exception as e:
            if str(e).startswith('400'):
                raise ConfigValueError(msg.locale.t('error.config.invalid'))
            else:
                Logger.error(traceback.format_exc())
            if use_cache and os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    await msg.send_message(msg.locale.t("maimai.message.use_cache"))
                    return data
                except Exception:
                    raise e
            else:
                raise e
    else:
        raise ConfigValueError(msg.locale.t('error.config.secret.not_found'))


async def get_total_record(msg: Bot.MessageSession, payload: dict, utage: bool = False,
                           use_cache: bool = True) -> Optional[str]:
    cache_path = os.path.join(cache_dir, f"{msg.target.sender_id.replace('|', '_')}_maimaidx_total_record.json")
    url = f"https://www.diving-fish.com/api/maimaidxprober/query/plate"
    payload['version'] = versions
    try:
        data = await post_url(url,
                              data=json.dumps(payload),
                              status_code=200,
                              headers={'Content-Type': 'application/json', 'accept': '*/*'},
                              fmt='json')
        if use_cache and data:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        if not utage:
            data = {'verlist': [d for d in data['verlist'] if d.get('id', 0) < 100000]}  # 过滤宴谱
        return data
    except Exception as e:
        if str(e).startswith('400'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.user_unbound.qq"))
            else:
                await msg.finish(msg.locale.t("maimai.message.user_not_found"))
        elif str(e).startswith('403'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.forbidden.eula"))
            else:
                await msg.finish(msg.locale.t("maimai.message.forbidden"))
        else:
            Logger.error(traceback.format_exc())
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                await msg.send_message(msg.locale.t("maimai.message.use_cache"))
                if not utage:
                    data = {'verlist': [d for d in data['verlist'] if d.get('id', 0) < 100000]}  # 过滤宴谱
                return data
            except Exception:
                raise e
        else:
            raise e


async def get_plate(msg: Bot.MessageSession, payload: dict, version: str, use_cache: bool = True) -> Optional[str]:
    version = '舞' if version == '覇' else version  # “覇者”属于舞代
    cache_path = os.path.join(cache_dir, f"{msg.target.sender_id.replace('|', '_')}_maimaidx_plate_{version}.json")
    url = f"https://www.diving-fish.com/api/maimaidxprober/query/plate"
    try:
        data = await post_url(url,
                              data=json.dumps(payload),
                              status_code=200,
                              headers={'Content-Type': 'application/json', 'accept': '*/*'},
                              fmt='json')
        if use_cache and data:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        return data
    except Exception as e:
        if str(e).startswith('400'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.user_unbound.qq"))
            else:
                await msg.finish(msg.locale.t("maimai.message.user_not_found"))
        elif str(e).startswith('403'):
            if "qq" in payload:
                await msg.finish(msg.locale.t("maimai.message.forbidden.eula"))
            else:
                await msg.finish(msg.locale.t("maimai.message.forbidden"))
        else:
            Logger.error(traceback.format_exc())
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                await msg.send_message(msg.locale.t("maimai.message.use_cache"))
                return data
            except Exception:
                raise e
        else:
            raise e
