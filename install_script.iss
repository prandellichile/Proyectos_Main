[Setup]
AppName=Dashboard Comercial
AppVersion=1.0
DefaultDirName={autopf}\DashboardComercial
DisableProgramGroupPage=yes
OutputDir=D:\Installer_Dashboard
OutputBaseFilename=Instalador_Dashboard
Compression=lzma
SolidCompression=yes

[Files]
Source: "D:\Installer_Dashboard\app\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{autoprograms}\Dashboard Comercial"; Filename: "{app}\lanzar_dashboard.vbs"; IconFilename: "{app}\icono.ico"
Name: "{userdesktop}\Dashboard Comercial"; Filename: "{app}\lanzar_dashboard.vbs"; IconFilename: "{app}\icono.ico"

[Run]
Filename: "{app}\lanzar_dashboard.vbs"; Description: "Iniciar Dashboard al terminar"; Flags: nowait postinstall skipifsilent