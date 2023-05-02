from core.builtins import Bot
from core.component import module
from .mcmod import mcmod as m

mcmod = module(
    bind_prefix='mcmod',
    desc='{mcmod.help.desc}',
    developers=['Dianliang233', 'HornCopper', 'DrLee_lihr'],
    alias={'moddetails': 'mcmod details'},
    support_languages=['zh_cn']
)


@mcmod.handle('<mod_name> {{mcmod.help.mod_name}}')
async def main(msg: Bot.MessageSession):
    message = await m(msg, msg.parsed_msg['<mod_name>'])
    await msg.finish(message)


@mcmod.handle('details <content> {{mcmod.help.details}}')
async def main(msg: Bot.MessageSession):
    message = await m(msg, msg.parsed_msg['<content>'], detail=True)
    await msg.finish(message)
