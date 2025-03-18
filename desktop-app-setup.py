from setuptools import setup

APP = ['desktop_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'PyQt6',
        'app',
        'app.agent',
        'app.flow',
    ],
    'includes': ['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    'iconfile': 'assets/icon.icns',  # Create this icon file for macOS
}

setup(
    name="OpenManus Desktop",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
