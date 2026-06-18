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
  --include-package-data=apify_fingerprint_datapoints ^
  --include-package-data=language_tags ^
  --output-filename="Spotify Downloader" ^
  --windows-icon-from-ico=icons/icon.ico .\main.py || exit /b 1

REM ВАЖНО (облачная синхронизация — OneDrive/Synology/Dropbox): если проект лежит в
REM синхронизируемой папке, её файлы — placeholder'ы, и крупные файлы бьются И при ЧТЕНИИ
REM (ISCC прочитает неполные байты исходников), И при ЗАПИСИ (синк портит большой Setup.exe).
REM При SolidCompression одного неполного файла достаточно, чтобы установщик упал с
REM "Compressed data is corrupted". Поэтому: исходники копируем в ЛОКАЛЬНУЮ папку (robocopy
REM принудительно скачивает их), и инсталлятор пишем тоже в ЛОКАЛЬНУЮ папку, а не в проект.
REM Браузер Camoufox уже лежит в %LOCALAPPDATA% (локально) — копировать его не нужно.
set "DIST_LOCAL=%TEMP%\spotidl_dist"
set "OUT_LOCAL=%LOCALAPPDATA%\SpotifyDownloaderSetup"
echo Staging dist to local folder "%DIST_LOCAL%" (cloud-sync safety)...
rmdir /s /q "%DIST_LOCAL%" 2>nul
robocopy "build\main.dist" "%DIST_LOCAL%" /E /MT /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if errorlevel 8 (echo robocopy failed & exit /b 1)

REM Inno Setup: ISCC из PATH, иначе — стандартный путь установки.
REM /DDistDir -> локальная копия сборки; /O -> локальная папка вывода (вне облака).
where ISCC >nul 2>nul && (ISCC /DDistDir="%DIST_LOCAL%" /O"%OUT_LOCAL%" installer.iss) || ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DDistDir="%DIST_LOCAL%" /O"%OUT_LOCAL%" installer.iss)
if errorlevel 1 (echo ISCC failed & exit /b 1)

rmdir /s /q "%DIST_LOCAL%" 2>nul
echo.
echo ====================================================================
echo  Installer ready: "%OUT_LOCAL%\Spotify Downloader 3.0.0 Setup.exe"
echo  (output is LOCAL, not in the synced project folder — by design)
echo ====================================================================
