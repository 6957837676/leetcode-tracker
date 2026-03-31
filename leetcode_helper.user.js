// ==UserScript==
// @name         LeetCode 刷题助手
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  在LeetCode页面添加完成标记和复习按钮
// @author       You
// @match        https://leetcode.cn/problems/*
// @match        https://leetcode.com/problems/*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      localhost
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    const SERVER_URL = 'http://localhost:8080';

    GM_addStyle(`
        .lc-helper-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .lc-helper-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .lc-helper-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .lc-complete-btn {
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
        }
        .lc-complete-btn.done {
            background: linear-gradient(135deg, #6b7280, #9ca3af);
        }
        .lc-review-btn {
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: white;
        }
        .lc-review-btn:hover {
            background: linear-gradient(135deg, #4338ca, #4f46e5);
        }
        .lc-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background: #059669;
            color: white;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10001;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .lc-toast.error {
            background: #dc2626;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .lc-review-panel {
            position: fixed;
            top: 80px;
            right: 20px;
            width: 320px;
            max-height: 400px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 10000;
            overflow: hidden;
            display: none;
        }
        .lc-review-panel.show {
            display: block;
        }
        .lc-review-header {
            padding: 16px;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: white;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .lc-review-close {
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        .lc-review-list {
            max-height: 320px;
            overflow-y: auto;
        }
        .lc-review-item {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.15s;
        }
        .lc-review-item:hover {
            background: #f3f4f6;
        }
        .lc-review-item:last-child {
            border-bottom: none;
        }
        .lc-review-item .info {
            flex: 1;
        }
        .lc-review-item .name {
            font-weight: 500;
            color: #1f2937;
            font-size: 13px;
        }
        .lc-review-item .meta {
            font-size: 11px;
            color: #6b7280;
            margin-top: 2px;
        }
        .lc-review-item .go-btn {
            padding: 4px 10px;
            background: #4f46e5;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
        }
        .lc-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
        }
        .lc-badge.easy { background: #dcfce7; color: #166534; }
        .lc-badge.medium { background: #fef3c7; color: #92400e; }
        .lc-badge.hard { background: #fee2e2; color: #991b1b; }
    `);

    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = 'lc-toast' + (isError ? ' error' : '');
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }

    function getProblemInfo() {
        const url = window.location.href;
        const match = url.match(/problems\/([^\/]+)/);
        if (!match) return null;
        
        const slug = match[1];
        const titleEl = document.querySelector('[data-cy="question-title"]') || 
                        document.querySelector('.mr-2.text-label-1') ||
                        document.querySelector('h4');
        
        let name = '';
        let id = '';
        if (titleEl) {
            const text = titleEl.textContent.trim();
            const idMatch = text.match(/^(\d+)\.\s*(.+)$/);
            if (idMatch) {
                id = idMatch[1];
                name = idMatch[2];
            } else {
                name = text;
            }
        }
        
        return { slug, name, id, key: id && name ? `${id}_${name}` : null };
    }

    function apiRequest(endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: method,
                url: SERVER_URL + endpoint,
                headers: { 'Content-Type': 'application/json' },
                data: data ? JSON.stringify(data) : null,
                onload: (response) => {
                    try {
                        resolve(JSON.parse(response.responseText));
                    } catch (e) {
                        reject(e);
                    }
                },
                onerror: (error) => {
                    reject(error);
                }
            });
        });
    }

    async function checkProgress(key) {
        try {
            const result = await apiRequest('/api/progress');
            return result.progress && result.progress[key];
        } catch (e) {
            return false;
        }
    }

    async function markComplete(key) {
        try {
            await apiRequest('/api/toggle', 'POST', { key: key });
            showToast('已标记完成！');
            updateButtonState(true);
        } catch (e) {
            showToast('标记失败，请确保服务器运行中', true);
        }
    }

    async function loadReviewList() {
        try {
            const result = await apiRequest('/api/review');
            return result.review || [];
        } catch (e) {
            return [];
        }
    }

    function updateButtonState(isDone) {
        const btn = document.querySelector('.lc-complete-btn');
        if (btn) {
            if (isDone) {
                btn.classList.add('done');
                btn.innerHTML = '✓ 已完成';
            } else {
                btn.classList.remove('done');
                btn.innerHTML = '✓ 标记完成';
            }
        }
    }

    function createReviewPanel() {
        const panel = document.createElement('div');
        panel.className = 'lc-review-panel';
        panel.id = 'lc-review-panel';
        panel.innerHTML = `
            <div class="lc-review-header">
                <span>📚 复习列表</span>
                <button class="lc-review-close" onclick="document.getElementById('lc-review-panel').classList.remove('show')">×</button>
            </div>
            <div class="lc-review-list" id="lc-review-list">
                <div style="padding: 20px; text-align: center; color: #6b7280;">加载中...</div>
            </div>
        `;
        document.body.appendChild(panel);
        return panel;
    }

    async function showReviewPanel() {
        let panel = document.getElementById('lc-review-panel');
        if (!panel) {
            panel = createReviewPanel();
        }
        
        panel.classList.toggle('show');
        
        if (panel.classList.contains('show')) {
            const list = document.getElementById('lc-review-list');
            const reviews = await loadReviewList();
            
            if (reviews.length === 0) {
                list.innerHTML = '<div style="padding: 20px; text-align: center; color: #6b7280;">暂无已完成的题目</div>';
            } else {
                list.innerHTML = reviews.map(p => {
                    const diffClass = p.difficulty === '简单' ? 'easy' : p.difficulty === '中等' ? 'medium' : 'hard';
                    return `
                        <div class="lc-review-item">
                            <div class="info">
                                <div class="name">${p.id}. ${p.name}</div>
                                <div class="meta">
                                    <span class="lc-badge ${diffClass}">${p.difficulty}</span>
                                    ${p.type ? ' · ' + p.type : ''}
                                </div>
                            </div>
                            <button class="go-btn" onclick="window.open('https://leetcode.cn/problems/${p.slug}/', '_blank')">复习</button>
                        </div>
                    `;
                }).join('');
            }
        }
    }

    function createUI() {
        const info = getProblemInfo();
        if (!info) return;

        const container = document.createElement('div');
        container.className = 'lc-helper-container';

        const completeBtn = document.createElement('button');
        completeBtn.className = 'lc-helper-btn lc-complete-btn';
        completeBtn.innerHTML = '✓ 标记完成';
        completeBtn.onclick = () => {
            if (info.key) {
                markComplete(info.key);
            } else {
                showToast('无法获取题目信息', true);
            }
        };

        const reviewBtn = document.createElement('button');
        reviewBtn.className = 'lc-helper-btn lc-review-btn';
        reviewBtn.innerHTML = '📚 REVIEW';
        reviewBtn.onclick = showReviewPanel;

        container.appendChild(completeBtn);
        container.appendChild(reviewBtn);
        document.body.appendChild(container);

        if (info.key) {
            checkProgress(info.key).then(isDone => {
                updateButtonState(isDone);
            });
        }
    }

    function waitForPageLoad() {
        const observer = new MutationObserver((mutations, obs) => {
            const titleEl = document.querySelector('[data-cy="question-title"]') || 
                           document.querySelector('.mr-2.text-label-1') ||
                           document.querySelector('h4');
            if (titleEl && !document.querySelector('.lc-helper-container')) {
                createUI();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            if (!document.querySelector('.lc-helper-container')) {
                createUI();
            }
        }, 2000);
    }

    waitForPageLoad();
})();
