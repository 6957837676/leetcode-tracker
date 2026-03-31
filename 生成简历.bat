@echo off
chcp 65001 >nul
echo 正在安装依赖...
pip install python-docx -q
echo 正在生成简历DOCX...
python "%~dp0html_to_docx.py"
pause
