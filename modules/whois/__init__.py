import ipaddress
import re

from core.builtins import Bot
from core.component import module
from .ip import check_ip, format_ip

# from .domain import check_domain, format_domain

w = module('whois', desc='{whois.help.desc}', 
            alias=['ip'],
            developers=['Dianliang233'])


@w.handle('<ip_or_domain>')
async def _(msg: Bot.MessageSession):
    query = msg.parsed_msg['<ip_or_domain>']
    query_type = ip_or_domain(query)
    if query_type == 'ip':
        res = await check_ip(query)
        await msg.finish(await format_ip(msg, res))
    # elif query_type == 'domain':
    #     res = await check_domain(query)
    #     await msg.finish(await format_domain(res))
    else:
        await msg.finish(msg.locale.t("whois.message.unknown"))
        

def ip_or_domain(string: str):
    domain_regex = r'^https?://[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,4}\b[-a-zA-Z0-9@:%_+.~#?&/=]*$'
    try:
        ipaddress.ip_address(string)
        return 'ip'
    except ValueError:
        if re.match(domain_regex, string):
            return 'domain'