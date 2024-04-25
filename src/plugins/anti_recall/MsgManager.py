import time
import datetime
import os
import nonebot
import re


class MsgManager:
    @staticmethod
    def get_filename(t: datetime.datetime):
        # [0, 4) hours -> 0
        # [4, 8) hours -> 1  as follows
        return f"msg_record_{t.year}_{t.month:02}_{t.day}_{t.hour // 4}.txt"

    @staticmethod
    def get_datetime(s: str):
        t = datetime.datetime.strptime(s, "msg_record_%Y_%m_%d_%H.txt")
        t = t.replace(hour=t.hour * 4)
        return t

    current_opening_file_name = ""
    current_opening_file = None

    def __init__(self, cache_expire, data_expire, data_path):
        cache_expire = (cache_expire + 59) // 60  # round up to the nearest minute
        self.cache_expire = cache_expire  # 单位：分钟
        self.data_expire = data_expire  # 单位：天
        self.data_path = data_path
        self.start_time = time.time()
        self.start_time = datetime.datetime.fromtimestamp(self.start_time)
        self.start_time.replace(second=0, microsecond=0)  # remove seconds and microseconds
        self.cache = {}

        self.current_opening_file_name = self.get_filename(self.start_time)
        try:
            self.current_opening_file = open(self.data_path + self.current_opening_file_name, "a")
        except Exception as e:
            nonebot.logger.error(f"无法打开文件{self.data_path + self.current_opening_file_name}，错误：{e}")

    def get_chunking_index(self, _time: datetime.datetime):
        if _time < self.start_time:
            return 0
        return (_time - self.start_time).seconds // (self.cache_expire * 60)

    def add_msg_cache(self, _time: datetime.datetime, sender_id: int, message):
        index = self.get_chunking_index(_time)
        if index not in self.cache:
            self.cache[index] = []
        self.cache[index].append((_time, sender_id, message))
        nonebot.logger.debug(f"消息{message}压入缓存{index}")

    def get_msg_by_usr(self, _time: datetime.datetime, user_id: int):
        begin_index = self.get_chunking_index(_time)
        end_index = self.get_chunking_index(datetime.datetime.fromtimestamp(time.time()))
        earliest_index_in_cache = min(self.cache.keys()) if len(self.cache) > 0 else 0
        nonebot.logger.debug(f"查询用户{user_id}的消息，缓存段为{begin_index}到{end_index}。")
        ret = []
        for i in range(max(begin_index, earliest_index_in_cache), end_index + 1):
            if i in self.cache:
                for t, sender, msg in self.cache[i]:
                    # nonebot.logger.debug(f"消息 {msg} 的发送者为{sender}。")
                    if str(sender) == str(user_id):
                        ret.append(f"[{t}] {msg}")

        # 将剩余的时间段从文件里读取
        # [2024-04-25 15:16:54] 2130985791: ...
        re_str = re.compile("\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})] (\d+): (.+)")
        for filename in os.listdir(self.data_path):
            nonebot.logger.debug(f"读取文件{filename}")
            t_file = self.get_datetime(filename)
            if t_file + datetime.timedelta(hours=4) < _time:
                nonebot.logger.debug(f"文件{filename}时间为{t_file}，早于{_time}，跳过")
                continue

            with open(self.data_path + filename, "r") as f:
                for line in f.readlines():
                    nonebot.logger.debug(f"读取文件{filename}：{line}")
                    match = re_str.match(line)
                    if match:
                        t, sender, msg = match.groups()
                        if str(sender) == str(user_id) and datetime.datetime.strptime(
                                t, "%Y-%m-%d %H:%M:%S") >= _time:
                            ret.append(line.strip())

        return "\n".join(ret)

    def remove_expired_cache(self):
        if self.current_opening_file_name != self.get_filename(self.start_time):
            self.current_opening_file.close()
            self.current_opening_file_name = self.get_filename(self.start_time)
            try:
                self.current_opening_file = open(self.data_path + self.current_opening_file_name, "a")
                nonebot.logger.debug(f"打开新文件{self.current_opening_file_name}")
            except Exception as e:
                nonebot.logger.error(f"无法打开文件{self.data_path + self.current_opening_file_name}，错误：{e}")

        expire_line = datetime.datetime.fromtimestamp(time.time()) - datetime.timedelta(minutes=self.cache_expire)
        chunk = self.get_chunking_index(expire_line)
        nonebot.logger.debug(f"删除缓存{chunk}之前的缓存")
        for i in range(chunk):
            if i in self.cache:
                for t, sender, msg in self.cache[i]:
                    self.current_opening_file.write(f"[{t}] {sender}: {msg}\n")
                    nonebot.logger.debug(f"写入文件{self.current_opening_file_name}：[{t}] {sender}: {msg}")
                del self.cache[i]

    def remove_all_cache(self):
        for i in self.cache:
            for t, sender, msg in self.cache[i]:
                self.current_opening_file.write(f"[{t}] {sender}: {msg}\n")
                nonebot.logger.debug(f"写入文件{self.current_opening_file_name}：[{t}] {sender}: {msg}")
        self.cache.clear()
        self.current_opening_file.flush()

    def remove_expired_data(self):
        files = os.listdir(self.data_path)
        for filename in files:
            t = self.get_datetime(filename)
            nonebot.logger.debug(f"文件{filename}的时间为{t}")
            if (datetime.datetime.now() - t) > datetime.timedelta(days=self.data_expire):
                os.remove(self.data_path + filename)
                nonebot.logger.debug(f"删除过期文件{filename}")

    def getMsgCache(self):
        return self.cache

    def __del__(self):
        # 关闭文件
        for i in self.cache:
            for t, sender, msg in self.cache[i]:
                self.current_opening_file.write(f"[{t}] {sender}: {msg}\n")
                nonebot.logger.debug(f"写入文件{self.current_opening_file_name}：[{t}] {sender}: {msg}")
        self.current_opening_file.flush()
        self.current_opening_file.close()



