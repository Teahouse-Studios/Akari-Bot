import datetime

from core.builtins import Bot, Embed, Image, EmbedField
from core.component import on_command

t = on_command('embed_test', required_superuser=True)


@t.handle()
async def _(session: Bot.MessageSession):
    await session.sendMessage(Embed(title='Embed Test', description='This is a test embed.',
                                    url='https://minecraft.fandom.com/zh/wiki/Minecraft_Wiki',
                                    color=0x00ff00, timestamp=datetime.datetime.now().timestamp(),
                                    author='oasisakari',
                                    footer='Test',
                                    image=Image('https://avatars.githubusercontent.com/u/68471503?s=200&v=4'),
                                    fields=[EmbedField('oaoa', 'aaaaa', inline=True),
                                            EmbedField('oaoa', 'aaaaa', inline=True)]))
