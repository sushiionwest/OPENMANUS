# scripts/build_windows.py
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def get_version():
    """Get the application version"""
    # You could read this from a version file or package
    return "0.1.0"


def get_app_info():
    """Get application information"""
    return {
        "name": "OpenManus Redo",
        "version": get_version(),
        "description": "A modern desktop interface for the OpenManus AI agent framework",
        "author": "OpenManus Redo Team",
        "author_email": "info@openmanus.example.com",
        "url": "https://github.com/example/openmanus-redo"
    }


def clean_build_dirs():
    """Clean build and dist directories"""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)


def copy_assets(target_dir):
    """Copy necessary assets to the distribution"""
    assets_dir = Path("assets")
    target_assets = Path(target_dir) / "assets"
    
    # Create target directory if it doesn't exist
    os.makedirs(target_assets, exist_ok=True)
    
    # Copy assets
    if assets_dir.exists():
        print("Copying assets...")
        for item in assets_dir.glob("**/*"):
            # Skip __pycache__ directories
            if "__pycache__" in str(item):
                continue
                
            # Get the relative path from the assets directory
            rel_path = item.relative_to(assets_dir)
            target_path = target_assets / rel_path
            
            # Create parent directories if they don't exist
            if item.is_file():
                os.makedirs(target_path.parent, exist_ok=True)
                shutil.copy2(item, target_path)
            elif item.is_dir():
                os.makedirs(target_path, exist_ok=True)


def build_windows_installer(args):
    """Build Windows installer using PyInstaller and NSIS"""
    clean_build_dirs()
    
    app_info = get_app_info()
    version = app_info["version"]
    
    print("Building Windows executable...")
    
    # PyInstaller command
    pyinstaller_args = [
        "pyinstaller",
        "--name", app_info["name"].replace(" ", ""),
        "--windowed",
        "--icon", "assets/images/icon.ico",
        "--add-data", "assets;assets",
        "--add-data", "config;config",
        "--hidden-import", "PyQt6",
        "--hidden-import", "app.agent.manus",
        "--hidden-import", "app.flow.base",
        "--hidden-import", "app.flow.flow_factory",
        "main.py"
    ]
    
    if args.onefile:
        pyinstaller_args.append("--onefile")
    else:
        pyinstaller_args.append("--onedir")
    
    # Run PyInstaller
    subprocess.run(pyinstaller_args, check=True)
    
    # Copy additional assets if needed
    if not args.onefile:
        copy_assets(os.path.join("dist", app_info["name"].replace(" ", "")))
    
    # Create NSIS installer script
    print("Creating NSIS installer script...")
    nsis_script = f"""
; NSIS Installer Script for {app_info["name"]}

!include "MUI2.nsh"

; Application information
Name "{app_info["name"]}"
OutFile "dist/{app_info["name"].replace(" ", "")}_Setup_{version}.exe"
InstallDir "$PROGRAMFILES\\{app_info["name"]}"
InstallDirRegKey HKCU "Software\\{app_info["name"]}" ""

; Request application privileges
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\\images\\icon.ico"
!define MUI_UNICON "assets\\images\\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Add files
    File /r "dist\\{app_info["name"].replace(" ", "")}\\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\{app_info["name"]}"
    CreateShortCut "$SMPROGRAMS\\{app_info["name"]}\\{app_info["name"]}.lnk" "$INSTDIR\\{app_info["name"].replace(" ", "")}.exe"
    CreateShortCut "$SMPROGRAMS\\{app_info["name"]}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortCut "$DESKTOP\\{app_info["name"]}.lnk" "$INSTDIR\\{app_info["name"].replace(" ", "")}.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\\{app_info["name"]}" "" $INSTDIR
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "DisplayName" "{app_info["name"]}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "DisplayVersion" "{version}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "Publisher" "{app_info["author"]}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}" "NoRepair" 1
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\\{app_info["name"]}.lnk"
    Delete "$SMPROGRAMS\\{app_info["name"]}\\{app_info["name"]}.lnk"
    Delete "$SMPROGRAMS\\{app_info["name"]}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\{app_info["name"]}"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_info["name"]}"
    DeleteRegKey HKCU "Software\\{app_info["name"]}"
SectionEnd
"""
    
    with open("installer.nsi", "w") as f:
        f.write(nsis_script)
    
    # Run NSIS if available
    try:
        print("Building installer...")
        subprocess.run(["makensis", "installer.nsi"], check=True)
        print(f"Installer created: dist/{app_info['name'].replace(' ', '')}_Setup_{version}.exe")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("NSIS not found. Installer script created but not compiled.")
        print("To create the installer, install NSIS and run: makensis installer.nsi")


def main():
    parser = argparse.ArgumentParser(description="Build Windows installer for OpenManus Redo")
    parser.add_argument("--onefile", action="store_true", help="Create a single executable file")
    args = parser.parse_args()
    
    build_windows_installer(args)


if __name__ == "__main__":
    main()


# scripts/build_macos.py
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def get_version():
    """Get the application version"""
    # You could read this from a version file or package
    return "0.1.0"


def get_app_info():
    """Get application information"""
    return {
        "name": "OpenManus Redo",
        "version": get_version(),
        "description": "A modern desktop interface for the OpenManus AI agent framework",
        "author": "OpenManus Redo Team",
        "author_email": "info@openmanus.example.com",
        "url": "https://github.com/example/openmanus-redo"
    }


def clean_build_dirs():
    """Clean build and dist directories"""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)


def build_macos_app(args):
    """Build macOS application using py2app"""
    clean_build_dirs()
    
    app_info = get_app_info()
    version = app_info["version"]
    
    print("Building macOS application...")
    
    # Create setup.py for py2app
    setup_py = f"""
from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets/images/icon.icns']),
    ('assets/images', [f for f in Path('assets/images').glob('*') if f.is_file()]),
    ('assets/icons', [f for f in Path('assets/icons').glob('*') if f.is_file()]),
    ('config', [f for f in Path('config').glob('*') if f.is_file()]),
]
OPTIONS = {{
    'argv_emulation': True,
    'plist': {{
        'CFBundleName': '{app_info["name"]}',
        'CFBundleDisplayName': '{app_info["name"]}',
        'CFBundleGetInfoString': '{app_info["description"]}',
        'CFBundleIdentifier': 'com.example.openmanus-redo',
        'CFBundleVersion': '{version}',
        'CFBundleShortVersionString': '{version}',
        'NSHumanReadableCopyright': '© {app_info["author"]}',
    }},
    'packages': [
        'PyQt6',
        'app',
        'app.agent',
        'app.flow',
        'desktop',
    ],
    'includes': [
        'PyQt6.QtCore', 
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'app.agent.manus',
        'app.flow.base',
        'app.flow.flow_factory',
    ],
    'iconfile': 'assets/images/icon.icns',
    'excludes': ['matplotlib', 'tkinter', 'PySide6'],
}}

setup(
    name='{app_info["name"]}',
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
    install_requires=['PyQt6'],
)
"""
    
    with open("setup_py2app.py", "w") as f:
        f.write(setup_py)
    
    # Run py2app
    build_type = "alias" if args.development else ""
    subprocess.run([sys.executable, "setup_py2app.py", "py2app", build_type], check=True)
    
    # Create a disk image if not in development mode
    if not args.development:
        print("Creating disk image...")
        app_name = app_info["name"].replace(" ", "")
        dmg_name = f"{app_name}_{version}"
        
        try:
            # Create temporary directory for DMG contents
            os.makedirs("dmg_contents", exist_ok=True)
            
            # Copy the app to the temporary directory
            shutil.copytree(
                f"dist/{app_info['name']}.app", 
                f"dmg_contents/{app_info['name']}.app",
                symlinks=True
            )
            
            # Create a symbolic link to Applications folder
            subprocess.run(
                ["ln", "-s", "/Applications", "dmg_contents/Applications"],
                check=True
            )
            
            # Create the DMG
            subprocess.run([
                "hdiutil", "create",
                "-volname", app_info["name"],
                "-srcfolder", "dmg_contents",
                "-ov", "-format", "UDZO",
                f"dist/{dmg_name}.dmg"
            ], check=True)
            
            print(f"Disk image created: dist/{dmg_name}.dmg")
            
            # Clean up
            shutil.rmtree("dmg_contents")
        except subprocess.SubprocessError as e:
            print(f"Error creating disk image: {e}")
    
    print("macOS build completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Build macOS application for OpenManus Redo")
    parser.add_argument("--development", action="store_true", help="Build in development mode (alias)")
    args = parser.parse_args()
    
    build_macos_app(args)


if __name__ == "__main__":
    main()


# scripts/build_linux.py
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def get_version():
    """Get the application version"""
    # You could read this from a version file or package
    return "0.1.0"


def get_app_info():
    """Get application information"""
    return {
        "name": "OpenManus Redo",
        "version": get_version(),
        "description": "A modern desktop interface for the OpenManus AI agent framework",
        "author": "OpenManus Redo Team",
        "author_email": "info@openmanus.example.com",
        "url": "https://github.com/example/openmanus-redo"
    }


def clean_build_dirs():
    """Clean build and dist directories"""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)


def build_linux_appimage(args):
    """Build Linux AppImage"""
    clean_build_dirs()
    
    app_info = get_app_info()
    version = app_info["version"]
    app_name = app_info["name"].replace(" ", "")
    
    print("Building Linux application...")
    
    # PyInstaller command
    pyinstaller_args = [
        "pyinstaller",
        "--name", app_name,
        "--windowed",
        "--icon", "assets/images/icon.png",
        "--add-data", "assets:assets",
        "--add-data", "config:config",
        "--hidden-import", "PyQt6",
        "--hidden-import", "app.agent.manus",
        "--hidden-import", "app.flow.base",
        "--hidden-import", "app.flow.flow_factory",
        "main.py"
    ]
    
    if args.onefile:
        pyinstaller_args.append("--onefile")
    else:
        pyinstaller_args.append("--onedir")
    
    # Run PyInstaller
    subprocess.run(pyinstaller_args, check=True)
    
    # Create AppDir structure
    appdir = Path("dist") / f"{app_name}.AppDir"
    os.makedirs(appdir, exist_ok=True)
    
    # Copy executable
    if args.onefile:
        shutil.copy(f"dist/{app_name}", appdir / "AppRun")
        os.chmod(appdir / "AppRun", 0o755)  # Make executable
    else:
        # For onedir, copy the whole directory
        for item in (Path("dist") / app_name).glob("**/*"):
            if item.is_file():
                dest = appdir / item.relative_to(Path("dist") / app_name)
                os.makedirs(dest.parent, exist_ok=True)
                shutil.copy2(item, dest)
        
        # Create AppRun script
        with open(appdir / "AppRun", "w") as f:
            f.write(f"""#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "$HERE/{app_name}" "$@"
""")
        os.chmod(appdir / "AppRun", 0o755)  # Make executable
    
    # Copy icon
    os.makedirs(appdir / "usr/share/icons/hicolor/256x256/apps", exist_ok=True)
    shutil.copy("assets/images/icon.png", appdir / f"usr/share/icons/hicolor/256x256/apps/{app_name}.png")
    shutil.copy("assets/images/icon.png", appdir / f"{app_name}.png")
    
    # Create desktop file
    with open(appdir / f"{app_name}.desktop", "w") as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name={app_info["name"]}
Comment={app_info["description"]}
Exec=AppRun
Icon={app_name}
Categories=Office;
Terminal=false
""")
    
    # If linuxdeploy and appimagetool are available, create AppImage
    try:
        if shutil.which("linuxdeploy") and shutil.which("appimagetool"):
            print("Creating AppImage...")
            subprocess.run([
                "linuxdeploy",
                "--appdir", appdir,
                "--output", "appimage",
                "--icon-file=assets/images/icon.png",
                "--desktop-file=" + str(appdir / f"{app_name}.desktop")
            ], check=True)
            print(f"AppImage created in dist/ directory")
        else:
            print("linuxdeploy or appimagetool not found. Install them to create an AppImage.")
            print("AppDir created in dist/ directory")
    except subprocess.SubprocessError as e:
        print(f"Error creating AppImage: {e}")
    
    print("Linux build completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Build Linux AppImage for OpenManus Redo")
    parser.add_argument("--onefile", action="store_true", help="Create a single executable file")
    args = parser.parse_args()
    
    build_linux_appimage(args)


if __name__ == "__main__":
    main()
