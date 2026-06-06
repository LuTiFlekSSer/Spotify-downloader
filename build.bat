@echo off
REM === Сборка Spotify Downloader (Nuitka + Inno Setup) ===
REM Запускать из активированного venv (где установлены PySide6, nuitka, camoufox).
REM Перед сборкой один раз скачайте браузер Camoufox:  camoufox fetch
REM (он попадёт в %LOCALAPPDATA%\camoufox\camoufox\Cache и будет вшит в инсталлятор)

python change_iss_version.py || exit /b 1

python -m nuitka --standalone --assume-yes-for-downloads --enable-plugin=pyside6 --follow-imports --jobs=12 ^
  --output-dir=build ^
  --windows-console-mode=disable ^
  --include-data-files=src/locales/locales.json=src/locales/locales.json ^
  --include-data-dir=src/frontend/style_sheets/qss=src/frontend/style_sheets/qss ^
  --include-data-dir=icons=icons ^
  --include-package-data=camoufox ^
  --include-package-data=browserforge ^
  --output-filename="Spotify Downloader" ^
  --windows-icon-from-ico=icons/icon.ico .\main.py || exit /b 1

REM ВАЖНО: облачная синхронизация (OneDrive/Synology/Dropbox) может держать файлы
REM как placeholder'ы. Тогда ISCC прочитает неполные байты исходников и вшьёт битый
REM сжатый поток -> установщик упадёт с "Compressed data is corrupted". Принудительно
REM материализуем все файлы сборки (чтение через type заставляет скачать их на диск).
echo Materializing build files (cloud-sync safety)...
for /r "build\main.dist" %%f in (*) do type "%%f" >nul 2>&1

REM Inno Setup: используем ISCC из PATH, иначе — стандартный путь установки
where ISCC >nul 2>nul && (ISCC installer.iss) || ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer.iss)
