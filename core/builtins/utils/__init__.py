import os

confirm_command = ["是", "对", '确定', '是吧', '大概是',
                   '也许', '可能', '对的', '是呢', '对呢', '嗯', '嗯呢', '对啊', '是啊'
                   '吼啊', '资瓷', '是呗', '也许吧', '对呗', '应该', '是呢', '是哦'
                   "對", '確定', '對的', '對啊', '對呢', '對唄', '資瓷', '是唄', '也許', '也許吧', '應該',
                   'yes', 'y', 'yeah', 'yep', 'ok', 'okay', '⭐', '√']

command_prefix = ['~', '～']  # 消息前缀


class EnableDirtyWordCheck:
    status = False


class PrivateAssets:
    path = os.path.abspath('.')

    @staticmethod
    def set(path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.mkdir(path)
        PrivateAssets.path = path


class Secret:
    list = []

    @staticmethod
    def add(secret):
        Secret.list.append(secret)


__all__ = ["confirm_command", "command_prefix", "EnableDirtyWordCheck", "PrivateAssets", "Secret"]
