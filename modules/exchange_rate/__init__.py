import datetime

from config import Config
from core.builtins import Bot
from core.component import module
from core.exceptions import NoReportException
from core.utils.http import get_url

api_key = Config('exchange_rate_api_key')

excr = module('exchange_rate',
                       desc='{exchange_rate.help.desc}',
                       alias={'exchangerate': 'exchange_rate',
                              'excr': 'exchange_rate'},
                       developers=['DoroWolf'])


@excr.command('<base> <target> [<amount>] {{exchange_rate.help}}')
async def _(msg: Bot.MessageSession):
    base = msg.parsed_msg['<base>'].upper()
    target = msg.parsed_msg['<target>'].upper()
    amount = msg.parsed_msg.get('<amount>', '1')
    try:
        amount = float(amount)
        if amount <= 0:
            await msg.finish(msg.locale.t('exchange_rate.message.error.non_positive'))
    except ValueError:
        await msg.finish(msg.locale.t('exchange_rate.message.error.non_digital'))
    await msg.finish(await exchange(base, target, amount, msg))



async def exchange(base_currency, target_currency, amount: float, msg):
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/codes'
    data = await get_url(url, 200, fmt='json')
    supported_currencies = data['supported_codes']
    unsupported_currencies = []
    if data['result'] == "success":
        for currencie_names in supported_currencies:
            if base_currency in currencie_names:
                break
        else:
            unsupported_currencies.append(base_currency)
        for currencie_names in supported_currencies:
            if target_currency in currencie_names:
                break
        else:
            unsupported_currencies.append(target_currency)
        if unsupported_currencies:
            await msg.finish(f"{msg.locale.t('exchange_rate.message.error.invalid')}{' '.join(unsupported_currencies)}")
    else:
        error_type = data['error-type']
        raise NoReportException(f"{error_type}")

    url = f'https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}/{amount}'
    data = await get_url(url, 200, fmt='json')
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    if data['result'] == "success":
        exchange_rate = data['conversion_result']
        await msg.finish(
            msg.locale.t('exchange_rate.message', amount=amount, base=base_currency, exchange_rate=exchange_rate,
                         target=target_currency, time=current_time))
    else:
        error_type = data['error-type']
        raise NoReportException(f"{error_type}")



@excr.regex(r"(\d+(\.\d+)?)?\s?([a-zA-Z]{3})[兑|换|兌|換]([a-zA-Z]{3})", desc='{exchange_rate.help.regex.desc}')
async def _(msg: Bot.MessageSession):
    groups = msg.matched_msg.groups()
    amount = groups[0] if groups[0] else '1'
    base = groups[2].upper()
    target = groups[3].upper()
    await msg.finish(await exchange(base, target, amount, msg))
