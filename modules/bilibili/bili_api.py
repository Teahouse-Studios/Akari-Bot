from core.builtins import Bot, Embed, EmbedField, ErrorMessage, Image, Plain, Url
from core.utils.http import get_url
from core.utils.web_render import webrender

DESC_LENGTH = 100


async def get_video_info(msg: Bot.MessageSession, query, get_detail=False, use_embed=False):
    if msg.target.sender_from in ['Discord|Client']:
        use_embed = True
    try:
        url = f'https://api.bilibili.com/x/web-interface/view/detail{query}'
        res = await get_url(webrender('source', url), 200, fmt='json', request_private_ip=True)
        if res['code'] != 0:
            if res['code'] == -400:
                await msg.finish(msg.locale.t("bilibili.message.invalid"))
            else:
                await msg.finish(msg.locale.t('bilibili.message.not_found'))
    except ValueError as e:
        if str(e).startswith('412'):
            await msg.finish(ErrorMessage('{bilibili.message.error.rejected}', locale=msg.locale.locale))
        else:
            raise e

    view = res['data']['View']
    stat = view['stat']

    video_url = f"https://www.bilibili.com/video/{view['bvid']}"
    pic = view['pic']
    title = view['title']
    tname = view['tname']
    desc = view['desc']
    desc = (desc[:100] + '...') if len(desc) > 100 else desc
    time = msg.ts2strftime(view['ctime'], iso=True, timezone=False)

    if len(view['pages']) > 1:
        pages = msg.locale.t("message.brackets", msg=f"{len(view['pages'])}P")
    else:
        pages = ''

    stat_view = format_num(msg, stat['view'])
    stat_danmaku = format_num(msg, stat['danmaku'])
    stat_reply = format_num(msg, stat['reply'])
    stat_favorite = format_num(msg, stat['favorite'])
    stat_coin = format_num(msg, stat['coin'])
    stat_share = format_num(msg, stat['share'])
    stat_like = format_num(msg, stat['like'])

    owner = view['owner']['name']
    avatar = view['owner']['face']
    fans = format_num(msg, res['data']['Card']['card']['fans'])

    if use_embed:
        await msg.finish(Embed(title=f'{title}{pages}',
                               description=desc,
                               url=video_url,
                               author=f"{owner}{msg.locale.t('message.brackets', msg=fans)}",
                               footer='Bilibili',
                               image=Image(pic),
                               thumbnail=Image(avatar),
                               fields=[EmbedField(msg.locale.t('bilibili.message.embed.type'), tname),
                                       EmbedField(msg.locale.t('bilibili.message.embed.view'), stat_view, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.danmaku'), stat_danmaku, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.reply'), stat_reply, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.like'), stat_like, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.coin'), stat_coin, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.favorite'), stat_favorite, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.share'), stat_share, inline=True),
                                       EmbedField(msg.locale.t('bilibili.message.embed.time'), time)]))
    elif not get_detail:
        output = msg.locale.t("bilibili.message", title=title, tname=tname, owner=owner, time=time)
        await msg.finish([Image(pic), Url(video_url), Plain(output)])
    else:
        output = msg.locale.t("bilibili.message.detail", title=title, pages=pages, tname=tname,
                              owner=owner, fans=fans, view=stat_view, danmaku=stat_danmaku,
                              reply=stat_reply,
                              like=stat_like, coin=stat_coin, favorite=stat_favorite, share=stat_share,
                              desc=desc, time=time)
        await msg.finish([Image(pic), Url(video_url), Plain(output)])


def format_num(msg: Bot.MessageSession, number):
    if msg.locale.locale in ['zh_cn', 'zh_tw']:
        zh_tw = True if msg.locale.locale == 'zh_tw' else False
        if number >= 100000000:
            formatted_number = number / 100000000
            formatted_str = f'{formatted_number:.2f}' if formatted_number < 100 else f'{formatted_number:.1f}'
            return formatted_str.rstrip('0').rstrip('.') + ('億' if zh_tw else '亿')
        elif number >= 10000:
            formatted_number = number / 10000
            formatted_str = f'{formatted_number:.2f}' if formatted_number < 100 else f'{formatted_number:.1f}'
            return formatted_str.rstrip('0').rstrip('.') + ('萬' if zh_tw else '万')
        else:
            return str(number)
    else:
        if number >= 1000000000:
            formatted_number = number / 1000000000
            formatted_str = f'{formatted_number:.2f}' if formatted_number < 100 else f'{formatted_number:.1f}'
            return formatted_str.rstrip('0').rstrip('.') + 'G'
        elif number >= 1000000:
            formatted_number = number / 1000000
            formatted_str = f'{formatted_number:.2f}' if formatted_number < 100 else f'{formatted_number:.1f}'
            return formatted_str.rstrip('0').rstrip('.') + 'M'
        elif number >= 1000:
            formatted_number = number / 1000
            formatted_str = f'{formatted_number:.2f}' if formatted_number < 100 else f'{formatted_number:.1f}'
            return formatted_str.rstrip('0').rstrip('.') + 'k'
        else:
            return str(number)
