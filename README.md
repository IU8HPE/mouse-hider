# HPE - Mouse Hider

A lightweight Windows utility that hides the mouse cursor after inactivity and restores it instantly on movement.

This package includes two ready-to-run builds:

- `MouseHider_x64.exe` (full UI, PySide6, 64-bit Windows)
- `MouseHiderLite_x86.exe` (minimal UI, Tkinter, 32-bit Windows)

## Why Two Builds

Some older devices still run 32-bit Windows and cannot execute modern x64 applications.

- Use `x64` build on Windows 10/11 64-bit.
- Use `x86 Lite` build on Windows 32-bit systems.

## Features

- Global mouse inactivity monitoring
- Configurable timeout (`1` to `300` seconds, default `10`)
- Cursor hide on idle, instant restore on movement
- Start/Stop monitoring button
- `Start minimized`
- `Start with Windows` (current user, registry `HKCU\...\Run`)
- `Start monitoring at launch`
- Optional `Auto-minimize 5s after cursor hidden`
- Safe shutdown with cursor restore
- Persistent settings in `config.json` next to executable

## Download / Run

Executables are in:

- `bin/MouseHider_x64.exe`
- `bin/MouseHiderLite_x86.exe`

Integrity hashes are in:

- `docs/SHA256SUMS.txt`

## Quick Start

1. Choose the correct build for the target PC architecture.
2. Copy the `.exe` to a local folder (not a temporary download folder).
3. Run as normal user.
4. Set timeout and click `Start`.
5. Optionally enable `Start with Windows`.

For step-by-step instructions:

- `docs/QUICK_START.md`

## Compatibility Matrix

- Windows 10/11 x64: use `MouseHider_x64.exe`
- Windows 10 32-bit: use `MouseHiderLite_x86.exe`
- CPU x64 + OS 32-bit: still requires `x86` build

## Troubleshooting

See:

- `docs/TROUBLESHOOTING.md`

Common examples covered:

- "This app can't run on your PC"
- Cursor not hiding on specific systems
- Startup entry issues

## Build From Source

Build instructions are in:

- `docs/BUILD.md`

Source code and build assets are in:

- `source/`

## Release Notes

- `docs/RELEASE_NOTES.md`

## Privacy

This tool does not send telemetry or network data.  
It operates locally and stores only local settings in `config.json`.

## Author

Andrea

## License

MIT License. See `LICENSE`.
