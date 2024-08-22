from datetime import datetime

from core.builtins import Bot, Plain
from core.utils.image import msgchain2image
from .chunithm_apidata import get_record
from .chunithm_mapping import *

SONGS_PER_PAGE = 30


def get_diff(diff):
    diff = diff.lower()
    diff_list_lower = [label.lower() for label in diff_list]

    if diff in diff_list_zhs:
        level = diff_list_zhs.index(diff)
    elif diff in diff_list_zht:
        level = diff_list_zht.index(diff)
    elif diff in diff_list_abbr:
        level = diff_list_abbr.index(diff)
    elif diff in diff_list_lower:
        level = diff_list_lower.index(diff)
    else:
        level = None
    return level


async def generate_best30_text(msg: Bot.MessageSession, payload: dict, use_cache: bool = True):
    data = await get_record(msg, payload, use_cache)
    b30_records = data["records"]["b30"]
    r10_records = data["records"]["r10"]

    html = "<style>pre { font-size: 15px; }</style><div style='margin-left: 30px; margin-right: 20px;'>\n"
    html += f"{msg.locale.t('chunithm.message.b30.text_prompt',
                            user=data['username'], rating=round(data['rating'], 2))}\n<pre>"
    html += "Best30\n"
    for idx, chart in enumerate(b30_records, start=1):
        level = ''.join(filter(str.isalpha, chart["level_label"]))[:3].upper()
        rank = next(
            rank for interval, rank in score_to_rate.items() if interval[0] <= chart["score"] < interval[1]  # 根据成绩获得等级
        )
        title = chart["title"]
        title = title[:17] + '...' if len(title) > 20 else title
        line = "#{:<2} {:>4} {:<3} {:>7} {:<4} {:<2} {:>4}->{:<5.2f} {:<20}\n".format(
            idx,
            chart["mid"],
            level,
            chart["score"],
            rank,
            combo_mapping.get(chart["fc"], ""),
            chart["ds"],
            chart["ra"],
            title
        )
        html += line
    html += "Recent10\n"
    for idx, chart in enumerate(r10_records, start=1):
        level = ''.join(filter(str.isalpha, chart["level_label"]))[:3].upper()
        rank = next(
            rank for interval, rank in score_to_rate.items() if interval[0] <= chart["score"] < interval[1]  # 根据成绩获得等级
        )
        title = chart["title"]
        title = title[:17] + '...' if len(title) > 20 else title
        line = "#{:<2} {:>4} {:<3} {:>7} {:<4} {:<2} {:>4}->{:<5.2f} {:<20}\n".format(
            idx,
            chart["mid"],
            level,
            chart["score"],
            rank,
            combo_mapping.get(chart["fc"], ""),
            chart["ds"],
            chart["ra"],
            title
        )
        html += line
    html += "</pre>"
    time = msg.ts2strftime(datetime.now().timestamp(), iso=True, timezone=False)
    html += f"""<p style='font-size: 10px; text-align: right;'>CHUNITHM Best30 Generator Beta\n{
        time}·Generated by Teahouse Studios \"Akaribot\"</p>"""
    html += "</div>"

    img = await msgchain2image([Plain(html)])
    if img:
        return img
    else:
        await msg.finish(msg.locale.t("error.config.webrender.invalid"))
