ZH_NUM_CHAR_DICT = {
    '1': 1, '一': 1, '壹': 1, '幺': 1,
    '2': 2, '二': 2, '俩': 2, '两': 2, '贰': 2,
    '3': 3, '三': 3, '仨': 3, '叁': 3,
    '4': 4, '四': 4, '肆': 4, '亖': 4,
    '5': 5, '五': 5, '伍': 5,
    '6': 6, '六': 6, '陆': 6,
    '7': 7, '七': 7, '柒': 7, '拐': 7,
    '8': 8, '八': 8, '捌': 8,
    '9': 9, '九': 9, '玖': 9, '勾': 9,
    '0': 0, '零': 0, '〇': 0, '洞': 0, 'O': 0, 'o': 0,
}

ZH_NUM_CHAR_DICT2 = {
    '亿': (100000000, True),
    '万': (10000, True),
    '千': (1000, False), '仟': (1000, False),
    '百': (100, False), '佰': (100, False),
    '十': (10, False), '拾': (10, False),
    '个': (1, True)
}


def Zh2Int(chars):
    result = 0
    buffer = 0
    buffer2 = 0
    prev_is_num = False
    if chars == '个':
        return 1
    chars = chars.replace('廿', '二十')
    for c in chars:
        if c in ZH_NUM_CHAR_DICT.keys():
            if prev_is_num:
                buffer *= 10
            buffer += ZH_NUM_CHAR_DICT[c]
            prev_is_num = True
        elif c in ZH_NUM_CHAR_DICT2.keys():
            if ZH_NUM_CHAR_DICT2[c][1]:
                buffer2 += buffer
                result += buffer2 * ZH_NUM_CHAR_DICT2[c][0]
                buffer2 = 0
            else:
                if buffer == 0:
                    buffer = 1
                buffer2 += buffer * ZH_NUM_CHAR_DICT2[c][0]
            buffer = 0
            prev_is_num = False
        else:
            raise ValueError(f"存在无法识别的字符:{c}")
    result += buffer2 + buffer
    return result
