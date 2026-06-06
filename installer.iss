; Inno Setup script — Spotify Downloader
; Версия подставляется автоматически из src/version (change_iss_version.py).

#define MyAppName "Spotify Downloader"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "LuTiFlekSSer"
#define MyAppURL "https://github.com/LuTiFlekSSer/Spotify-downloader"
#define MyAppExeName "Spotify Downloader.exe"

[Setup]
AppId={{7F2E9C44-1A3B-4D6E-9C2A-5B8E1F0A7C31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
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
Source: ".\build\main.dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\build\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Браузер Camoufox: вшивается из кэша сборочной машины (camoufox fetch) в кэш пользователя.
; camoufox ищет браузер строго в %LOCALAPPDATA%\camoufox\camoufox\Cache.
; Source раскрывается на этапе компиляции -> читаем %LOCALAPPDATA% сборочной машины через ISPP GetEnv;
; DestDir раскрывается на этапе установки -> {localappdata} целевого пользователя.
Source: "{#GetEnv('LOCALAPPDATA')}\camoufox\camoufox\Cache\*"; DestDir: "{localappdata}\camoufox\camoufox\Cache"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
