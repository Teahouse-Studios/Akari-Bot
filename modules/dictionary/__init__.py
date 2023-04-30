from core.builtins import Bot, Image, Plain
from core.component import module
from .screenshot import get_pic


dict_module = module('dictionary', alias=["dict"],
                     desc='{dictionary.help.desc}', developers=['Dianliang233'], support_languages=['en_us'])


@dict_module.handle(help_doc='<term> {{dictionary.help}}')
async def _(msg: Bot.MessageSession):
    print(str(msg.parsed_msg['<term>']).replace(' ', '-').lower())
    pic_collins = await get_pic(
        'https://www.collinsdictionary.com/dictionary/english/' + str(msg.parsed_msg['<term>']).replace(' ',
                                                                                                        '-').lower(),
        'collins')
    # pic_yd = await get_pic('https://www.youdao.com/result?word=' + msg.parsed_msg['<term>'] + '&lang=en', 'yd')
    # if pic_collins or pic_yd:
    if pic_collins:
        # await msg.finish([Image(pic_collins), Image(pic_yd),
        await msg.finish([Image(pic_collins), Plain(
            f'https://www.collinsdictionary.com/dictionary/english/{msg.parsed_msg["<term>"]}')])
# 有道：https://www.youdao.com/result?lang=en&word={msg.parsed_msg["<term>"]}'''])
