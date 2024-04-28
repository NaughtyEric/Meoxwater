from nonebot import get_driver
import os, datetime
from nonebot import on_notice, on_command
from nonebot.log import logger
from nonebot.rule import is_type
from nonebot.params import CommandArg

from nonebot.adapters.onebot.v11 import Bot, GroupRecallNoticeEvent, PrivateMessageEvent, Message
from .AntiRecall import AntiRecall

driver = get_driver()

__plugin_name__ = 'anti_recall'
anti_recall: AntiRecall

@driver.on_startup
async def on_startup():
    global anti_recall
    if not os.path.exists('./config'):
        os.makedirs('./config')
    anti_recall = AntiRecall('./config/anti_recall.json', "./datamsg_record/")


recall = on_notice()
@recall.handle()
async def recall_handle(bot: Bot, event: GroupRecallNoticeEvent):
    global anti_recall
    if not (isinstance(anti_recall, AntiRecall) and anti_recall.activated):  # 只有在激活状态下才会执行
        return
    if str(event.user_id) != str(bot.self_id):
        mid = event.message_id
        gid = event.group_id
        uid = event.user_id
        oid = event.operator_id
        tid = datetime.datetime.fromtimestamp(event.time)
        response = await bot.get_msg(message_id=mid)
        logger.debug(f'{oid}撤回了{uid}在{gid}的消息{response["message"]}')
        if anti_recall.group_activated(gid):
            try:
                msg = response['message']
                anti_recall.add_message(tid, uid, msg)
            except Exception as e:
                logger.debug(f'群组监听失败，错误：{e}')


query = on_command('arq', aliases={"反撤回"}, rule=is_type(PrivateMessageEvent))
@query.handle()
async def query_handle(event: PrivateMessageEvent, args: Message = CommandArg()):
    global anti_recall
    if not (isinstance(anti_recall, AntiRecall) and anti_recall.activated):
        return
    if event.user_id not in anti_recall.admins:
        await query.finish('权限不足')
        return
    uid = event.user_id
    t = datetime.datetime.now() - datetime.timedelta(hours=1)
    if args:
        if len(args) == 1:
            # 只有一个查询目标qq号
            ret = anti_recall.msg_query(t, uid, args[0])
            if ret:
                await query.finish('最近一小时内的发言：\n' + ret)
            else:
                await query.finish('查询失败')
        elif len(args) == 2:
            # 两个参数，第一个是查询目标qq号，第二个是查询时间
            ret = anti_recall.msg_query(args[1], uid, args[0])
            if ret:
                await query.finish(ret)
            else:
                await query.finish('查询失败')
        else:
            await query.finish('参数错误')
    else:
        await query.finish('参数错误')

force_refresh = on_command('arfr', rule=is_type(PrivateMessageEvent))

@force_refresh.handle()
async def force_refresh_handle(event: PrivateMessageEvent):
    global anti_recall
    if not (isinstance(anti_recall, AntiRecall) and anti_recall.activated):
        return
    if event.user_id not in anti_recall.admins:
        await force_refresh.finish('权限不足')
        return
    anti_recall.manager.remove_all_cache()
    anti_recall.manager.remove_expired_data()
    anti_recall.reload_config()
    await force_refresh.finish('重载完成')


