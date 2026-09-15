from pydantic import BaseModel


class Config(BaseModel, extra="ignore"):
    """Plugin Config Here"""

    # 服务器列表配置文件，见 assets/mc_bridge/servers.json
    mc_bridge_config_filepath: str = "./assets/mc_bridge/servers.json"
    # QQ -> MC 单条消息最大长度，超出部分截断
    mc_msg_max_length: int = 200
