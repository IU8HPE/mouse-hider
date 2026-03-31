# Release Notes

## v1.0.0

Initial public package with dual-build distribution:

- Added full `x64` build (`MouseHider_x64.exe`) with PySide6 UI
- Added lite `x86` build (`MouseHiderLite_x86.exe`) with minimal Tkinter UI
- Idle timeout configurable from `1` to `300` seconds (default `10`)
- Start/Stop monitoring
- Instant cursor restore on movement
- Settings persistence in `config.json`
- Startup options:
  - Start minimized
  - Start with Windows
  - Start monitoring at launch
  - Auto-minimize after cursor hidden
- Separate autostart keys for x64 and x86 variants to avoid conflicts
- Added publication bundle with checksums and build docs

### Reliability updates

- Improved cursor hide/restore strategy for broader compatibility across old systems
- Clean restore behavior on normal app shutdown
