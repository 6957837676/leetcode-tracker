#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeetCode 刷题进度管理工具
支持命令行操作和启动Web仪表板
"""

import json
import os
import webbrowser
import http.server
import socketserver
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent
PROBLEMS_FILE = DATA_DIR / "problems.json"
PROGRESS_FILE = DATA_DIR / "progress.json"
DAILY_FILE = DATA_DIR / "daily.json"


def load_json(file_path: Path) -> dict:
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_json(file_path: Path, data: dict):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_problem_key(problem: dict) -> str:
    return f"{problem['id']}_{problem['name']}"


def load_problems() -> dict:
    return load_json(PROBLEMS_FILE)


def load_progress() -> dict:
    return load_json(PROGRESS_FILE)


def save_progress(progress: dict):
    save_json(PROGRESS_FILE, progress)


def load_daily() -> dict:
    return load_json(DAILY_FILE)


def save_daily(daily: dict):
    save_json(DAILY_FILE, daily)


def get_all_problems() -> List[dict]:
    problems = []
    data = load_problems()
    for tier in data.get('tiers', []):
        for module in tier.get('modules', []):
            for problem in module.get('problems', []):
                problems.append({
                    **problem,
                    'tier': tier['name'],
                    'module': module['name']
                })
    return problems


def mark_completed(problem_id: int or str, name: str = None):
    progress = load_progress()
    daily = load_daily()
    problems = get_all_problems()
    
    target = None
    for p in problems:
        if str(p['id']) == str(problem_id):
            if name is None or p['name'] == name:
                target = p
                break
    
    if not target:
        print(f"未找到题目: {problem_id}")
        return False
    
    key = get_problem_key(target)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if progress.get(key):
        print(f"题目 {target['id']}. {target['name']} 已经完成")
        return True
    
    progress[key] = True
    save_progress(progress)
    
    if today not in daily:
        daily[today] = []
    daily[today].append(key)
    save_daily(daily)
    
    print(f"✓ 已完成: {target['id']}. {target['name']} ({target['difficulty']})")
    return True


def unmark_completed(problem_id: int or str):
    progress = load_progress()
    daily = load_daily()
    problems = get_all_problems()
    
    target = None
    for p in problems:
        if str(p['id']) == str(problem_id):
            target = p
            break
    
    if not target:
        print(f"未找到题目: {problem_id}")
        return False
    
    key = get_problem_key(target)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if key in progress:
        del progress[key]
        save_progress(progress)
    
    if today in daily and key in daily[today]:
        daily[today].remove(key)
        save_daily(daily)
    
    print(f"✗ 已取消: {target['id']}. {target['name']}")
    return True


def show_stats():
    problems = get_all_problems()
    progress = load_progress()
    daily = load_daily()
    
    total = len(problems)
    completed = sum(1 for p in problems if progress.get(get_problem_key(p)))
    
    print("\n" + "="*50)
    print("📊 刷题进度统计")
    print("="*50)
    print(f"总题数: {total}")
    print(f"已完成: {completed}")
    print(f"剩余: {total - completed}")
    print(f"完成率: {completed/total*100:.1f}%")
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = len(daily.get(today, []))
    print(f"\n今日完成: {today_count} 题")
    
    print("\n按难度统计:")
    difficulty_stats = {}
    for p in problems:
        diff = p['difficulty']
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {'total': 0, 'completed': 0}
        difficulty_stats[diff]['total'] += 1
        if progress.get(get_problem_key(p)):
            difficulty_stats[diff]['completed'] += 1
    
    for diff, stats in sorted(difficulty_stats.items(), key=lambda x: ['简单', '中等', '困难'].index(x[0]) if x[0] in ['简单', '中等', '困难'] else 99):
        percent = stats['completed'] / stats['total'] * 100
        bar = '█' * int(percent / 5) + '░' * (20 - int(percent / 5))
        print(f"  {diff}: {bar} {stats['completed']}/{stats['total']} ({percent:.0f}%)")
    
    print("\n按梯队统计:")
    data = load_problems()
    for i, tier in enumerate(data.get('tiers', [])):
        tier_completed = 0
        tier_total = 0
        for module in tier.get('modules', []):
            for p in module.get('problems', []):
                tier_total += 1
                if progress.get(get_problem_key(p)):
                    tier_completed += 1
        percent = tier_completed / tier_total * 100 if tier_total > 0 else 0
        bar = '█' * int(percent / 5) + '░' * (20 - int(percent / 5))
        print(f"  第{i+1}梯队: {bar} {tier_completed}/{tier_total} ({percent:.0f}%)")
    
    print("="*50 + "\n")


def show_today():
    daily = load_daily()
    progress = load_progress()
    problems = get_all_problems()
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_problems = daily.get(today, [])
    
    print(f"\n📅 今日完成 ({today})")
    print("-"*40)
    
    if not today_problems:
        print("今天还没有完成任何题目，加油！")
        return
    
    for key in today_problems:
        for p in problems:
            if get_problem_key(p) == key:
                print(f"  ✓ {p['id']}. {p['name']} ({p['difficulty']})")
                break
    
    print(f"\n共完成 {len(today_problems)} 题")


def show_remaining(limit: int = 10):
    problems = get_all_problems()
    progress = load_progress()
    
    remaining = [p for p in problems if not progress.get(get_problem_key(p))]
    
    print(f"\n📝 待完成题目 (共{len(remaining)}题)")
    print("-"*40)
    
    for i, p in enumerate(remaining[:limit]):
        companies = ', '.join(p['companies'][:2])
        print(f"  {p['id']}. {p['name']} [{p['difficulty']}] ({companies})")
    
    if len(remaining) > limit:
        print(f"\n... 还有 {len(remaining) - limit} 道题目")


def show_next():
    problems = get_all_problems()
    progress = load_progress()
    
    for p in problems:
        if not progress.get(get_problem_key(p)):
            print(f"\n🎯 下一题推荐:")
            print("-"*40)
            print(f"  题号: {p['id']}")
            print(f"  名称: {p['name']}")
            print(f"  难度: {p['difficulty']}")
            print(f"  公司: {', '.join(p['companies'])}")
            print(f"  标签: {', '.join(p['tags'])}")
            print(f"  要点: {p['key_point']}")
            
            if not str(p['id']).startswith('offer'):
                print(f"\n  链接: https://leetcode.cn/problems/{p['name']}/")
            return
    
    print("🎉 恭喜！所有题目都已完成！")


def reset_progress():
    confirm = input("确定要重置所有进度吗？(yes/no): ")
    if confirm.lower() == 'yes':
        save_progress({})
        save_daily({})
        print("进度已重置")
    else:
        print("已取消")


def start_dashboard(port: int = 8080):
    os.chdir(DATA_DIR)
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DATA_DIR), **kwargs)
    
    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}/dashboard.html"
        print(f"\n🚀 刷题进度仪表板已启动")
        print(f"📱 访问地址: {url}")
        print("按 Ctrl+C 停止服务器\n")
        
        webbrowser.open(url)
        httpd.serve_forever()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
LeetCode 刷题进度管理工具

用法:
    python tracker.py <命令> [参数]

命令:
    start               启动Web仪表板
    stats               显示统计信息
    today               显示今日完成情况
    next                显示下一题推荐
    remaining [n]       显示待完成题目 (默认10题)
    done <题号>         标记题目完成
    undo <题号>         取消题目完成
    reset               重置所有进度

示例:
    python tracker.py start
    python tracker.py stats
    python tracker.py done 206
    python tracker.py remaining 20
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        start_dashboard(port)
    elif command == 'stats':
        show_stats()
    elif command == 'today':
        show_today()
    elif command == 'next':
        show_next()
    elif command == 'remaining':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_remaining(limit)
    elif command == 'done':
        if len(sys.argv) < 3:
            print("请提供题号，例如: python tracker.py done 206")
        else:
            mark_completed(sys.argv[2])
    elif command == 'undo':
        if len(sys.argv) < 3:
            print("请提供题号，例如: python tracker.py undo 206")
        else:
            unmark_completed(sys.argv[2])
    elif command == 'reset':
        reset_progress()
    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()
