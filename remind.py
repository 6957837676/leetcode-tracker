#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信提醒刷题工具 - 使用Server酱推送 (免费)
"""

import json
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent
PROGRESS_FILE = DATA_DIR / "progress.json"
DAILY_FILE = DATA_DIR / "daily.json"

SERVERCHAN_KEY = "SCT331462TooDHBMsoiARnujWYAHtJKgxN"

def get_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_daily():
    if DAILY_FILE.exists():
        with open(DAILY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_today_done():
    daily = get_daily()
    today = datetime.now().strftime('%Y-%m-%d')
    return len(daily.get(today, []))

def send_wechat_message(title, content):
    if not SERVERCHAN_KEY:
        print("请先设置Server酱 SendKey")
        return False
    
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {
        "title": title,
        "desp": content
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        if result.get('code') == 0:
            print("微信提醒发送成功")
            return True
        else:
            print(f"发送失败: {result.get('message')}")
            return False
    except Exception as e:
        print(f"发送异常: {e}")
        return False

def remind_daily():
    progress = get_progress()
    daily = get_daily()
    today = datetime.now().strftime('%Y-%m-%d')
    
    total_done = len(progress)
    today_done = len(daily.get(today, []))
    goal = 3
    remain = goal - today_done
    
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday = weekday_names[datetime.now().weekday()]
    
    if today_done >= goal:
        title = "🎉 今日刷题目标已完成！"
        content = f"""
## 恭喜！今日目标已达成

📅 {datetime.now().strftime('%Y年%m月%d日')} {weekday}

✅ 今日完成: **{today_done}** 题

📊 累计完成: **{total_done}** 题

继续保持，明天继续加油！💪
        """
    else:
        title = f"📚 今日刷题提醒 (已完成{today_done}/{goal}题)"
        content = f"""
## 刷题提醒

📅 {datetime.now().strftime('%Y年%m月%d日')} {weekday}

✅ 今日完成: **{today_done}** 题

🎯 今日目标: **{goal}** 题

⏳ 还需完成: **{remain}** 题

📊 累计完成: **{total_done}** 题

---

💡 **点击下方链接开始刷题：**

[打开刷题面板](http://localhost:8080)

加油！坚持就是胜利！💪
        """
    
    send_wechat_message(title, content)

def remind_morning():
    title = "🌅 早安！今日刷题任务待完成"
    content = f"""
## 早安提醒

📅 {datetime.now().strftime('%Y年%m月%d日')}

🎯 今日目标: **3** 题

⏰ 别忘了今天的刷题任务哦！

[点击开始刷题](http://localhost:8080)
    """
    send_wechat_message(title, content)

def remind_evening():
    today_done = get_today_done()
    if today_done < 3:
        title = "🌙 晚间提醒：今日刷题未完成"
        content = f"""
## 晚间提醒

📅 {datetime.now().strftime('%Y年%m月%d日')}

✅ 今日完成: **{today_done}** 题

🎯 今日目标: **3** 题

⏳ 还差: **{3 - today_done}** 题

睡前再来刷几题吧！💪

[点击继续刷题](http://localhost:8080)
        """
        send_wechat_message(title, content)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'morning':
            remind_morning()
        elif cmd == 'evening':
            remind_evening()
        elif cmd == 'now':
            remind_daily()
        elif cmd == 'test':
            if len(sys.argv) > 2:
                SERVERCHAN_KEY = sys.argv[2]
            send_wechat_message("测试消息", "这是一条测试消息，如果你收到说明配置成功！")
    else:
        remind_daily()
