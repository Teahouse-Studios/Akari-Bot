import ast
import os
import re
import shutil
import sys
import traceback  # noqa
from time import sleep

if __name__ == '__main__':
    sys.path.append(os.getcwd())

from core.constants import *
from core.utils.i18n import Locale
from core.utils.text import isint

TYPE_MAPPING = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
}


def safe_literal_eval(node):
    """ 安全解析 AST 节点 """
    if isinstance(node, ast.Str):  # 字符串类型
        return node.s
    elif isinstance(node, ast.Num):  # 数字类型
        return node.n
    elif isinstance(node, ast.NameConstant):  # 常量类型 (True, False, None)
        return node.value
    elif isinstance(node, ast.Tuple):  # 元组类型
        # 对元组元素进行递归解析，对于 type 类型的元素保持原样
        return tuple(safe_literal_eval(el) if not isinstance(el, ast.Name)
                     or el.id != 'type' else el for el in node.elts)
    elif isinstance(node, ast.List):  # 列表类型
        return tuple(safe_literal_eval(el) for el in node.elts)  # 转换成元组
    elif isinstance(node, ast.Dict):  # 字典类型
        return frozenset((safe_literal_eval(k), safe_literal_eval(v))
                         for k, v in zip(node.keys, node.values))  # 转换成 frozenset
    elif isinstance(node, ast.Name):  # 变量名类型
        return TYPE_MAPPING.get(node.id, node.id)  # 尝试在映射表中查找
    else:
        return None  # 对于其他不支持的类型返回 None 或进行其他处理


def generate_config(dir_path, language):
    config_code_list = {}
    os.makedirs(dir_path, exist_ok=True)
    path_ = os.path.join(dir_path, config_filename)

    dir_list = ['bots', 'core', 'modules', 'schedulers']
    exclude_dir_list = [os.path.join('core', 'config'), os.path.join('core', 'scripts')]


    # create empty config.toml
    locale = Locale(language)
    with open(path_, 'w', encoding='utf-8') as f:
        f.write(f"# {locale.t('config.header.line.1', fallback_failed_prompt=False)}\n")
        f.write(f"# {locale.t('config.header.line.2', fallback_failed_prompt=False)}\n")
        f.write(f"# {locale.t('config.header.line.3', fallback_failed_prompt=False)}\n")
        f.write('\n')
        f.write(
            f'default_locale = "{language}" # {
                locale.t(
                    "config.comments.default_locale",
                    fallback_failed_prompt=False)}\n')
        f.write(
            f'config_version = {
                str(config_version)} # {
                locale.t(
                    "config.comments.config_version",
                    fallback_failed_prompt=False)}\n')
        f.write('initialized = false\n')

    from core.config import Config, CFGManager  # noqa
    CFGManager.switch_config_path(dir_path)

    for _dir in dir_list:
        for root, _, _files in os.walk(_dir):
            if root in exclude_dir_list:
                continue
            for file in _files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()

                        # 解析代码中的函数调用
                        tree = ast.parse(code)
                        for node in ast.walk(tree):
                            if isinstance(
                                    node, ast.Call) and isinstance(
                                    node.func, ast.Name) and node.func.id == "Config":
                                # 提取位置参数 (args) 和关键字参数 (kwargs)
                                args = []
                                kwargs = {}

                                # 提取位置参数
                                for arg in node.args:
                                    args.append(safe_literal_eval(arg))

                                # 提取关键字参数
                                for kwarg in node.keywords:
                                    kwargs[kwarg.arg] = safe_literal_eval(kwarg.value)

                                # 在参数列表中加上 _generate=True
                                kwargs['_generate'] = True

                                # 存储参数：使用元组作为键，`args` 和 `kwargs` 分开
                                config_code_list[(tuple(args), frozenset(kwargs.items()))] = file_path

    # 调用 Config 函数
    for (args, kwargs) in config_code_list:
        try:
            # 安全地调用 Config 函数
            print(str(args))
            print(str(kwargs))
            Config(*args, **dict(kwargs))
        except Exception:
            traceback.print_exc()

    CFGManager.write('initialized', True)


if not os.path.exists(os.path.join(config_path, config_filename)) and __name__ != '__main__':
    while True:
        i = 1
        lang = input(
            f"""Hi, it seems you are first time to run AkariBot, what language do you want to use by default?
{''.join([f"{i}. {lang_list[list(lang_list.keys())[i - 1]]}\n" for i in range(1, len(lang_list) + 1)])}
Please input the number of the language you want to use: """)
        if lang.strip() == '':
            sys.exit(0)
        if isint(lang) and (langI := (int(lang) - 1)) in range(len(lang_list)):
            lang = list(lang_list.keys())[langI]
            break
        print('Invalid input, please try again.')

    generate_config(config_path, lang)

    sleep(1)
    print('Config file generated successfully, please modify the config file according to your needs.')
    print('The config file is located at ' + config_path)
    print('Please restart the bot after modifying the config file.')
    print('Press enter to exit.')
    input()
    sys.exit(0)


if __name__ == '__main__':
    import zipfile
    import difflib

    def zip_language_folders(config_store_path, config_store_packed_path):
        for lang in os.listdir(config_store_path):
            lang_path = os.path.join(config_store_path, lang)
            if os.path.isdir(lang_path):
                zip_path = os.path.join(config_store_packed_path, f'{lang}.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, _, files in os.walk(lang_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, lang_path)
                            zipf.write(file_path, arcname)

    config_store_path = os.path.join(assets_path, 'config_store')
    config_store_packed_path = os.path.join(assets_path, 'config_store_packed')
    config_store_path_bak = config_store_path + '_bak'
    if os.path.exists(config_store_path_bak):
        shutil.rmtree(config_store_path_bak)
    if os.path.exists(config_store_path):
        shutil.move(config_store_path, config_store_path_bak)
    os.makedirs(config_store_path, exist_ok=True)
    os.makedirs(config_store_packed_path, exist_ok=True)
    for lang in lang_list:
        config_store_path_ = os.path.join(config_store_path, lang)
        os.makedirs(config_store_path_, exist_ok=True)
        generate_config(config_store_path_, lang)
    # compare old and new config files
    repack = False
    for lang in lang_list:
        config_store_path_ = os.path.join(config_store_path, lang)
        config_store_path_bak = config_store_path + '_bak'
        if not os.path.exists(config_store_path_bak):
            repack = True
            break
        for root, _, files_ in os.walk(config_store_path_):
            for file in files_:
                file_path = os.path.join(root, file)
                file_path_bak = file_path.replace(config_store_path, config_store_path_bak)
                if not os.path.exists(file_path_bak):
                    repack = True
                    break
                with open(file_path, 'r', encoding='utf-8') as f:
                    new = f.readlines()
                with open(file_path_bak, 'r', encoding='utf-8') as f:
                    old = f.readlines()
                diff = difflib.unified_diff(old, new, fromfile=file_path_bak, tofile=file_path)
                for d in diff:

                    if d:
                        print(d)
                        repack = True
                        break
            if repack:
                break
    if repack:
        zip_language_folders(config_store_path, config_store_packed_path)
        print('Changes detected, repacked the config files.')
    shutil.rmtree(config_store_path + '_bak')

    print('Config files generated successfully.')
