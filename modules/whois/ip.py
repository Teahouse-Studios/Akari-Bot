import ipaddress
import json
import socket
from typing import Any, Dict

from core.utils.http import get_url


async def check_ip(ip: str):
    info = ipaddress.ip_address(ip)
    ip_property = ''
    real_ip = None
    skip_geoip = False
    if info.is_multicast:
        ip_property = 'multicast'
    elif info.is_global:
        ip_property = 'global'
    elif info.is_loopback:
        ip_property = 'loopback'
        skip_geoip = True
    elif info.is_unspecified:
        ip_property = 'unspecified'
        skip_geoip = True
    elif info.is_link_local:
        ip_property = 'link_local'
        skip_geoip = True
    elif info.is_reserved:
        ip_property = 'reserved'
        skip_geoip = True
    elif info.is_private:
        ip_property = 'private'
        skip_geoip = True
    elif isinstance(info, ipaddress.IPv6Address):
        if info.is_site_local:
            ip_property = 'site_local'
        elif info.ipv4_mapped:
            ip_property = 'ipv4_mapped'
            real_ip = info.ipv4_mapped.compressed
        elif info.sixtofour:
            ip_property = 'sixtofour'
            real_ip = info.sixtofour.compressed
        elif info.teredo:
            ip_property = 'teredo'
            ip = str(info.teredo)
    else:
        ip_property = 'unknown'
        skip_geoip = True

    res = {
        'ip': ip,
        'version': info.version,
        'country_code': None,
        'country': None,
        'region_code': None,
        'region': None,
        'city': None,
        'postal_code': None,
        'contient_code': None,
        'latitude': None,
        'longitude': None,
        'organization': None,
        'asn': None,
        'asn_organization': None,
        'offset': None,
        'reverse': None,
        'ip_property': ip_property,
        'real_ip': real_ip
    }
    if not skip_geoip:
        data = json.loads(await get_url('https://api.ip.sb/geoip/' + ip))
        reverse = socket.getnameinfo((ip, 0), 0)
        res['reverse'] = reverse[0]
        for key in res:
            if key in data:
                res[key] = data[key]
    return res


def parse_coordinate(axis: str, value: float):
    if axis == 'latitude':
        return f'{value}°{"N" if value > 0 else "S"}'
    elif axis == 'longitude':
        return f'{value}°{"E" if value > 0 else "W"}'


async def format_ip(msg, info: Dict[str, Any]):
    ip_property = {
        'global': msg.locale.t('whois.message.ip.ip_property.global'),
        'private': msg.locale.t('whois.message.ip.ip_property.private'),
        'reserved': msg.locale.t('whois.message.ip.ip_property.reserved'),
        'multicast': msg.locale.t('whois.message.ip.ip_property.multicast'),
        'link_local': msg.locale.t('whois.message.ip.ip_property.link_local'),
        'loopback': msg.locale.t('whois.message.ip.ip_property.loopback'),
        'unspecified': msg.locale.t('whois.message.ip.ip_property.unspecified'),
        'ipv4_mapped': msg.locale.t('whois.message.ip.ip_property.ipv4_mapped'),
        'sixtofour': msg.locale.t('whois.message.ip.ip_property.sixtofour'),
        'teredo': msg.locale.t('whois.message.ip.ip_property.teredo'),
        'site_local': msg.locale.t('whois.message.ip.ip_property.site_local'),
        'unknown': msg.locale.t('whois.message.ip.ip_property.unknown')
    }

    return f'''\
{info['ip']}
{msg.locale.t('whois.message.ip.type')}IPv{info['version']} {ip_property[info['ip_property']]}{msg.locale.t('whois.message.ip.ip_property')}{f"""
{msg.locale.t('whois.message.ip.real_ip')}{info['real_ip']}""" if info['real_ip'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.location')}{f"{info['city']}, " if info['city'] is not None else ''}{f"{info['region']}, " if info['region'] is not None else ''}{info['country']}""" if info['country'] is not None else ''}{f" ({parse_coordinate('longitude', info['longitude'])}, {parse_coordinate('latitude', info['latitude'])})" if info['longitude'] is not None and info['latitude'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.postal_code')}{info['postal_code']}""" if info['postal_code'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.organization')}{info['organization']}""" if info['organization'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.asn')}{info['asn']}""" if info['asn'] is not None else ''}{f" ({info['asn_organization']}) " if info['asn_organization'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.utc')}UTC{(info['offset'] / 3600):+g}""" if info['offset'] is not None else ''}{f"""
{msg.locale.t('whois.message.ip.reverse')}{info['reverse']}""" if info['reverse'] is not None and info['reverse'] != info['ip'] else ''}'''
