; Inno Setup script for ufo-agent.
; Produces a classic per-user setup.exe: Start-menu shortcut, run-at-login,
; uninstaller. No admin required (installs under %LOCALAPPDATA%).
; Build: ISCC.exe /DAppVersion=0.0.1 packaging\ufo-agent.iss
;   (paths below are relative to this .iss file, i.e. packaging\)

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{B2F1C3A4-1A2B-4C3D-8E4F-0123456789AB}
AppName=UFO Agent
AppVersion={#AppVersion}
AppPublisher=posix4e
DefaultDirName={localappdata}\UFO Agent
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer
OutputBaseFilename=ufo-agent-setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\ufo-agent.exe
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; PyInstaller --onedir output (repo-root dist\ufo-agent\)
Source: "..\dist\ufo-agent\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\UFO Agent"; Filename: "{app}\ufo-agent.exe"
; Run at login (per-user Startup) — the agent should be on whenever the user is.
Name: "{userstartup}\UFO Agent"; Filename: "{app}\ufo-agent.exe"

[Run]
Filename: "{app}\ufo-agent.exe"; Description: "Launch UFO Agent now"; Flags: nowait postinstall skipifsilent
