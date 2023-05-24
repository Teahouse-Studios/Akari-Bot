import csv
import os
import re
import shutil
import string
import traceback

import ujson as json

from core.utils.cache import random_cache_path
from core.utils.http import get_url, download_to_cache

assets_path = os.path.abspath('./assets/phigros')
cache_path = os.path.abspath('./cache')
rating_path = os.path.abspath('./assets/phigros/rating.json')
json_url = 'https://raw.githubusercontent.com/ssmzhn/Phigros/main/Phigros.json'

p_headers = {'Accept': 'application/json',
             'X-LC-Id': 'rAK3FfdieFob2Nn8Am',
             'X-LC-Key': 'Qr9AEqtuoSVS3zeD6iVbM4ZC0AtkJcQ89tywVyi0',
             'User-Agent': 'LeanCloud-CSharp-SDK/1.0.3'}


def remove_punctuations(text):
    punctuations = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～、。〃〈〉《》「」『』【】〒〔〕〖〗〘〙〚〛〜・♫☆×♪↑↓ '
    text = ''.join([char for char in text if char not in string.punctuation and char not in punctuations])
    text = re.sub(' +', ' ', text)
    return text.lower()


async def update_assets():
    illustration_path = os.path.join(assets_path, 'illustration')
    if not os.path.exists(illustration_path):
        os.makedirs(illustration_path, exist_ok=True)
    illustration_list = os.listdir(illustration_path)
    file_path = random_cache_path() + '.json'
    data = {}
    update_json = json.loads(await get_url(json_url, 200))
    for song in update_json:
        diff = {}
        for c in update_json[song]['chart']:
            diff[c] = update_json[song]['chart'][c]['difficulty']
        data[remove_punctuations(update_json[song]['song']) + '.' +
             remove_punctuations(update_json[song]['composer'])] = diff

        song_name = remove_punctuations(update_json[song]['song'])
        if song_name not in illustration_list:
            try:
                download_file = await download_to_cache(update_json[song]['illustration'])
                if download_file:
                    shutil.move(download_file, os.path.join(illustration_path, song_name))
            except Exception:
                traceback.print_exc()
    another_assets_url = 'https://github.com/7aGiven/PhigrosLibrary/archive/refs/heads/master.zip'
    download_file = await download_to_cache(another_assets_url)
    if download_file:
        ca = random_cache_path()
        shutil.unpack_archive(download_file, ca)
        shutil.copytree(
            os.path.join(
                ca,
                'PhigrosLibrary-master',
                'illustration'),
            illustration_path,
            dirs_exist_ok=True)

        with open(os.path.join(ca, 'PhigrosLibrary-master', 'difficulty.csv'), 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                data[row[0].lower()] = {'EZ': row[1], 'HD': row[2], 'IN': row[3]}
                if len(row) > 4:
                    data[row[0].lower()]['AT'] = row[4]

        os.remove(download_file)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))
    shutil.move(file_path, rating_path)
    return True
