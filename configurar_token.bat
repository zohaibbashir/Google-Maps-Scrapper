@echo off
chcp 65001 > nul
title Configurar Token do Ngrok

cls
echo ========================================================
echo          CONFIGURAR TOKEN DO NGROK
echo ========================================================
echo.
echo Para usar o Ngrok, voce precisa de um Authtoken gratuito.
echo Se voce ainda nao tem um, crie sua conta e copie o token em:
echo https://dashboard.ngrok.com/get-started/your-authtoken
echo.
set /p token="Cole o seu Authtoken do Ngrok aqui: "

if "%token%"=="" (
    echo.
    echo [Erro] Token invalido ou vazio!
    pause
    exit /b
)

echo.
echo Configurando o token usando o executavel local do Ngrok...
.\ngrok.exe config add-authtoken "%token%"
echo.
echo ========================================================
echo Token configurado com sucesso!
echo Agora voce ja pode usar a API com acesso publico.
echo ========================================================
echo.
pause
