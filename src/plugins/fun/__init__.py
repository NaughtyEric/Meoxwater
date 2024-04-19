# 花里胡哨的东西想到了就加进来

from nonebot import on_keyword
import time

good_night = on_keyword({'晚安', '晚安啦', '晚安了'}, priority=5)
good_morning = on_keyword({'早上好', '早安'}, priority=5)

@good_night.handle()
async def _(bot, event):
    t = time.localtime()
    # 如果是在晚上十点到十二点之间，就回复晚安
    if 22 <= t.tm_hour < 24:
        await good_night.finish('晚安喵，愿你的梦境不受梦魇侵扰~')
    # 如果是在凌晨0点到6点之间，就回复晚安
    elif 0 <= t.tm_hour < 6:
        await good_night.finish('把细碎的烦恼暂时关掉，把月亮挂好睡个好觉。虽然已经夜深人静，还是要祝你做个好梦喵~')
    else:
        await good_night.finish('啊……呃，晚安……喵？')

@good_morning.handle()
async def _(bot, event):
    t = time.localtime()
    if 5 <= t.tm_hour < 10:
        await good_morning.finish('早上好，新的一天也要活力满满喵~')
    elif 10 <= t.tm_hour < 17:
        await good_morning.finish('（戳表）这都几点了喵！还在早安？起床，起床喵！')
    else:
        await good_morning.finish('早上好……喵？（陷入思考）（死机）')
