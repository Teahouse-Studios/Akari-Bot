import importlib
import glob
import os
import traceback

import orjson as json

from core.console.info import client_name as console_client_name, \
    sender_prefix_list as console_sender_prefix, \
    target_prefix_list as console_target_prefix
from core.logger import Logger
from core.path import bots_info_path


def get_bot_names(attribute_name, console_name):
    names = []
    if not Info.binary_mode:
        for info_file in glob.glob(bots_info_path):
            module_name = os.path.splitext(os.path.relpath(info_file, './'))[0].replace('/', '.')
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, attribute_name):
                    names.extend(
                        getattr(
                            module,
                            attribute_name) if isinstance(
                            getattr(
                                module,
                                attribute_name),
                            list) else [
                            getattr(
                                module,
                                attribute_name)])
            except Exception:
                continue
    else:
        try:
            Logger.warning('Binary mode detected, trying to load pre-built bots list...')
            js = 'assets/bots_list.json'
            with open(js, 'r', encoding='utf-8') as f:
                dir_list = json.loads(f.read())
                for i in dir_list:
                    try:
                        module = importlib.import_module(i.replace('/', '.') + '.info')
                        if hasattr(module, attribute_name):
                            names.extend(
                                getattr(
                                    module,
                                    attribute_name) if isinstance(
                                    getattr(
                                        module,
                                        attribute_name),
                                    list) else [
                                    getattr(
                                        module,
                                        attribute_name)])
                    except Exception:
                        traceback.print_exc()
                        continue
        except Exception:
            Logger.error('Failed to load pre-built bots list...')
            return []
    names.append(console_name)
    return names


def get_all_clients_name():
    return get_bot_names('client_name', console_client_name)


def get_all_sender_prefix():
    return get_bot_names('sender_prefix_list', console_sender_prefix)


def get_all_target_prefix():
    return get_bot_names('target_prefix_list', console_target_prefix)


class Info:
    version = None
    subprocess = False
    binary_mode = False
    command_parsed = 0
    client_name = ''


__all__ = ["get_all_clients_name", "get_all_sender_prefix", "get_all_target_prefix", "Info"]
