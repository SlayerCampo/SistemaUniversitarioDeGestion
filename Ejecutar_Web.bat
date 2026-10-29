@echo off
chcp 65001 > nul
title Sistema Universitario UCC - Version Web
cd /d "%~dp0"
python -m streamlit run "2_Version_Web_Desplegable\app.py"
if errorlevel 1 pause
