import traceback

from core.builtins import Bot, Url, ErrorMessage
from core.utils.http import get_url
from modules.github.utils import dirty_check, darkCheck


async def search(msg: Bot.MessageSession):
    try:
        result = await get_url('https://api.github.com/search/repositories?q=' + msg.parsed_msg['<query>'], 200,
                               fmt='json')
        if 'message' in result and result['message'] == 'Not Found':
            await msg.finish(msg.locale.t("github.search.message.not_found"))
        elif 'message' in result and result['message']:
            await msg.finish(result['message'])
        items = result['items']
        item_count_expected = int(result['total_count']) if result['total_count'] < 5 else 5
        items_out = []
        for item in items:
            try:
                items_out.append(str(item['full_name'] + ': ' + str(Url(item['html_url']))))
            except TypeError:
                continue
        footnotes = msg.locale.t("github.search.message.more_information", more_result=result['total_count'] - 5) if item_count_expected == 5 else ''
        message = msg.locale.t("github.search.message", result=result['total_count']) + '\n' + '\n'.join(
            items_out[0:item_count_expected]) + f'\n{footnotes}'

        is_dirty = await dirty_check(message) or darkCheck(message)
        if is_dirty:
            message = 'https://wdf.ink/6OUp'

        await msg.finish(message)
    except ValueError:
        await msg.finish(msg.locale.t("github.message.error"))
    except Exception as error:
        await msg.sendMessage(ErrorMessage(str(error)))
        traceback.print_exc()
