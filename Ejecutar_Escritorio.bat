@echo off
chcp 65001 > nul
title Sistema Universitario UCC - Version Escritorio
cd /d "%~dp01_Version_Escritorio_Avanzada"
python main.py
if errorlevel 1 pause
