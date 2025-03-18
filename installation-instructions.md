# OpenManus Redo: Installation Guide

This guide will help you set up and run the OpenManus Redo desktop application.

## Prerequisites

- Python 3.12 or newer
- OpenManus framework
- Qt dependencies for your operating system

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/openmanus-redo.git
cd openmanus-redo
```

### 2. Create a Virtual Environment

#### Using venv
```bash
python -m venv venv
```

#### Activate the virtual environment:

- **Windows**:
  ```bash
  venv\Scripts\activate
  ```

- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Link or Copy OpenManus Framework

The desktop application expects the OpenManus framework in the `app` directory. You can either:

- **Symlink** existing OpenManus installation:
  ```bash
  ln -s /path/to/your/openmanus/app app
  ```

- **Copy** OpenManus code:
  ```bash
  cp -r /path/to/your/openmanus/app app
  ```

### 5. Configure the Application

Create a configuration file:

```bash
cp desktop/utils/config.example.toml desktop/utils/config.toml
```

Edit `desktop/utils/config.toml` with your preferred settings.

### 6. Run the Application

```bash
python main.py
```

## Building Standalone Applications

### Windows

```bash
python scripts/build_windows.py
```

The executable will be created in the `dist` directory.

### macOS

```bash
python scripts/build_macos.py
```

The `.app` bundle will be created in the `dist` directory.

### Linux

```bash
python scripts/build_linux.py
```

The AppImage will be created in the `dist` directory.

## Development Setup

For development, you may want to install additional tools:

```bash
pip install -r requirements-dev.txt
```

This includes:
- pytest for testing
- flake8 for linting
- black for code formatting

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black desktop/ scripts/ tests/
```

## Troubleshooting

### Missing Qt Dependencies

If you encounter errors related to PyQt6, ensure you have the proper Qt dependencies installed:

- **Windows**: No additional dependencies needed
- **macOS**: `brew install qt`
- **Ubuntu/Debian**: `sudo apt-get install python3-pyqt6 pyqt6-dev-tools`
- **Fedora**: `sudo dnf install python3-qt6`

### OpenManus Integration Issues

If you have trouble with OpenManus integration:

1. Ensure you're using a compatible version of OpenManus
2. Check your `config.toml` file for proper API configurations
3. Verify that all required dependencies for OpenManus are installed

### Visual Issues

If the UI appears incorrect:

1. Ensure you're using a supported version of PyQt6
2. Try resetting the configuration file
3. Check system theme compatibility settings

## Getting Help

If you encounter any problems, please:

1. Check the application logs in `openmanus_redo.log`
2. Submit an issue on the GitHub repository with details about your environment and the problem you're facing
3. Join our community Discord server for real-time support

## License

OpenManus Redo is licensed under the MIT License. See the LICENSE file for more details.
