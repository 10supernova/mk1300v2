; MK1300-Linux Windows Installer — Inno Setup 6 Script
; -------------------------------------------------------
; Compile this with Inno Setup 6 (https://jrsoftware.org/isinfo.php)
; on Windows to produce:  mk1300-win-setup-1.0.0.exe
;
; Prerequisites on Windows build machine:
;   1. pip install pyinstaller hidapi
;   2. pyinstaller mk1300-win.spec        → creates dist\mk1300-win.exe
;   3. Open this .iss in Inno Setup → Build → Compile
;
; The produced setup .exe will:
;   • Install mk1300-win.exe to Program Files
;   • Add it to PATH
;   • Create a Start Menu entry
;   • Install the WinUSB/HID driver note (hidapi uses Windows HID directly)
;   • Provide an uninstaller

#define MyAppName      "MK1300 RGB Controller"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "10supernova"
#define MyAppURL       "https://github.com/10supernova/mk1300-linux"
#define MyAppExeName   "mk1300-win.exe"

[Setup]
AppId={{A3F2C1B4-8D6E-4F7A-9C0B-1E2D3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\MK1300RGB
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
SourceDir=..
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=mk1300-win-setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesEnvironment=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add mk1300-win to &PATH (recommended)"; GroupDescription: "Environment:"

[Files]
; Main executable (built by PyInstaller)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md";  DestDir: "{app}\docs"; Flags: ignoreversion
Source: "LICENSE";    DestDir: "{app}\docs"; Flags: ignoreversion
Source: "NOTICE";     DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{group}\MK1300 RGB CLI";      Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Registry]
; Add to user PATH if task selected
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath(ExpandConstant('{app}')); \
    Tasks: addtopath

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "info"; \
    Description: "Run 'mk1300-win info' (verify keyboard is detected)"; \
    Flags: postinstall nowait skipifsilent

[Code]
{ ── Helper: check if path already in PATH ── }
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
