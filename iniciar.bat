@echo off
:: Configura o console para UTF-8 de modo a exibir acentos corretamente no Windows
chcp 65001 > nul
title Google Maps Scraper - Inicializador

cls
echo ========================================================
echo          GOOGLE MAPS SCRAPER - INICIALIZADOR
echo ========================================================
echo.
echo Este script irá rodar o buscador no ambiente virtual (venv).
echo Os resultados serão salvos por padrão no arquivo 'result.csv'.
echo.
echo ========================================================
echo.

set /p busca="Digite o termo de busca (Ex: restaurantes em Pinheiros SP): "
if "%busca%"=="" (
    echo.
    echo [Erro] Você precisa digitar um termo de busca!
    pause
    exit /b
)

set /p total="Digite a quantidade total de locais a extrair (Padrão: 10): "
if "%total%"=="" set total=10

echo.
echo ========================================================
echo Iniciando a busca para: "%busca%"
echo Quantidade máxima: %total%
echo ========================================================
echo.

:: Executa o script python no venv
.\venv\Scripts\python.exe main.py -s "%busca%" -t %total%

echo.
echo ========================================================
echo Busca Concluída! Os dados foram salvos no arquivo 'result.csv'.
echo ========================================================
echo.
pause
