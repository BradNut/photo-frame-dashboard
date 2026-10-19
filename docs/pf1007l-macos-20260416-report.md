# PF1007L / AiMOR 6.0.78 / 20260416: T3c root ADB, then persistent USB ADB, no boot patch

One USB-C-only unit on April `20260416` firmware, tested from macOS. Stock ADB was off, network
ADB was refused, and the FEL stub card darkened the screen but never produced a FEL device.
[T3c](pf1007l-start-here.md#t3c-temporary-adb-through-the-aimor-connection) then gave temporary
root ADB over Wi-Fi, and `setprop persist.sys.usb.config mass_storage,adb` made root USB ADB
survive a cold boot. Nothing was written to the eMMC outside `/data` to get access; the WebView
swap and boot fixes later wrote `/system`.

## Unit report

```text
About model / firmware: PF1007L, firmware 321-OS-AIMOR.0.20260416 (full string as shown in Settings → About)
AiMOR version: 6.0.78 (code 78)
Ports (DC jack, or USB-C only): USB-C only
Cable and port that gave USB data (or none): some USB-A-to-USB-C cables only. Two cables into a Mac USB-A port (one through a USB-C-to-USB-A adapter) gave 1f3a:1000 / 1f3a:1002. Another A-to-C cable in the same port powered the frame but carried no data (the frame's android_usb state stayed DISCONNECTED).
T3 USB IDs seen / adb devices output: 1f3a:1000 (product "Android") seen on USB after boot, stayed connected about 4 min. `adb devices -l` lists no device.
T3b network ADB result (port 5555): refused (nc -vz -w 3), with the frame on Wi-Fi at a LAN address, vendor server blocked on the router before it joined. Frame answers ping.
T4 sunxi-fel version output (or skipped): `ERROR: Allwinner USB FEL device not found!` after the FEL stub was written to a 16 GB SDHC card (readback verified; stub SHA-256 2ccec08a…, 8192 bytes at offset 8192) and the card was seated in the frame's TF slot. Watched probe (polling every 0.2 s): 1f3a:efe8 never appeared in three windows, with the direct USB-A port, the adapter chain, and the recessed reset button held during plug-in. The screen stayed dark, and no U-Boot or Android boot was observed after insertion.
T5 check-dump stage / chunks (or skipped): skipped
eMMC size in sectors: 30,777,344
Boot partition start sector: 172032 (p6, 65,536 sectors)
Boot image SHA-256 (sector 172032, 31,028 sectors): bef19d67da122b8034670fcd73483c916ef30c6112b9503025a2a05f11d5dbc9 (31,032 sectors: fc4d22d2d595817e3b3de14bc44715f3a91ebb004233ca1017e703dbcd64514d)
Route used and result: T3c (dns.py + server.py, unchanged) gave root ADB over Wi-Fi; then persist.sys.usb.config=mass_storage,adb; after a cold boot USB 1f3a:1002, adb -d shell id -> uid=0(root)
Host OS: macOS (Darwin 27.0.0), adb from Homebrew android-platform-tools
First failed step and its exact output: T3b: "nc: connectx to <frame-ip> port 5555 (tcp) failed: Connection refused"
```

Later failed step: T4 `sunxi-fel version`: "ERROR: Allwinner USB FEL device not found!"

Fingerprint: `AEEZO/astar_m86_8723cs/astar-m86_8723cs:6.0.1/MOB30R/20260416:eng/test-keys`,
`ro.debuggable=1`, `ro.build.display.id` `astar_m86_8723cs-eng 6.0.1 MOB30R 20260416 test-keys.1`.
Both boot hashes match the `20260416` row of the firmware table.

## T3c on `20260416`

The procedure in [pf1007l-20260410-network-adb.md](pf1007l-20260410-network-adb.md) worked
unchanged. The offline tests passed and `server.py --dry-run` built the expected 73-byte packet.

- **Router:** TP-Link Deco. Its WAN DNS setting refuses a LAN address ("This IP conflicts with the
  LAN IP Subnet. To use this DNS Server, set it at the DHCP Server"). Setting the Mac as primary
  DNS under **Advanced → DHCP Server** (secondary blank) worked. Clients then ask the Mac
  directly, so `dns.py` needs the frame's own address (`--clients-file`), not the router's.
  `dns.py` silently drops clients that aren't listed, so any other device that renews its lease
  in that window loses DNS. Keep the window short and restore the DHCP DNS before stopping
  `dns.py`.
- **No static IP:** AiMOR's Wi-Fi screen has no Modify network option and long-press does nothing,
  so DNS could not be set on the frame alone.
- **Timing:** the frame's AiMOR connected and received the command while the owner was toggling
  Wi-Fi. The frame came back on a new address, and ADB on 5555 was already listening there.
- **macOS:** `adb connect` first failed with `No route to host` while `nc` reached port 5555.
  `adb kill-server` fixed it. A long-running `adb` server seems to lack Local Network access.

## Persistent USB ADB

`setprop persist.sys.usb.config mass_storage,adb` (the `20260410` #83 and `20260529` #117 method)
took effect immediately (`sys.usb.state=mass_storage,adb`). After a cold boot (cable unplugged
and replugged), the frame enumerated as `1f3a:1002` and `adb -d shell id` returned `uid=0(root)`.
Undo: `setprop persist.sys.usb.config mass_storage`.

## Backup over ADB: `dd` stops at 2 GiB

The full eMMC was backed up before any further change, in MD5-checked chunks with on-device
`gzip -1`. There was no independent re-read, no `0xCC` check and no SHA-256 of the whole image,
so this backup does not meet the [backup rule](../README.md#rules-we-learned-the-hard-way). The stock `dd` (`/system/bin/dd`) returns **zero bytes** for any read that starts past
2 GiB, on `/dev/block/mmcblk0` and on the 13 GB `/data` partition alike, with no error. Comparing
on-device and host MD5s does not catch this, because both sides hash the same empty stream:
check the byte count too. `/sbin/busybox dd` reads past 2 GiB correctly.

| Path | Speed |
| --- | --- |
| Wi-Fi ADB, raw | about 0.5 MB/s (128 MiB in 252 s, signal −45 dBm) |
| USB ADB, raw | about 8 MB/s (256 MiB in 32 s) |

## Lock-down (T8)

After a reboot the frame's AiMOR had an established connection to the vendor on TCP 7806, even
though the router was meant to block it. The in-memory `vendor_block` rule plus a force-stop
closed it. Rootless Launcher 3.9.1 (SHA-256 matched the guide) was installed and confirmed on the
panel, including Settings. Then `com.efercro.os.aimor`, `com.yhk.qeota` and `com.DeviceTest`
were disabled; `package-restrictions.xml` showed `enabled="2"` for all three on the first check.
After a cold boot: Rootless was Home, USB root ADB worked, the three packages stayed disabled
and not running, and `netstat` showed nothing on 7806 or 5555. `getenforce` reported `Disabled`
with AiMOR off.

## WebView 106 and the kiosk

Stock WebView was 44.0.2403.119. Section 6 of the
[PF1007L guide](allwinner-a33-pf1007l.md#6-upgrade-webview-before-using-the-kiosk) worked as
written: the APK hash matched, the three `lib/armeabi-v7a` libraries went to `lib/arm`, and
`/system` had 405,820 KiB free. After a cold boot `dumpsys package` reported
`versionName=106.0.5249.126`, `WebViewFactory` loaded `/system/app/webview/lib/arm/libwebviewchromium.so`
with no `dlopen failed`, and the Home HQ kiosk (built with JDK 17 and build-tools 34 on macOS)
rendered the demo over `adb reverse` on the panel. Density was already 160. External HTTPS
images failed with `net_error -202`, as the guide warns.

**Run the two `mv` commands once.** Here the swap command was run twice by accident: the second
run moved the new live tree *into* `/system/homehq-stock-webview/webview` and left no
`/system/app/webview` at all. It was fixed with one `mv` back before rebooting. Step 4 of the
[guide's swap](allwinner-a33-pf1007l.md#6-upgrade-webview-before-using-the-kiosk) already says to
refuse existing staging or rollback paths; follow it.

## Boot fixes

[pf1007l-boot-fixes.md](pf1007l-boot-fixes.md) installed over USB ADB with `install.sh apply`
(`MAC` empty, so derived from the serial; `WIFI_DEFER=1`; `POWER_FIX=0`, since the frame was
on a Mac USB-A port). The TP-Link Deco did not answer NTP (`sntp` timed out), so
`NTP_SERVER=time.google.com`. `install.sh check` passed on this firmware. After one power-cycle,
`install.sh verify` passed: the configured MAC replaced the driver's random `88:00:33:…` address
before association, Wi-Fi started at 39.9 s uptime, the clock was right and
`/data/local/frame-lasttime` was written. One boot only; repeated and power-cut boots were not
tested.

## Earlier attempts compared with other reports

- [#119](https://github.com/wesbos/photo-frame-dashboard/issues/119), the same `20260416`
  firmware on Windows, did get FEL and finished Route U with a 12 MHz low-power U-Boot. This unit
  never showed FEL, so the firmware alone does not explain it. The cable result above suggests
  the T4 cables may not have carried data; T4 was not retried with the cable that later worked.
- A dark screen with the stub card and no USB device also matches the second unit in
  [allwinner-a33-pf1007l.md](allwinner-a33-pf1007l.md#second-unit-usb-c-only-no-dc-jack).
