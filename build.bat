@echo off
REM === Сборка Spotify Downloader (Nuitka + Inno Setup) ===
REM Перед сборкой один раз скачайте браузер Camoufox:  camoufox fetch
REM (он попадёт в %LOCALAPPDATA%\camoufox\camoufox\Cache и будет вшит в инсталлятор)

cmd /c python change_iss_version.py

cmd /c nuitka --standalone --assume-yes-for-downloads --enable-plugin=pyside6 --follow-imports --jobs=12 ^
  --output-dir=build ^
  --windows-console-mode=disable ^
  --include-data-files=src/locales/locales.json=src/locales/locales.json ^
  --include-data-dir=src/frontend/style_sheets/qss=src/frontend/style_sheets/qss ^
  --include-data-dir=icons=icons ^
  --include-package-data=camoufox ^
  --include-package-data=browserforge ^
  --output-filename="Spotify Downloader" ^
  --windows-icon-from-ico=icons/icon.ico .\main.py

cmd /c ISCC installer.iss
