import re
import traceback

from config import Config
from core.builtins import Image, Plain, Bot
from core.component import module
from core.exceptions import InvalidHelpDocTypeError
from core.loader import ModulesManager
from core.parser.command import CommandParser
from core.utils.image_table import ImageTable, image_table_render
from database import BotDBUtil

m = module('module',
           base=True,
           alias={'enable': 'module enable',
                  'disable': 'module disable',
                  'reload': 'module reload'},
           developers=['OasisAkari', 'Light-Beacon'],
           required_admin=True
           )


@m.command(['enable <module>... {{core.help.module.enable}}',
            'enable all {{core.help.module.enable_all}}',
            'disable <module>... {{core.help.module.disable}}',
            'disable all {{core.help.module.disable_all}}',
            'reload <module> ... {{core.help.module.reload}}',
            'list {{core.help.module.list}}'], exclude_from=['QQ|Guild'])
async def _(msg: Bot.MessageSession):
    if msg.parsed_msg.get('list', False):
        await modules_help(msg)
    await config_modules(msg)


@m.command(['enable <module>... {{core.help.module.enable}}',
            'enable all {{core.help.module.enable_all}}',
            'disable <module>... {{core.help.module.disable}}',
            'disable all {{core.help.module.disable_all}}',
            'reload <module> ... {{core.help.module.reload}}',
            'list {{core.help.module.list}}'], options_desc={'-g': '{core.help.option.tion.tion.tion.tion.module.g}'},
           available_for=['QQ|Guild'])
async def _(msg: Bot.MessageSession):
    if msg.parsed_msg.get('list', False):
        await modules_help(msg)
    await config_modules(msg)


async def config_modules(msg: Bot.MessageSession):
    alias = ModulesManager.modules_aliases
    modules_ = ModulesManager.return_modules_list(
        targetFrom=msg.target.targetFrom)
    enabled_modules_list = BotDBUtil.TargetInfo(msg).enabled_modules
    wait_config = [msg.parsed_msg.get(
        '<module>')] + msg.parsed_msg.get('...', [])
    wait_config_list = []
    for module_ in wait_config:
        if module_ not in wait_config_list:
            if module_ in alias:
                wait_config_list.append(alias[module_])
            else:
                wait_config_list.append(module_)
    msglist = []
    recommend_modules_list = []
    recommend_modules_help_doc_list = []
    if msg.parsed_msg.get('enable', False):
        enable_list = []
        if msg.parsed_msg.get('all', False):
            for function in modules_:
                if function[0] == '_':
                    continue
                if modules_[function].base or modules_[function].required_superuser:
                    continue
                enable_list.append(function)
        else:
            for module_ in wait_config_list:
                if module_ not in modules_:
                    msglist.append(msg.locale.t("core.message.module.enable.not_found", module=module_))
                else:
                    if modules_[module_].required_superuser and not msg.checkSuperUser():
                        msglist.append(msg.locale.t("core.message.module.enable.perimission.denied",
                                                    module=module_))
                    elif modules_[module_].base:
                        msglist.append(msg.locale.t("core.message.module.enable.base", module=module_))
                    else:
                        enable_list.append(module_)
                        recommend = modules_[module_].recommend_modules
                        if recommend is not None:
                            for r in recommend:
                                if r not in enable_list and r not in enabled_modules_list:
                                    recommend_modules_list.append(r)
        if '-g' in msg.parsed_msg and msg.parsed_msg['-g']:
            get_all_channel = await msg.get_text_channel_list()
            for x in get_all_channel:
                query = BotDBUtil.TargetInfo(f'{msg.target.targetFrom}|{x}')
                query.enable(enable_list)
            for x in enable_list:
                msglist.append(msg.locale.t("core.message.module.enable.qq_channel_global.success", module=x))
        else:
            if msg.data.enable(enable_list):
                for x in enable_list:
                    if x in enabled_modules_list:
                        msglist.append(msg.locale.t("core.message.module.enable.already", module=x))
                    else:
                        msglist.append(msg.locale.t("core.message.module.enable.success", module=x))
                        support_lang = modules_[x].support_languages
                        if support_lang is not None:
                            if msg.locale.locale not in support_lang:
                                msglist.append(msg.locale.t("core.message.module.unsupported_language",
                                                            module=x))
        if recommend_modules_list:
            for m in recommend_modules_list:
                try:
                    recommend_modules_help_doc_list.append(msg.locale.t("core.message.module.module.help", module=m
                                                                        ))

                    if modules_[m].desc is not None:
                        d_ = modules_[m].desc
                        if locale_str := re.findall(r'\{(.*)}', d_):
                            for l in locale_str:
                                d_ = d_.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                        recommend_modules_help_doc_list.append(d_)
                    hdoc = CommandParser(modules_[m], msg=msg, bind_prefix=modules_[m].bind_prefix,
                                         command_prefixes=msg.prefixes).return_formatted_help_doc()
                    if hdoc == '':
                        hdoc = msg.locale.t('core.help.none')
                    recommend_modules_help_doc_list.append(hdoc)
                except InvalidHelpDocTypeError:
                    pass
    elif msg.parsed_msg.get('disable', False):
        disable_list = []
        if msg.parsed_msg.get('all', False):
            for function in modules_:
                if function[0] == '_':
                    continue
                if modules_[function].base or modules_[function].required_superuser:
                    continue
                disable_list.append(function)
        else:
            for module_ in wait_config_list:
                if module_ not in modules_:
                    msglist.append(msg.locale.t("core.message.module.disable.not_found", module=module_))
                else:
                    if modules_[module_].required_superuser and not msg.checkSuperUser():
                        msglist.append(msg.locale.t("core.message.module.disable.permission.denied",
                                                    module=module_))
                    elif modules_[module_].base:
                        msglist.append(msg.locale.t("core.message.module.disable.base", module=module_))
                    else:
                        disable_list.append(module_)
        if '-g' in msg.parsed_msg and msg.parsed_msg['-g']:
            get_all_channel = await msg.get_text_channel_list()
            for x in get_all_channel:
                query = BotDBUtil.TargetInfo(f'{msg.target.targetFrom}|{x}')
                query.disable(disable_list)
            for x in disable_list:
                msglist.append(msg.locale.t("core.message.module.disable.qqchannel_global.success", module=x))
        else:
            if msg.data.disable(disable_list):
                for x in disable_list:
                    if x not in enabled_modules_list:
                        msglist.append(msg.locale.t("core.message.module.disable.already", module=x))
                    else:
                        msglist.append(msg.locale.t("core.message.module.disable.success", module=x))
    elif msg.parsed_msg.get('reload', False):
        if msg.checkSuperUser():
            def module_reload(module, extra_modules):
                reloadCnt = ModulesManager.reload_module(module)
                if reloadCnt > 1:
                    return f'{msg.locale.t("core.message.module.reload.success", module=module)}' + ' '.join(
                        extra_modules) + msg.locale.t("core.message.module.reload.with", reloadCnt=reloadCnt - 1)
                elif reloadCnt == 1:
                    return f'{msg.locale.t("core.message.module.reload.success", module=module)}' + \
                        ' '.join(extra_modules) + msg.locale.t("core.message.module.reload.no_more")
                else:
                    return f'{msg.locale.t("core.message.module.reload.failed")}'

            if '-f' in msg.parsed_msg and msg.parsed_msg['-f']:
                msglist.append(module_reload(module_))
            elif module_ not in modules_:
                msglist.append(msg.locale.t("core.message.module.reload.unbound", module=module_))
            else:
                if modules_[module_].base:
                    msglist.append(msg.locale.t("core.message.module.reload.base", module=module_))
                else:
                    extra_reload_modules = ModulesManager.search_related_module(module_, False)
                    if len(extra_reload_modules):
                        confirm = await msg.waitConfirm(msg.locale.t("core.message.module.reload.confirm",
                                                                     modules='\n'.join(extra_reload_modules)))
                        if not confirm:
                            await msg.finish()
                            return
                    msglist.append(module_reload(module_, extra_reload_modules))
        else:
            msglist.append(msg.locale.t("core.message.module.reload.permission.denied"))
    if msglist is not None:
        if not recommend_modules_help_doc_list:
            await msg.finish('\n'.join(msglist))
        else:
            await msg.sendMessage('\n'.join(msglist))
    if recommend_modules_help_doc_list and ('-g' not in msg.parsed_msg or not msg.parsed_msg['-g']):
        confirm = await msg.waitConfirm(msg.locale.t("core.message.module.recommends",
                                                     msgs='\n'.join(recommend_modules_list) + '\n\n' +
                                                     '\n'.join(recommend_modules_help_doc_list)))
        if confirm:
            if msg.data.enable(recommend_modules_list):
                msglist = []
                for x in recommend_modules_list:
                    msglist.append(msg.locale.t("core.message.module.enable.success", module=x))
                await msg.finish('\n'.join(msglist))
    else:
        await msg.finish()


hlp = module('help',
             base=True,
             developers=['OasisAkari', 'Dianliang233'],
             )


@hlp.command('<module> {{core.help.module.help.detail}}')
async def bot_help(msg: Bot.MessageSession):
    module_list = ModulesManager.return_modules_list(
        targetFrom=msg.target.targetFrom)
    alias = ModulesManager.modules_aliases
    if msg.parsed_msg is not None:
        msgs = []
        help_name = msg.parsed_msg['<module>']
        if help_name in alias:
            help_name = alias[help_name]
        if help_name in module_list:
            module_ = module_list[help_name]
            if module_.desc is not None:
                desc = module_.desc
                if locale_str := re.match(r'\{(.*)}', desc):
                    if locale_str:
                        desc = msg.locale.t(locale_str.group(1))
                msgs.append(desc)
            help_ = CommandParser(module_list[help_name], msg=msg, bind_prefix=module_list[help_name].bind_prefix,
                                  command_prefixes=msg.prefixes)
            if help_.args:
                msgs.append(help_.return_formatted_help_doc())

            doc = '\n'.join(msgs)
            if module_.regex_list.set:
                doc += '\n' + msg.locale.t("core.message.module.help.support_regex")
                for regex in module_.regex_list.set:
                    pattern = None
                    if isinstance(regex.pattern, str):
                        pattern = regex.pattern
                    elif isinstance(regex.pattern, re.Pattern):
                        pattern = regex.pattern.pattern
                    if pattern:
                        desc = regex.desc
                        if desc:
                            if locale_str := re.findall(r'\{(.*)}', desc):
                                for l in locale_str:
                                    desc = desc.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                            doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.detail",
                                                                  msg=desc)
                        else:
                            doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.no_information")
            module_alias = module_.alias
            malias = []
            if module_alias:
                for a in module_alias:
                    malias.append(f'{a} -> {module_alias[a]}')
            if module_.developers is not None:
                devs = '、'.join(module_.developers)
            else:
                devs = ''
            devs_msg = '\n' + msg.locale.t("core.message.module.help.author.type1") + devs
            wiki_msg = '\n' + msg.locale.t("core.message.module.help.helpdoc.address",
                                           help_url=Config('help_url')) + '/' + help_name
            if len(doc) > 500 and msg.Feature.image:
                try:
                    tables = [ImageTable([[doc, '\n'.join(malias), devs]],
                                         [msg.locale.t("core.message.module.help.table.header.help"),
                                          msg.locale.t("core.message.module.help.table.header.alias"),
                                          msg.locale.t("core.message.module.help.author.type2")])]
                    render = await image_table_render(tables)
                    if render:
                        await msg.finish([Image(render),
                                          Plain(wiki_msg)])
                except Exception:
                    traceback.print_exc()
            if malias:
                doc += f'\n{msg.locale.t("core.help.alias")}\n' + '\n'.join(malias)
            await msg.finish(doc + devs_msg + wiki_msg)
        else:
            await msg.finish(msg.locale.t("core.message.module.help.not_found"))


@hlp.command('{{core.help.module.help}}')
async def _(msg: Bot.MessageSession):
    module_list = ModulesManager.return_modules_list(
        targetFrom=msg.target.targetFrom)
    target_enabled_list = msg.enabled_modules
    legacy_help = True
    if msg.Feature.image:
        try:
            tables = []
            essential = []
            m = []
            for x in module_list:
                module_ = module_list[x]
                appends = [module_.bind_prefix]
                doc_ = []
                help_ = CommandParser(module_, msg=msg, bind_prefix=module_.bind_prefix,
                                      command_prefixes=msg.prefixes)

                if module_.desc is not None:
                    d_ = module_.desc
                    if locale_str := re.findall(r'\{(.*)}', d_):
                        for l in locale_str:
                            d_ = d_.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                    doc_.append(d_)
                if help_.args:
                    doc_.append(help_.return_formatted_help_doc())
                doc = '\n'.join(doc_)
                if module_.regex_list.set:
                    doc += '\n' + msg.locale.t("core.message.module.help.support_regex")
                    for regex in module_.regex_list.set:
                        pattern = None
                        if isinstance(regex.pattern, str):
                            pattern = regex.pattern
                        elif isinstance(regex.pattern, re.Pattern):
                            pattern = regex.pattern.pattern
                        if pattern:
                            desc = regex.desc
                            if desc:
                                if locale_str := re.findall(r'\{(.*)}', desc):
                                    for l in locale_str:
                                        desc = desc.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                                doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.detail",
                                                                      msg=desc)
                            else:
                                doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.no_information")
                appends.append(doc)
                module_alias = module_.alias
                malias = []
                if module_alias:
                    for a in module_alias:
                        malias.append(f'{a} -> {module_alias[a]}')
                appends.append('\n'.join(malias) if malias else '')
                if module_.developers:
                    appends.append('、'.join(module_.developers))
                if module_.base:
                    essential.append(appends)
                if x in target_enabled_list:
                    m.append(appends)
            if essential:
                tables.append(ImageTable(
                    essential, [msg.locale.t("core.message.module.help.table.header.base"),
                                msg.locale.t("core.message.module.help.table.header.help"),
                                msg.locale.t("core.message.module.help.table.header.alias"),
                                msg.locale.t("core.message.module.help.author.type2")]))
            if m:
                tables.append(ImageTable(m, [msg.locale.t("core.message.module.help.table.header.external"),
                                             msg.locale.t("core.message.module.help.table.header.help"),
                                             msg.locale.t("core.message.module.help.table.header.alias"),
                                             msg.locale.t("core.message.module.help.author.type2")]))
            if tables:
                render = await image_table_render(tables)
                if render:
                    legacy_help = False
                    await msg.finish([Image(render),
                                      Plain(msg.locale.t("core.message.module.help.more_information",
                                                         prefix=msg.prefixes[0], help_url=Config('help_url'), donate_url=Config('donate_url')))])
        except Exception:
            traceback.print_exc()
    if legacy_help:
        help_msg = [msg.locale.t("core.message.module.help.legacy.base")]
        essential = []
        for x in module_list:
            if module_list[x].base:
                essential.append(module_list[x].bind_prefix)
        help_msg.append(' | '.join(essential))
        help_msg.append(msg.locale.t("core.message.module.help.legacy.external"))
        module_ = []
        for x in module_list:
            if x in target_enabled_list:
                module_.append(x)
        help_msg.append(' | '.join(module_))
        help_msg.append(
            msg.locale.t(
                "core.message.module.help.legacy.more_information",
                prefix=msg.prefixes[0],
                help_url=Config('help_url')))
        if msg.Feature.delete:
            help_msg.append(msg.locale.t("core.message.module.help.revoke.legacy"))
        send = await msg.sendMessage('\n'.join(help_msg))
        await msg.sleep(60)
        await send.delete()


async def modules_help(msg: Bot.MessageSession):
    module_list = ModulesManager.return_modules_list(
        targetFrom=msg.target.targetFrom)
    legacy_help = True
    if msg.Feature.image:
        try:
            tables = []
            m = []
            for x in module_list:
                module_ = module_list[x]
                if x[0] == '_':
                    continue
                if module_.base or module_.required_superuser:
                    continue
                appends = [module_.bind_prefix]
                doc_ = []
                help_ = CommandParser(
                    module_, bind_prefix=module_.bind_prefix, command_prefixes=msg.prefixes, msg=msg)
                if module_.desc is not None:
                    desc = module_.desc
                    if locale_str := re.findall(r'\{(.*)}', desc):
                        for l in locale_str:
                            desc = desc.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                    doc_.append(desc)
                if help_.args:
                    doc_.append(help_.return_formatted_help_doc())
                doc = '\n'.join(doc_)
                if module_.regex_list.set:
                    doc += '\n' + msg.locale.t("core.message.module.help.support_regex")
                    for regex in module_.regex_list.set:
                        pattern = None
                        if isinstance(regex.pattern, str):
                            pattern = regex.pattern
                        elif isinstance(regex.pattern, re.Pattern):
                            pattern = regex.pattern.pattern
                        if pattern:
                            desc = regex.desc
                            if desc:
                                if locale_str := re.findall(r'\{(.*)}', desc):
                                    for l in locale_str:
                                        desc = desc.replace(f'{{{l}}}', msg.locale.t(l, fallback_failed_prompt=False))
                                doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.detail",
                                                                      msg=desc)
                            else:
                                doc += f'\n{pattern} ' + msg.locale.t("core.message.module.help.regex.no_information")
                appends.append(doc)
                module_alias = module_.alias
                malias = []
                if module_alias:
                    for a in module_alias:
                        malias.append(f'{a} -> {module_alias[a]}')
                appends.append('\n'.join(malias) if malias else '')
                if module_.developers:
                    appends.append('、'.join(module_.developers))
                m.append(appends)
            if m:
                tables.append(ImageTable(m, [msg.locale.t("core.message.module.help.table.header.external"),
                                             msg.locale.t("core.message.module.help.table.header.help"),
                                             msg.locale.t("core.message.module.help.table.header.alias"),
                                             msg.locale.t("core.message.module.help.author.type2")]))
            if tables:
                render = await image_table_render(tables)
                if render:
                    legacy_help = False
                    await msg.finish([Image(render)])
        except Exception:
            traceback.print_exc()
    if legacy_help:
        help_msg = [msg.locale.t("core.message.module.help.legacy.availables")]
        module_ = []
        for x in module_list:
            if x[0] == '_':
                continue
            if module_list[x].base or module_list[x].required_superuser:
                continue
            module_.append(module_list[x].bind_prefix)
        help_msg.append(' | '.join(module_))
        help_msg.append(
            msg.locale.t(
                "core.message.module.help.legacy.more_information",
                prefix=msg.prefixes[0],
                help_url=Config('help_url')))
        if msg.Feature.delete:
            help_msg.append(msg.locale.t("core.message.module.help.revoke.legacy"))
        send = await msg.sendMessage('\n'.join(help_msg))
        await msg.sleep(60)
        await send.delete()
