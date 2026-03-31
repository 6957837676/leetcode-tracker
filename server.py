#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeetCode 刷题进度服务
使用SQLite存储进度，提供REST API
"""

import sqlite3
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

DB_FILE = os.path.join(os.path.dirname(__file__), 'progress.db')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'problems.json')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            problem_key TEXT PRIMARY KEY,
            completed INTEGER DEFAULT 0,
            completed_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily (
            date TEXT,
            problem_key TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, problem_key)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_progress():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT problem_key, completed FROM progress WHERE completed = 1')
    return {row['problem_key']: True for row in c.fetchall()}

def set_progress(problem_key, completed):
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if completed:
        c.execute('''
            INSERT OR REPLACE INTO progress (problem_key, completed, completed_at)
            VALUES (?, 1, ?)
        ''', (problem_key, datetime.now().isoformat()))
        c.execute('''
            INSERT OR IGNORE INTO daily (date, problem_key)
            VALUES (?, ?)
        ''', (today, problem_key))
    else:
        c.execute('DELETE FROM progress WHERE problem_key = ?', (problem_key,))
        c.execute('DELETE FROM daily WHERE date = ? AND problem_key = ?', (today, problem_key))
    
    conn.commit()
    conn.close()

def get_daily():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT date, problem_key FROM daily')
    result = {}
    for row in c.fetchall():
        if row['date'] not in result:
            result[row['date']] = []
        result[row['date']].append(row['problem_key'])
    conn.close()
    return result

def get_settings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT key, value FROM settings')
    result = {}
    for row in c.fetchall():
        try:
            result[row['key']] = json.loads(row['value'])
        except:
            result[row['key']] = row['value']
    conn.close()
    return result

def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    ''', (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value)))
    conn.commit()
    conn.close()

def reset_all():
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM progress')
    c.execute('DELETE FROM daily')
    conn.commit()
    conn.close()

def get_review_problems():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT problem_key, completed_at FROM progress WHERE completed = 1 ORDER BY completed_at ASC')
    completed = c.fetchall()
    conn.close()
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_problems = []
    for day in data.get('days', []):
        for p in day.get('problems', []):
            all_problems.append({
                'id': p.get('id'),
                'name': p.get('name'),
                'slug': p.get('slug'),
                'difficulty': p.get('difficulty'),
                'type': p.get('type'),
                'day': day.get('day')
            })
    
    review_list = []
    for row in completed:
        key = row['problem_key']
        completed_at = row['completed_at']
        for p in all_problems:
            if f"{p['id']}_{p['name']}" == key:
                review_list.append({
                    **p,
                    'completed_at': completed_at,
                    'key': key
                })
                break
    
    return review_list

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/api/progress':
            self.send_json({'progress': get_progress()})
        elif path == '/api/daily':
            self.send_json({'daily': get_daily()})
        elif path == '/api/settings':
            self.send_json({'settings': get_settings()})
        elif path == '/api/problems':
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.send_json(json.load(f))
        elif path == '/api/stats':
            progress = get_progress()
            daily = get_daily()
            today = datetime.now().strftime('%Y-%m-%d')
            today_count = len(daily.get(today, []))
            total_done = len(progress)
            
            dates = sorted(daily.keys())
            streak = 0
            now = datetime.now()
            for i in range(len(dates) - 1, -1, -1):
                d = datetime.strptime(dates[i], '%Y-%m-%d')
                diff = (now - d).days
                if diff == streak and len(daily[dates[i]]) > 0:
                    streak += 1
                elif diff > streak:
                    break
            
            self.send_json({
                'total_done': total_done,
                'today_count': today_count,
                'streak': streak
            })
        elif path == '/api/review':
            self.send_json({'review': get_review_problems()})
        elif path == '/api/remind':
            self.send_json({'settings': get_settings()})
        elif path == '/' or path == '/index.html':
            self.serve_file('dashboard.html')
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if path == '/api/toggle':
            problem_key = data.get('key')
            if problem_key:
                progress = get_progress()
                completed = problem_key not in progress
                set_progress(problem_key, completed)
                self.send_json({'success': True, 'completed': completed})
            else:
                self.send_json({'success': False, 'error': 'Missing key'}, 400)
        elif path == '/api/complete':
            problem_key = data.get('key')
            if problem_key:
                set_progress(problem_key, True)
                self.send_json({'success': True, 'message': '已标记完成'})
            else:
                self.send_json({'success': False, 'error': 'Missing key'}, 400)
        elif path == '/api/settings':
            for key, value in data.items():
                set_setting(key, value)
            self.send_json({'success': True})
        elif path == '/api/reset':
            reset_all()
            self.send_json({'success': True})
        else:
            self.send_error(404)
    
    def serve_file(self, filename):
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

def run_server(port=8080):
    init_db()
    server = HTTPServer(('127.0.0.1', port), APIHandler)
    print(f'''
╔══════════════════════════════════════════════════════╗
║     LeetCode 刷题进度监督系统 - 服务已启动           ║
╠══════════════════════════════════════════════════════╣
║  🌐 访问地址: http://localhost:{port}                  ║
║  📊 数据存储: SQLite ({DB_FILE})
║  ⌨️  按 Ctrl+C 停止服务                              ║
╚══════════════════════════════════════════════════════╝
    ''')
    
    import webbrowser
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务已停止')
        server.shutdown()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
