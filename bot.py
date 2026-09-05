import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.minecraft import Adapter as MCAdapter


nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)
driver.register_adapter(MCAdapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    # host/port 由 .env 的 HOST/PORT 决定，不在此处硬编码（否则会覆盖配置，
    # 导致 Docker/跨机部署时 HOST=0.0.0.0 等设置形同虚设）
    nonebot.run()