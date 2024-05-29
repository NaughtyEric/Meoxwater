# 从.env中读取mysql配置，链接数据库
import nonebot.adapters
from nonebot.matcher import Matcher
from nonebot.internal.params import ArgPlainText
from nonebot.params import CommandArg

from .database import Database
from nonebot import get_driver, logger, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
import nonebot.adapters.mirai as mirai

global_config = get_driver().config
MYSQL_URL = None
MYSQL_USER = None
MYSQL_PASSWORD = None
DB = Database()

caramel_cup = on_command("ccup", priority=5)

temp_mute = on_command("ccup", priority=2, block=True)
@temp_mute.handle()
async def _(bot: Bot, event: MessageEvent):
    await temp_mute.finish()  # 暂时禁用焦糖杯插件


@get_driver().on_startup
async def on_startup():
    global MYSQL_URL, MYSQL_USER, MYSQL_PASSWORD, DB
    logger.info("正在加载焦糖杯插件...")
    error_msg = ""
    if not global_config.mysql_url:
        error_msg += ", mysql_url"
    if not global_config.mysql_user:
        error_msg += ", mysql_user"
    if not global_config.mysql_password:
        error_msg += ", mysql_password"
    if error_msg:
        logger.error(f"缺少配置项{error_msg}未配置")

    MYSQL_URL = str(global_config.mysql_url)
    MYSQL_USER = str(global_config.mysql_user)
    MYSQL_PASSWORD = str(global_config.mysql_password)
    try:
        DB = Database(url=MYSQL_URL, user=MYSQL_USER, password=MYSQL_PASSWORD)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return
    logger.info("焦糖杯插件加载完成")


@get_driver().on_shutdown
async def on_shutdown():
    global DB
    if DB:
        del DB
        DB = None
        logger.info("焦糖杯插件卸载完成")


@caramel_cup.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    logger.debug("step 1")
    if args.extract_plain_text():
        matcher.set_arg("operation", args)


@caramel_cup.got("operation", prompt="请问你需要我帮你做什么呢？")
async def _(bot: Bot, event: MessageEvent, operation: str = ArgPlainText()):
    logger.debug(f"operation: {operation}")
    global DB
    if not DB:
        await caramel_cup.finish("焦糖杯相关插件加载失败，请联系管理员。")
        return
    operation = operation.strip()
    DB.remove_expired_captcha()
    if operation in ['注册', 'register', 'reg']:
        check_if_already_registered = DB.execute("SELECT * FROM users WHERE qid = %s", (event.get_user_id(),))
        check_if_in_register_procedure = DB.execute("SELECT * FROM participant WHERE qid = %s", (event.get_user_id(),))
        logger.debug(f"check_if_already_registered: {check_if_already_registered}, "
                     f"check_if_in_register_procedure: {check_if_in_register_procedure}")

        if check_if_already_registered:
            await caramel_cup.pause("你已经注册过了。是否需要重置密码？发送“是”以确认，发送其他内容以取消。")
        elif check_if_in_register_procedure:
            await caramel_cup.pause("你已经在注册流程中了。是否需要重置captcha？发送“是”以确认，发送其他内容以取消。")
        else:
            try:
                message = f"您的captcha是：\n{DB.gen_captcha(event.get_user_id(), False)}\n请登录焦糖杯网站进行注册。"
                await bot.send_temp_message(group=event.group_id, target=int(event.get_user_id()), message=message)
            except Exception as e:
                logger.error(f"发送私聊消息失败: {e}")
                DB.rollback()
                await caramel_cup.finish("发送私聊消息失败。")
            else:
                DB.commit()
                await caramel_cup.finish("为你发送了一条私聊消息，请查收。")
    else:
        await caramel_cup.finish("不支持的操作。")


@caramel_cup.handle()
async def _(bot: mirai.Bot, event: MessageEvent):
    logger.debug("step 3")
    if event.message.extract_plain_text() == "是":
        await bot.send_private_msg(user_id=int(event.get_user_id()),
                                   message=f"您的captcha是：\n{DB.gen_captcha(event.get_user_id(), True)}\n"
                                           f"\n请登录焦糖杯网站进行注册。")
        await caramel_cup.finish("为你发送了一条私聊消息，请查收。")
    else:
        await caramel_cup.finish("操作已取消。")
