# LifeOS Build Guide

## Requirements
- Python 3.10+
- Windows 10/11

## Install Dependencies

```bash
# Create virtual environment
python -m venv C:\lifeos_venv

# Activate
C:\lifeos_venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller
```

## Build EXE

### Option 1: Using build script
```bash
build.bat
```

### Option 2: Manual build
```bash
pyinstaller lifeos.spec --noconfirm --clean
```

### Output
- EXE: `dist\lifeos\lifeos.exe`
- Size: ~500MB (includes all dependencies)

## Run

```bash
# From source
lifeos --help

# From EXE
dist\lifeos\lifeos.exe --help
```

## CI/CD

GitHub Actions workflow automatically:
1. Runs tests on push/PR
2. Builds Windows EXE on main branch
3. Creates release with EXE

## Troubleshooting

### PyInstaller fails
- Ensure all dependencies are installed
- Check `lifeos.spec` for missing imports
- Run with `--debug` flag for verbose output

### EXE too large
- Use `--strip` option in spec
- Exclude unused packages
- Use UPX compression

### Missing DLLs
- Install Visual C++ Redistributable
- Check `hiddenimports` in spec
