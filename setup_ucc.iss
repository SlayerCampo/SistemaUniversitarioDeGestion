; ==============================================================================
; Script de Instalación Oficial Inno Setup - Sistema Universitario UCC
; Sede Cali - Facultad de Ingeniería
; Autores: Alejandro Campo Solarte, Juan Esteban Cardona, Diego Fernando Gómez
; ==============================================================================

#define MyAppName "Sistema Universitario UCC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Universidad Cooperativa de Colombia"
#define MyAppURL "https://sistemauniversitariodegestion.streamlit.app/"
#define MyAppExeName "Sistema_Universitario_UCC.exe"

[Setup]
AppId={{9F82A31B-4C9D-4F1E-9C64-28B369D39422}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=Instalador_Sistema_Universitario_UCC_Setup
SetupIconFile=1_Version_Escritorio_Avanzada\logo_ucc.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "1_Version_Escritorio_Avanzada\dist\Sistema_Universitario_UCC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo_ucc.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo_ucc.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
