#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步工具 - 将Web localStorage数据同步到Python
运行此脚本后，可以通过命令行查看Web端记录的进度
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent
PROGRESS_FILE = DATA_DIR / "progress.json"
DAILY_FILE = DATA_DIR / "daily.json"
GOALS_FILE = DATA_DIR / "goals.json"


def export_for_web():
    progress = {}
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    
    daily = {}
    if DAILY_FILE.exists():
        with open(DAILY_FILE, 'r', encoding='utf-8') as f:
            daily = json.load(f)
    
    goals = {"weekday": 3, "weekend": 8}
    if GOALS_FILE.exists():
        with open(GOALS_FILE, 'r', encoding='utf-8') as f:
            goals = json.load(f)
    
    print("Python端数据已准备好")
    print(f"进度记录: {len(progress)} 题")
    print(f"日期记录: {len(daily)} 天")
    return progress, daily, goals


def import_from_web(progress_json: str, daily_json: str, goals_json: str = None):
    try:
        progress = json.loads(progress_json) if progress_json else {}
        daily = json.loads(daily_json) if daily_json else {}
        
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        
        with open(DAILY_FILE, 'w', encoding='utf-8') as f:
            json.dump(daily, f, ensure_ascii=False, indent=2)
        
        if goals_json:
            goals = json.loads(goals_json)
            with open(GOALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(goals, f, ensure_ascii=False, indent=2)
        
        print("✓ 数据已从Web同步到Python")
        return True
    except Exception as e:
        print(f"✗ 同步失败: {e}")
        return False


if __name__ == '__main__':
    print("""
数据同步说明
============

Web端数据存储在浏览器的localStorage中，Python端存储在JSON文件中。

从Web导出数据到Python:
1. 在浏览器中打开 dashboard.html
2. 打开浏览器开发者工具 (F12)
3. 在Console中执行:
   console.log('progress:', localStorage.getItem('leetcode_progress'));
   console.log('daily:', localStorage.getItem('leetcode_daily'));
   console.log('goals:', localStorage.getItem('leetcode_goals'));
4. 将输出的JSON数据保存到对应的文件

从Python导入数据到Web:
1. 确保 progress.json 和 daily.json 文件存在
2. 在浏览器Console中执行:
   localStorage.setItem('leetcode_progress', '进度JSON内容');
   localStorage.setItem('leetcode_daily', '日期JSON内容');
   localStorage.setItem('leetcode_goals', '目标JSON内容');
3. 刷新页面

注意: 建议主要使用Web界面，数据会自动保存在浏览器中。
    """)
    
    export_for_web()
