@echo off
chcp 65001
title Audio Booster Launcher
echo ===============================
echo    Audio Booster Launcher
echo ===============================
echo.
echo Выберите действие:
echo 1 - Установить VB-Cable
echo 2 - Запустить мост усиления
echo 3 - Проверить аудио устройства
echo.
set /p choice="Введите номер [1-3]: "

if "%choice%"=="1" (
    python install_vb_cable.py
) else if "%choice%"=="2" (
    python basic_audio_bridge.py
) else if "%choice%"=="4" (
    python super_audio_bridge.py
) else if "%choice%"=="3" (
    python -c "import pyaudio; p = pyaudio.PyAudio(); print('Устройства:'); [print(f'{i}: {p.get_device_info_by_index(i)['name']}') for i in range(p.get_device_count())]; p.terminate()"
    pause
) else (
    echo Неверный выбор
    pause
)