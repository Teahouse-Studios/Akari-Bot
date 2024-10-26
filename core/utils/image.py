import base64
import traceback
from io import BytesIO
from typing import List, Union

import aiohttp
import filetype as ft
import orjson as json
from aiofile import async_open
from jinja2 import FileSystemLoader, Environment
from PIL import Image as PILImage

from core.builtins import Plain, Image, Voice, Embed, MessageChain, MessageSession
from core.logger import Logger
from core.utils.cache import random_cache_path
from core.utils.http import download
from core.utils.web_render import WebRender, webrender


env = Environment(loader=FileSystemLoader('assets/templates'))


async def image_split(i: Image) -> List[Image]:
    i = PILImage.open(await i.get())
    iw, ih = i.size
    if ih <= 1500:
        return [Image(i)]
    _h = 0
    i_list = []
    for x in range((ih // 1500) + 1):
        if _h + 1500 > ih:
            crop_h = ih
        else:
            crop_h = _h + 1500
        i_list.append(Image(i.crop((0, _h, iw, crop_h))))
        _h = crop_h
    return i_list


def get_fontsize(font, text):
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


save_source = True


async def msgchain2image(message_chain: Union[List, MessageChain], msg: MessageSession = None, use_local=True) -> Union[List[PILImage], bool]:
    '''使用Webrender将消息链转换为图片。

    :param message_chain: 消息链或消息链列表。
    :param use_local: 是否使用本地Webrender渲染。
    :return: 图片的PIL对象列表。
    '''
    if not WebRender.status:
        return False
    elif not WebRender.local:
        use_local = False
    if isinstance(message_chain, List):
        message_chain = MessageChain(message_chain)

    lst = []

    for m in message_chain.as_sendable(msg=msg, embed=False):
        if isinstance(m, Plain):
            lst.append('<div>' + m.text.replace('\n', '<br>') + '</div>')
        elif isinstance(m, Image):
            async with async_open(await m.get(), 'rb') as fi:
                data = await fi.read()
                try:
                    ftt = ft.match(data)
                    lst.append(f'<img src="data:{ftt.mime};base64,{
                               (base64.encodebytes(data)).decode("utf-8")}" width="720" />')
                except Exception:
                    Logger.error(traceback.format_exc())
        elif isinstance(m, Voice):
            lst.append('<div>[Voice]</div>')
        elif isinstance(m, Embed):
            lst.append('<div>[Embed]</div>')

    html_content = env.get_template('msgchain_to_image.html').render(content='\n'.join(lst))
    fname = random_cache_path() + '.html'
    with open(fname, 'w', encoding='utf-8') as fi:
        fi.write(html_content)

    d = {'content': html_content, 'element': '.botbox'}
    html_ = json.dumps(d)

    try:
        pic = await download(webrender('element_screenshot', use_local=use_local),
                             status_code=200,
                             headers={'Content-Type': 'application/json'},
                             method="POST",
                             post_data=html_,
                             attempt=1,
                             timeout=30,
                             request_private_ip=True
                             )
    except aiohttp.ClientConnectorError:
        if use_local:
            pic = await download(webrender('element_screenshot', use_local=False),
                                 status_code=200,
                                 method='POST',
                                 headers={'Content-Type': 'application/json'},
                                 post_data=html_,
                                 request_private_ip=True
                                 )
        else:
            Logger.info('[Webrender] Generation Failed.')
            return False

    with open(pic) as read:
        load_img = json.loads(read.read())
    img_lst = []
    for x in load_img:
        b = base64.b64decode(x)
        bio = BytesIO(b)
        bimg = PILImage.open(bio)
        img_lst.append(bimg)

    return img_lst


async def svg_render(file_path: str, use_local=True) -> Union[List[PILImage], bool]:
    '''使用Webrender渲染svg文件。

    :param file_path: svg文件路径。
    :param use_local: 是否使用本地Webrender渲染。
    :return: 图片的PIL对象。
    '''
    if not WebRender.status:
        return False
    elif not WebRender.local:
        use_local = False

    with open(file_path, 'r') as file:
        svg_content = file.read()

    html_content = env.get_template('svg_template.html').render(svg=svg_content)

    fname = random_cache_path() + '.html'
    with open(fname, 'w', encoding='utf-8') as fi:
        fi.write(html_content)

    d = {'content': html_content, 'element': '.botbox', 'counttime': False}
    html_ = json.dumps(d)

    try:
        pic = await download(webrender('element_screenshot', use_local=use_local),
                             status_code=200,
                             headers={'Content-Type': 'application/json'},
                             method="POST",
                             post_data=html_,
                             attempt=1,
                             timeout=30,
                             request_private_ip=True
                             )
    except aiohttp.ClientConnectorError:
        if use_local:
            pic = await download(webrender('element_screenshot', use_local=False),
                                 status_code=200,
                                 method='POST',
                                 headers={'Content-Type': 'application/json'},
                                 post_data=html_,
                                 request_private_ip=True
                                 )
        else:
            Logger.info('[Webrender] Generation Failed.')
            return False

    with open(pic) as read:
        load_img = json.loads(read.read())

    img_lst = []
    for x in load_img:
        b = base64.b64decode(x)
        bio = BytesIO(b)
        bimg = PILImage.open(bio)
        img_lst.append(bimg)

    return img_lst
