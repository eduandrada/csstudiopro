; ==============================================================================
; Script de Inno Setup para CS 1.6 Modding & Tuning Studio Pro
; Empaqueta la salida de PyInstaller (dist\CSStudioPro\*) en un Setup.exe profesional
; ==============================================================================

[Setup]
AppId={{8B47E209-1D8C-4D2A-B9C3-2895E54FA011}
AppName=CS 1.6 Modding & Tuning Studio Pro
AppVersion=4.0
AppPublisher=Edu Andrada, yuyito, Hidden /A/, KYAMI, vANS
AppPublisherURL=https://github.com/eduandrada/csstudiopro.git
DefaultDirName={autopf}\CS 1.6 Modding Studio Pro
DefaultGroupName=CS 1.6 Modding Studio Pro
DisableProgramGroupPage=yes
OutputDir=Output_Installer
OutputBaseFilename=CS_Studio_Pro_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copia todo el contenido compilado por PyInstaller
Source: "dist\CSStudioPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CS 1.6 Modding Studio Pro"; Filename: "{app}\CSStudioPro.exe"
Name: "{group}\{cm:UninstallProgram, CS 1.6 Modding Studio Pro}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CS 1.6 Modding Studio Pro"; Filename: "{app}\CSStudioPro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CSStudioPro.exe"; Description: "{cm:LaunchProgram, CS 1.6 Modding Studio Pro}"; Flags: nowait postinstall skipifsilent runascurrentuser
