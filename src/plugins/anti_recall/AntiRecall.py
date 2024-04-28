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
        self.scheduler = None
        self.ignore_list = None
        self.admins = None
        self.activated_groups = None
        self.manager = None
        self.activated = None
        self.file_path = file_path
        self.data_path = data_path
        self.reload_config()

    def reload_config(self):
        if not os.path.exists(self.file_path):
            # 尝试创建文件
            try:
                with open(self.file_path, "w") as f:
                    f.write(json.dumps(self.DEFAULT_CONFIG, indent=4))
            except Exception as e:
                raise FileNotFoundError("AntiRecall无法创建配置文件。")

        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        with open(self.file_path, "r") as f:
            config = json.load(f)
        self.activated = config["activated"]
        self.manager = MsgManager(cache_expire=config["cache_expire"], data_expire=config["data_expire"]
                                  , data_path=self.data_path)
        self.activated_groups = config["activated_groups"]
        self.admins = config["admins"]
        self.ignore_list = config["ignore"]
        # 启动periodic_clean_cache
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._periodic_clean_cache, 'interval', minutes=30)
        self.scheduler.start()

    def group_activated(self, group_id: int) -> bool:
        """
        判断群组是否激活
        :param group_id: 群组id，即群号
        :return: bool，仅在激活状态下返回True
        """
        if self.activated and group_id in self.activated_groups:
            return True
        return False

    def add_message(self, msg_time, msg_sender, msg):
        """
        添加消息到缓存
        :param msg_time: 消息的时间，使用datetime.datetime.fromtimestamp()生成
        :param msg_sender: 消息发送者的qq号
        :param msg: 消息内容，str
        """
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





