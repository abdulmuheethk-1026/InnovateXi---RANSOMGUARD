; ─────────────────────────────────────────────────────────────────────────────
; RANSOMGUARD – Inno Setup Script
; Produces:  RansomGuard_Setup_v1.0.0.exe
;
; Requirements:
;   - Inno Setup 6+  (https://jrsoftware.org/isinfo.php)
;   - PyInstaller dist/ folder must be built first (run build.py)
;
; To build the installer:
;   1. python build.py              ← creates dist\RansomGuard\
;   2. iscc RansomGuard_Setup.iss   ← creates Output\RansomGuard_Setup_v1.0.0.exe
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "RansomGuard"
#define AppVersion   "1.0.0"
#define AppPublisher "RansomGuard Security"
#define AppURL       "https://ransomguard.io"
#define AppExeName   "RansomGuard.exe"
#define AppDesc      "Lightweight Ransomware Early Warning System"

[Setup]
; ── Identity ──────────────────────────────────────────────────────────────
AppId                   = {{A3F2C1B4-9E7D-4F8A-B6C2-D1E5F3A8B9C0}
AppName                 = {#AppName}
AppVersion              = {#AppVersion}
AppVerName              = {#AppName} v{#AppVersion}
AppPublisher            = {#AppPublisher}
AppPublisherURL         = {#AppURL}
AppSupportURL           = {#AppURL}/support
AppUpdatesURL           = {#AppURL}/download
VersionInfoVersion      = {#AppVersion}
VersionInfoDescription  = {#AppDesc}

; ── Install paths ─────────────────────────────────────────────────────────
DefaultDirName          = {autopf}\{#AppName}
DefaultGroupName        = {#AppName}
DisableProgramGroupPage = yes
OutputDir               = Output
OutputBaseFilename      = RansomGuard_Setup_v{#AppVersion}
SetupIconFile           = assets\shield_icon.ico
UninstallDisplayIcon    = {app}\{#AppExeName}

; ── Appearance ────────────────────────────────────────────────────────────
WizardStyle             = modern
WizardSizePercent       = 110
WizardImageFile         = assets\wizard_banner.bmp
WizardSmallImageFile    = assets\wizard_small.bmp

; ── Behaviour ─────────────────────────────────────────────────────────────
Compression             = lzma2/ultra64
SolidCompression        = yes
PrivilegesRequired      = admin
AllowNoIcons            = yes
DisableReadyMemo        = no
ShowLanguageDialog      = auto

; ── Signing (comment out if no certificate) ───────────────────────────────
; SignTool = signtool sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 /f "cert.pfx" /p "password" $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut";             GroupDescription: "Additional icons:"
Name: "startupentry";  Description: "Start RansomGuard automatically at boot"; GroupDescription: "Startup:"; Flags: checked

[Files]
; Main application (PyInstaller output)
Source: "dist\RansomGuard\*";  DestDir: "{app}";  Flags: ignoreversion recursesubdirs createallsubdirs

; Default config
Source: "assets\default_config.json";  DestDir: "{commonappdata}\RansomGuard";  Flags: onlyifdoesntexist

[Icons]
; Start menu
Name: "{group}\{#AppName}";                  Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";        Filename: "{uninstallexe}"

; Desktop shortcut (optional task)
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExeName}";  Tasks: desktopicon

[Registry]
; Auto-start at boot (optional task)
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
  ValueType: string; ValueName: "{#AppName}";
  ValueData: """{app}\{#AppExeName}""";
  Tasks: startupentry; Flags: uninsdeletevalue

; Add to installed programs (displayed in Settings > Apps)
Root: HKLM; Subkey: "SOFTWARE\{#AppPublisher}\{#AppName}";
  ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\{#AppPublisher}\{#AppName}";
  ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"

[Run]
; Launch app after install
Filename: "{app}\{#AppExeName}";
  Description: "Launch {#AppName} now";
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Gracefully stop the service before uninstall
Filename: "{app}\{#AppExeName}"; Parameters: "--stop"; Flags: runhidden

[UninstallDelete]
; Remove logs and config on uninstall (optional)
Type: filesandordirs; Name: "{commonappdata}\RansomGuard"

[Code]
{ ── Custom Inno Setup Pascal code ───────────────────────────────────────── }

{ Minimum OS check: Windows 10 or later }
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.Major < 10 then
  begin
    MsgBox('RansomGuard requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

{ Show EULA on second page }
procedure InitializeWizard();
begin
  WizardForm.LicenseAcceptedRadio.Checked := False;
end;

{ Confirm cancel }
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;
