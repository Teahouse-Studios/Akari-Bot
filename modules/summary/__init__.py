import re
import openai

from core.builtins import Bot
from core.component import module
from core.dirty_check import check_bool
from core.logger import Logger
from config import Config

openai.api_key = Config('openai_api_key')

s = module('summary', developers=['Dianliang233', 'OasisAkari'], desc='{summary.help}', available_for=['QQ', 'QQ|Group'])


@s.handle('{{summary.help.summary}}')
async def _(msg: Bot.MessageSession):
    f_msg = await msg.waitNextMessage(msg.locale.t('summary.message'), append_instruction=False)
    try:
        f = re.search(r'\[Ke:forward,id=(.*?)\]', f_msg.asDisplay()).group(1)
    except AttributeError:
        await msg.finish(msg.locale.t('summary.message.not_found'))
    Logger.info(f)
    data = await f_msg.call_api('get_forward_msg', message_id=f)
    msgs = data['messages']
    texts = [f'\n{m["sender"]["nickname"]}：{m["content"]}' for m in msgs]

    char_count = sum([len(i) for i in texts])
    wait_msg = await msg.sendMessage(msg.locale.t('summary.message.waiting', count=char_count, time=round(char_count / 33.5, 1)))

    nth = 0
    prev = ''
    while nth < len(texts):
        prompt = msg.locale.t("summary.prompt") \
                 f'''{{msg.locale.t("summary.prompt.hint"), prev=prev} if nth != 0 else ""}'''
        len_prompt = len(prompt)
        post_texts = ''
        for t in texts[nth:]:
            if len(post_texts) + len_prompt < 1970:
                post_texts += texts[nth]
                nth += 1
            else:
                break
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                    {'role': 'system', "content": "You are an helpful assistant."},
                    {'role': 'user', "content": f'''{prompt}

{post_texts}'''},
                ]
        )
    output = completion['choices'][0]['message']['content']
    await wait_msg.delete()
    if await check_bool(output):
        await msg.finish('https://wdf.ink/6OUp')
    await msg.finish(output, disable_secret_check=True)
