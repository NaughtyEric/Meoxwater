from pydantic import BaseModel


class Config(BaseModel, extra="ignore"):
    """Plugin Config Here"""

    # 互通的服务器名，需与鹊桥 config.yml 的 server_name 完全一致
    mc_server_name: str = ""
    # 与该服务器互通的 QQ 群号
    mc_groups: list[int] = []

    # MC -> QQ 各类事件开关
    mc_sync_chat: bool = True
    mc_sync_join: bool = True
    mc_sync_quit: bool = True
    mc_sync_death: bool = True
    mc_sync_achievement: bool = True

    # QQ -> MC 单条消息最大长度，超出部分截断
    mc_msg_max_length: int = 200
