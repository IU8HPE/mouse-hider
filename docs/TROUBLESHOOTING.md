# Troubleshooting

## "This app can't run on your PC"

Cause: architecture mismatch.

- If OS is 32-bit, run `MouseHiderLite_x86.exe`
- If OS is 64-bit, run `MouseHider_x64.exe`

Tip: CPU can be x64 but OS may still be 32-bit.

## Cursor does not hide

1. Make sure monitoring is started (`Start` clicked).
2. Confirm status changes from `Active` to `Idle`.
3. Wait full timeout value.
4. Ensure no third-party software is forcing custom cursor behavior.
5. Test with default Windows cursor theme.

## Cursor remains hidden after an abnormal crash

The app restores cursors on clean exit.  
If the process is forcibly terminated by the OS:

1. Relaunch the app and click `Stop`.
2. Or sign out / sign in to Windows.
3. Or reboot.

## Startup with Windows not working

The app writes startup entry to:

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

Checks:

1. Ensure current user has registry write access.
2. Re-toggle `Start with Windows` checkbox.
3. Verify path is local and executable still exists.

## Slow old devices

Use the lite x86 build for old 32-bit systems:

- `MouseHiderLite_x86.exe`

It has a simpler UI toolkit and lower overhead.
