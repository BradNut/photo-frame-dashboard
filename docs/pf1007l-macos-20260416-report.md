# PF1007L / AiMOR 6.0.78 / 20260416: USB data yes, no ADB over USB or network (T3, T3b)

About model / firmware: PF1007L, firmware 321-OS-AIMOR.0.20260416 (full string as shown in Settings → About)
AiMOR version: 6.0.78 (code 78)
Ports (DC jack, or USB-C only): USB-C only
Cable and port that gave USB data (or none): USB-C-to-USB-A adapter plus USB-A-to-USB-C data cable, into a Mac USB-C port (1f3a:1000 seen; no direct USB-A test yet)
T3 USB IDs seen / adb devices output: 1f3a:1000 (product "Android") seen on USB after boot, stayed connected about 4 min. `adb devices -l` lists no device.
T3b network ADB result (port 5555): refused (nc -vz -w 3), with the frame on Wi-Fi at a LAN address, vendor server blocked on the router before it joined. Frame answers ping.
T4 sunxi-fel version output (or skipped): skipped
T5 check-dump stage / chunks (or skipped): skipped
eMMC size in sectors: unknown (not read)
Boot partition start sector: unknown (not read)
Boot image SHA-256 (sector 172032, 31,028 sectors): not read
Route used and result: none. Stopped at T3b. T3c not tried (needs the vendor server reachable; conflicts with the router block).
Host OS: macOS (Darwin 27.0.0), adb from Homebrew android-platform-tools
First failed step and its exact output: T3b: "nc: connectx to <frame-ip> port 5555 (tcp) failed: Connection refused"

