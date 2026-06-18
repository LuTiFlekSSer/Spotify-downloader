; Inno Setup script — Spotify Downloader
; Версия подставляется автоматически из src/version (change_iss_version.py).

#define MyAppName "Spotify Downloader"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "LuTiFlekSSer"
#define MyAppURL "https://github.com/LuTiFlekSSer/Spotify-downloader"
#define MyAppExeName "Spotify Downloader.exe"
; Каталог с Nuitka-сборкой. build.bat подставляет ЛОКАЛЬНУЮ копию через /DDistDir=...,
; чтобы ISCC не читал placeholder'ы из облачной папки (OneDrive/Synology) и не вшил
; битый поток. По умолчанию — сборка прямо в проекте.
#ifndef DistDir
  #define DistDir "build\main.dist"
#endif

[Setup]
AppId={{7F2E9C44-1A3B-4D6E-9C2A-5B8E1F0A7C31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
; Версия в свойствах файла Setup.exe (иначе Inno ставит 0.0.0.0). {#MyAppVersion} подставляет
; change_iss_version.py из src/version -> заполняется автоматически в каждой будущей сборке.
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
; БЕЗ AppMutex: в тихом режиме (/VERYSILENT /SUPPRESSMSGBOXES) наличие мьютекса заставляет
; Inno аварийно прерваться (exit 1), а не закрыть приложение. Вместо этого закрытие
; работающего приложения делает RestartManager через /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS
; (плюс само приложение завершается перед запуском установщика обновления).
; Per-user, чтобы браузер Camoufox лёг в кэш текущего пользователя
PrivilegesRequired=lowest
OutputBaseFilename=Spotify Downloader {#MyAppVersion} Setup
SetupIconFile=.\icons\icon.ico
SolidCompression=yes
Compression=lzma2/max
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Само приложение (Nuitka standalone)
Source: "{#DistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Браузер Camoufox: вшивается из кэша сборочной машины (camoufox fetch) в кэш пользователя.
; camoufox ищет браузер строго в %LOCALAPPDATA%\camoufox\camoufox\Cache.
; Source раскрывается на этапе компиляции -> читаем %LOCALAPPDATA% сборочной машины через ISPP GetEnv;
; DestDir раскрывается на этапе установки -> {localappdata} целевого пользователя.
; uninsneveruninstall: не удалять браузер при деинсталляции (это общий для машины кэш camoufox).
Source: "{#GetEnv('LOCALAPPDATA')}\camoufox\camoufox\Cache\*"; DestDir: "{localappdata}\camoufox\camoufox\Cache"; \
    Flags: ignoreversion recursesubdirs createallsubdirs uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; без skipifsilent — чтобы при тихом обновлении приложение перезапускалось автоматически
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall
