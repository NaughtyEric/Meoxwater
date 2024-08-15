from typing import Union, Any
import utils
import datetime
import os
import ast
from pathlib import Path
from nonebot.adapters import Bot
from nonebot.log import logger


class GlobalManager:
    """
    全局插件管理
    """

    def __init__(self, bot: Bot, base_path: Union[str, Path]):
        self.bot = bot
        self._managers = {}  # 群管理器字典
        self.path: Path = Path(base_path)
        pass

    def init_from_group(self, group_id):
        """
        从群号初始化一个群管理器。
        :param group_id: 群号
        :return: 群管理器
        """
        if group_id in self._managers.keys():
            return self._managers[group_id]
        else:
            self._managers[group_id] = GroupManager(group_id, self)
            return self._managers[group_id]


class GroupManager:
    """
    为单独的群进行管理。
    """

    def __init__(self, group_id, global_manager: GlobalManager):
        self.group_id = group_id  # 群号
        self.latest_update = datetime.datetime(1970, 1, 1)  # 最近一次更新时间
        self.pernament_pairs = {}  # 永久对
        self.temp_pairs = {}  # 随机匹配的群员
        self.global_manager = global_manager
        self.read_form_local()

    def _refresh(self):
        """
        刷新今日老婆，如果时间戳表明已过刷新时间，则解除所有随机对。北京时间4点刷新。
        """
        cur_time = datetime.datetime.now()
        if cur_time.hour >= 4 and self.latest_update.day != cur_time.day:
            self.temp_pairs.clear()
            self.latest_update = cur_time

    def add_pernament_pairs(self, qid1: int, qid2: int):
        """
        添加一组永久对。这项操作会解绑二人今日的随机匹配，并使未来的查询总是查到他们二人。
        :param qid1: 成员1的qq号
        :param qid2: 成员2的qq号
        :return: 字符串，表示本次操作的响应。
        """

        # 移除原有关系
        if qid1 in self.temp_pairs.keys():
            p_qid1 = self.temp_pairs[qid1]
            self.temp_pairs.pop(p_qid1)
            self.temp_pairs.pop(qid1)
        if qid2 in self.temp_pairs.keys():
            p_qid2 = self.temp_pairs[qid1]
            self.temp_pairs.pop(p_qid2)
            self.temp_pairs.pop(qid2)

        if qid1 in self.pernament_pairs.keys() or qid2 in self.pernament_pairs.keys():
            return "操作失败：至少有一方已经存在长期关系。"

        self.pernament_pairs[qid1] = qid2
        self.pernament_pairs[qid2] = qid1
        return "操作成功。"

    def remove_user_relationships(self, qid: int):
        """
        解除一个用户已存在的关系。这个操作会使用户立刻解除所有现存关系，包括临时/永久。
        :param qid: 要操作的用户的qq号。
        """
        if qid in self.temp_pairs.keys():
            self.temp_pairs.pop(qid)
        if qid in self.pernament_pairs.keys():
            self.pernament_pairs.pop(qid)

    def find_wife(self, qid: int) -> int:
        """
        找到该群友的今日老婆。如果没有，随机分配一个。
        :param qid: 群友qq号
        :return: 老婆qq号
        """
        p_qid = self.pernament_pairs.get(qid, -1)
        if p_qid != -1:  # 拥有永久关系
            return p_qid
        else:
            self._refresh()
            p_qid = self.temp_pairs.get(qid, -1)
            if p_qid == -1 or p_qid not in self.global_manager.bot.get_group_member_list(group_id=self.group_id):
                # TODO: 如果qid不存在/已退群，分配一个新的
                pass
            else:
                return p_qid

    def _get_wife(self, qid: int) -> int:
        """
        给指定群友分配一个老婆。

        **该操作不会检测合法性，即：不会删除已有关系，请注意。**
        :param qid: 群友qq号
        :return: 老婆qq号
        """
        self._refresh()
        p_qid = self.temp_pairs.get(qid, -1)
        return 1

    def read_form_local(self):
        """
        从本地文件读取本群的信息，文件名格式为:"群号.txt"
        """
        baseP = self.global_manager.path
        if not baseP.exists() or not (baseP / f"{self.group_id}.txt").exists():  # 不存在文件，不读取
            logger.warning(f"群{self.group_id}的信息文件不存在。")
            return
        with open(baseP / f"{self.group_id}.txt", "r") as f:
            self.latest_update = datetime.datetime.fromisoformat(f.readline())
            self.pernament_pairs = ast.literal_eval(f.readline())
            self.temp_pairs = ast.literal_eval(f.readline())
            logger.debug(f"群{self.group_id}的信息已读取，上次更新时间为{self.latest_update}，"
                         f"本次读取了{len(self.pernament_pairs)}对永久对和{len(self.temp_pairs)}对临时对。")

    def write_to_local(self, path: Union[str, Path]):
        """
        将本群的信息保存在文件中，文件名格式为:"群号.txt"
        """
        baseP = self.global_manager.path
        if not baseP.exists():
            baseP.mkdir()
        with open(baseP / f"{self.group_id}.txt", "w") as f:
            f.write(f"{self.latest_update}\n")
            f.write(f"{self.pernament_pairs}\n")
            f.write(f"{self.temp_pairs}\n")
