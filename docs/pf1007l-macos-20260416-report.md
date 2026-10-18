# PF1007L / AiMOR 6.0.78 / 20260416: USB data yes, no ADB over USB or network, no FEL from the stub card (T3, T3b, T4)

One USB-C-only unit on April `20260416` firmware, tested from macOS. Stock ADB was off, network
ADB was refused, and the FEL stub card darkened the screen but never produced a FEL device.
No route completed and nothing was written to the frame.

## Unit report

```text
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
```

Later failed step: T4 `sunxi-fel version`: "ERROR: Allwinner USB FEL device not found!"

## Notes

- The frame's USB device dropped for about 3 seconds at one point and came back as `1f3a:1000`,
  then stayed up.
- Its Wi-Fi MAC changed at each boot, and its address changed with it.
- Only the adapter chain ever gave USB data. The FEL attempts used both that chain and the direct
  cable, so a cable or port problem has not been ruled out for T4.

## Compared with other reports (not tested on this unit)

- [#119](https://github.com/wesbos/photo-frame-dashboard/issues/119), the same `20260416`
  firmware on Windows, did get FEL and finished Route U with a 12 MHz low-power U-Boot. So the
  firmware alone does not explain the missing FEL device.
- A dark screen with the stub card and no USB device also matches the second unit in
  [allwinner-a33-pf1007l.md](allwinner-a33-pf1007l.md#second-unit-usb-c-only-no-dc-jack). That unit had no USB
  data at all. This one shows `1f3a:1000` in Android.
- Not tried yet: [T3c](pf1007l-start-here.md#t3c-temporary-adb-through-the-aimor-connection)
  (tested on `20260410` and `20260529`, not `20260416`), and the read-only
  [T5](pf1007l-start-here.md#t5-route-s-sd-boot-and-emmc-dump-test-read-only-on-the-frame)
  Route S dump, which needs no USB. Route S's write accepts only the January boot image, so stop after the dump.
