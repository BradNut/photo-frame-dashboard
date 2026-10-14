# PF1007L / AiMOR 6.0.78 / 20260416: USB data yes, no ADB over USB or network (T3, T3b)

About model / firmware: PF1007L, firmware 321-OS-AIMOR.0.20260416 (full string as shown in Settings → About)
AiMOR version: 6.0.78 (code 78)
Ports (DC jack, or USB-C only): USB-C only
Cable and port that gave USB data (or none): USB-C-to-USB-A adapter plus USB-A-to-USB-C data cable, into a Mac USB-A port (1f3a:1000 seen). A direct USB-A-to-USB-C cable into a Mac USB-A port later showed no frame device.
T3 USB IDs seen / adb devices output: 1f3a:1000 (product "Android") seen on USB after boot, stayed connected about 4 min. `adb devices -l` lists no device.
T3b network ADB result (port 5555): refused (nc -vz -w 3), with the frame on Wi-Fi at a LAN address, vendor server blocked on the router before it joined. Frame answers ping.
T4 sunxi-fel version output (or skipped): `ERROR: Allwinner USB FEL device not found!` after the FEL stub was written to a 16 GB SDHC card (readback verified; stub SHA-256 2ccec08a…, 8192 bytes at offset 8192) and the card was seated in the frame's TF slot. Watched probe (polling every 0.2 s): 1f3a:efe8 never appeared in three windows, with the direct USB-A port, the adapter chain, and the recessed reset button held during plug-in. The screen stayed dark, and no U-Boot or Android boot was observed after insertion.
T5 check-dump stage / chunks (or skipped): skipped
eMMC size in sectors: unknown (not read)
Boot partition start sector: unknown (not read)
Boot image SHA-256 (sector 172032, 31,028 sectors): not read
Route used and result: none completed. T3b failed; T3c not tried (needs the vendor server reachable; conflicts with the router block). Route U (FEL stub on TF card) was started and stopped at T4: the FEL device never enumerated, so no eMMC backup was attempted.
Host OS: macOS (Darwin 27.0.0), adb from Homebrew android-platform-tools
First failed step and its exact output: T3b: "nc: connectx to <frame-ip> port 5555 (tcp) failed: Connection refused"

Later failed step: T4 `sunxi-fel version`: "ERROR: Allwinner USB FEL device not found!"

Notes: the frame's USB device dropped for about 3 seconds at one point and came back as 1f3a:1000, then stayed up. Stock ADB was off on this unit. Its Wi-Fi MAC changed at each boot, and its address changed with it.

