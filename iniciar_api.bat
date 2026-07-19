@echo off
chcp 65001 > nul
title Google Maps Scraper API - Servidor

cls
echo ========================================================
echo          GOOGLE MAPS SCRAPER - SERVIDOR API
echo ========================================================
echo.
echo Iniciando o servidor local da API...
echo O endereco de acesso (POST) sera: http://127.0.0.1:8000/scrape
echo.
echo Exemplo de corpo da requisicao (JSON):
echo { "search": "restaurantes recife", "total": 5 }
echo.
echo Para fechar a API, basta fechar esta janela ou pressionar Ctrl+C.
echo ========================================================
echo.

.\venv\Scripts\python.exe api.py
pause
