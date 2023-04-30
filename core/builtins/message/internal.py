import re
import uuid
from os.path import abspath
from typing import List
from urllib import parse

import aiohttp
import filetype
from PIL import Image as PImage
from tenacity import retry, stop_after_attempt

from config import CachePath, Config
from core.types.message.internal import Plain as P, Image as I, Voice as V, Embed as E, EmbedField as EF, \
    Url as U, ErrorMessage as EMsg
from core.utils.i18n import Locale


class Plain(P):
    def __init__(self,
                 text, *texts):
        self.text = str(text)
        for t in texts:
            self.text += str(t)

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'Plain(text="{self.text}")'


class Url(U):
    mm = False
    disable_mm = False

    def __init__(self, url: str, use_mm: bool = False, disable_mm: bool = False):
        self.url = url
        if (Url.mm and not disable_mm) or (use_mm and not Url.disable_mm):
            mm_url = f'https://mm.teahouse.team/?source=akaribot&rot13=%s'
            rot13 = str.maketrans(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM")
            self.url = mm_url % parse.quote(parse.unquote(url).translate(rot13))

    def __str__(self):
        return self.url

    def __repr__(self):
        return f'Url(url="{self.url}")'


class ErrorMessage(EMsg):
    def __init__(self, error_message, locale=None):
        self.error_message = error_message
        if locale:
            locale = Locale(locale)
            if locale_str := re.findall(r'\{(.*)}', error_message):
                for l in locale_str:
                    error_message = error_message.replace(f'{{{l}}}', locale.t(l))
            self.error_message = locale.t('error.prompt', error_msg=error_message) + \
                str(Url(Config('bug_report_url')))

    def __str__(self):
        return self.error_message

    def __repr__(self):
        return self.error_message


class Image(I):
    def __init__(self,
                 path, headers=None):
        self.need_get = False
        self.path = path
        self.headers = headers
        if isinstance(path, PImage.Image):
            save = f'{CachePath}{str(uuid.uuid4())}.png'
            path.convert('RGBA').save(save)
            self.path = save
        elif re.match('^https?://.*', path):
            self.need_get = True

    async def get(self):
        if self.need_get:
            return abspath(await self.get_image())
        return abspath(self.path)

    @retry(stop=stop_after_attempt(3))
    async def get_image(self):
        url = self.path
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as req:
                raw = await req.read()
                ft = filetype.match(raw).extension
                img_path = f'{CachePath}{str(uuid.uuid4())}.{ft}'
                with open(img_path, 'wb+') as image_cache:
                    image_cache.write(raw)
                return img_path

    def __str__(self):
        return self.path

    def __repr__(self):
        return f'Image(path="{self.path}", headers={self.headers})'


class Voice(V):
    def __init__(self,
                 path=None):
        self.path = path

    def __str__(self):
        return self.path

    def __repr__(self):
        return f'Voice(path={self.path})'


class EmbedField(EF):
    def __init__(self,
                 name: str = None,
                 value: str = None,
                 inline: bool = False):
        self.name = name
        self.value = value
        self.inline = inline

    def __str__(self):
        return f'{self.name}: {self.value}'

    def __repr__(self):
        return f'EmbedField(name="{self.name}", value="{self.value}", inline={self.inline})'


class Embed(E):
    def __init__(self,
                 title: str = None,
                 description: str = None,
                 url: str = None,
                 timestamp: float = None,
                 color: int = None,
                 image: Image = None,
                 thumbnail: Image = None,
                 author: str = None,
                 footer: str = None,
                 fields: List[EmbedField] = None):
        self.title = title
        self.description = description
        self.url = url
        self.timestamp = timestamp
        self.color = color
        self.image = image
        self.thumbnail = thumbnail
        self.author = author
        self.footer = footer
        self.fields = fields

    def to_msgchain(self):
        text_lst = []
        if self.title is not None:
            text_lst.append(self.title)
        if self.description is not None:
            text_lst.append(self.description)
        if self.url is not None:
            text_lst.append(self.url)
        if self.fields is not None:
            for f in self.fields:
                if f.inline:
                    text_lst.append(f"{f.name}: {f.value}")
                else:
                    text_lst.append(f"{f.name}:\n{f.value}")
        if self.author is not None:
            text_lst.append("作者：" + self.author)
        if self.footer is not None:
            text_lst.append(self.footer)
        msgchain = []
        if text_lst:
            msgchain.append(Plain('\n'.join(text_lst)))
        if self.image is not None:
            msgchain.append(self.image)
        return msgchain

    def __str__(self):
        return str(self.to_msgchain())

    def __repr__(self):
        return f'Embed(title="{self.title}", description="{self.description}", url="{self.url}", ' \
               f'timestamp={self.timestamp}, color={self.color}, image={self.image.__repr__()}, ' \
               f'thumbnail={self.thumbnail.__repr__()}, author="{self.author}", footer="{self.footer}", ' \
               f'fields={self.fields})'


__all__ = ["Plain", "Image", "Voice", "Embed", "EmbedField", "Url", "ErrorMessage"]
