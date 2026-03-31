# Mouse Hider Build Guide

## 1) Full UI (64-bit) - PySide6

Build machine requirements:
- Windows 10/11 x64
- Python x64 (recommended 3.12+)

Commands:

```powershell
cd C:\Tools\hide_mouse
py -3.12 -m pip install -r requirements_x64.txt
py -3.12 -m PyInstaller --noconfirm --clean MouseHider64.spec
```

Output:
- `dist\MouseHider_x64.exe`

## 2) Lite UI (32-bit) - Tkinter

Build machine requirements:
- Windows 32-bit (or any machine with Python x86 installed)
- Python **x86** (for example `3.11-32` or `3.12-32`)

If Python x86 is missing, you can install local x86 runtime in this project folder:

```powershell
cd C:\Tools\hide_mouse
.\install_py311x86.cmd
```

Commands:

```powershell
cd C:\Tools\hide_mouse
.\build_lite32.cmd
```

Output:
- `dist\MouseHiderLite_x86.exe`

Notes:
- The x86 executable must be built with an x86 Python interpreter.
- The lite build keeps the same core behavior (timeout, hide/restore cursor, config.json, autostart, clean exit) with a simpler UI toolkit.
