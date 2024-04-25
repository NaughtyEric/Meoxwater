import json
import os
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot import message
from .MsgManager import MsgManager


# Listen


class AntiRecall:
    DEFAULT_CONFIG = {
        "activated": True,
        "activated_groups": [],
        "cache_expire": 240,
        "data_expire": 2,
        "admins": []
    }

    def __init__(self, file_path, data_path):
        if not os.path.exists(file_path):
            # 尝试创建文件
            try:
                with open(file_path, "w") as f:
                    f.write(json.dumps(self.DEFAULT_CONFIG, indent=4))
            except Exception as e:
                raise FileNotFoundError("AntiRecall无法创建配置文件。")

        if not os.path.exists(data_path):
            os.makedirs(data_path)

        with open(file_path, "r") as f:
            config = json.load(f)
        self.activated = config["activated"]
        self.manager = MsgManager(cache_expire=config["cache_expire"], data_expire=config["data_expire"]
                                  , data_path=data_path)
        self.activated_groups = config["activated_groups"]
        self.admins = config["admins"]
        self.ignore_list = config["ignore"]
        # 启动periodic_clean_cache
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._periodic_clean_cache, 'interval', minutes=30)
        self.scheduler.start()

    def group_activated(self, group_id: int) -> bool:
        if self.activated and group_id in self.activated_groups:
            return True
        return False

    def add_message(self, msg_time, msg_sender, msg):
        if not self.activated:
            return
        if msg_sender not in self.ignore_list:
            self.manager.add_msg_cache(msg_time, msg_sender, msg)

    def _periodic_clean_cache(self):
        self.manager.remove_expired_cache()
        self.manager.remove_expired_data()

    def msg_query(self, msg_time, operator_id, usr_id):
        if not self.activated:
            return None
        if operator_id in self.admins:
            return self.manager.get_msg_by_usr(msg_time, usr_id)
        return None

    def __del__(self):
        self.scheduler.shutdown()





