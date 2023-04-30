from decimal import Decimal
import re
from PIL import Image as PILImage
import io
import asyncio

from langchain.callbacks import get_openai_callback

from core.builtins import Bot, Plain, Image
from core.component import module
from core.dirty_check import check_bool
from core.exceptions import NoReportException

from .agent import agent_executor
from .formatting import generate_latex, generate_code_snippet

ONE_K = Decimal('1000')
# https://openai.com/pricing
BASE_COST_GPT_3_5 = Decimal('0.002')  # gpt-3.5-turbo： $0.002 / 1K tokens
# We are not tracking specific tool usage like searches b/c I'm too lazy, use a universal multiplier
THIRD_PARTY_MULTIPLIER = Decimal('1.5')
PROFIT_MULTIPLIER = Decimal('1.1')  # At the time we are really just trying to break even
PRICE_PER_1K_TOKEN = BASE_COST_GPT_3_5 * THIRD_PARTY_MULTIPLIER * PROFIT_MULTIPLIER
# Assuming 1 USD = 7 CNY, 100 petal = 1 CNY
USD_TO_CNY = 7
CNY_TO_PETAL = 100

a = module('ask', developers=['Dianliang233'], desc='{ask.help.desc}', required_superuser=True)


@a.command('<question> {{ask.help}}')
@a.regex(r'^(?:ask|问)[\:：]? ?(.+?)[?？]$')
async def _(msg: Bot.MessageSession):
    is_superuser = msg.checkSuperUser()
    if not is_superuser and msg.data.petal < 100:  # refuse
        raise NoReportException(msg.locale.t('petal_'))
    if hasattr(msg, 'parsed_msg'):
        question = msg.parsed_msg['<question>']
    else:
        question = msg.matched_msg[0]
    if await check_bool(question):
        raise NoReportException('https://wdf.ink/6OUp')
    with get_openai_callback() as cb:
        res = await agent_executor.arun(question)
        tokens = cb.total_tokens
    # TODO: REMEMBER TO UNCOMMENT THIS BEFORE LAUNCH!!!!
    # if not is_superuser:
    #     price = tokens / ONE_K * PRICE_PER_1K_TOKEN
    #     petal = price * USD_TO_CNY * CNY_TO_PETAL
    #     await msg.data.modify_petal(-petal)
    price = tokens / ONE_K * PRICE_PER_1K_TOKEN
    petal = price * USD_TO_CNY * CNY_TO_PETAL
    msg.data.modify_petal(-int(petal))

    blocks = parse_markdown(res)

    chain = []
    for block in blocks:
        if block['type'] == 'text':
            chain.append(Plain(block['content']))
        elif block['type'] == 'latex':
            chain.append(Image(PILImage.open(io.BytesIO(await generate_latex(block['content'])))))
        elif block['type'] == 'code':
            chain.append(Image(PILImage.open(io.BytesIO(await generate_code_snippet(block['content']['code'], block['content']['language'])))))

    if await check_bool(res):
        raise NoReportException('https://wdf.ink/6OUp')
    await msg.finish(chain)


def parse_markdown(md: str):
    regex = r'(```[\s\S]*?\n```|\$\$[\s\S]*?\$\$|[^\n]+)(?:\n|$)'

    blocks = []
    for match in re.finditer(regex, md):
        content = match.group(1)
        print(content)
        if content.startswith('```'):
            block = 'code'
            try:
                language, code = re.match(r'```(.*)\n([\s\S]*?)\n```', content).groups()
            except AttributeError:
                raise ValueError('Code block is missing language or code')
            content = {'language': language, 'code': code}
        elif content.startswith('$$'):
            block = 'latex'
            content = content[2:-2].strip()
        else:
            block = 'text'
        blocks.append({'type': block, 'content': content})

    return blocks
