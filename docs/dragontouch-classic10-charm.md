# Dragon Touch Classic10 Charm (Frameo): root ADB over Wi-Fi and the WebView kiosk

Report from **one unit**, tested on **16–17 October 2026** using an **Apple silicon Mac,
macOS 27.0** with platform-tools 37.0.1. The owner bought it from
[Amazon US, ASIN B0GTLPX5LC](https://a.co/d/0elUZPxy). The listing identifies the
purchase, not a guarantee that another unit has this firmware.

**Verified result:** root ADB was reachable over Wi-Fi with no authorization prompt, and
the shell has full root capabilities. After a private, verified backup of the critical
partitions, the repository's native kiosk (`dashboard/kiosk`) was installed and runs the
hosted dashboard full-screen through the shipped WebView 106 — no browser, no WebView
swap, no boot patch, and nothing written outside `/data`. The kiosk is the frame's only
`android.intent.category.HOME` handler, so it comes up at boot (see
[the HOME finding](#no-app-on-this-unit-claims-home)).

## Identity and observations

| Item | Observed value |
| --- | --- |
| Model in properties | `Classic10 charm` |
| Firmware build | `Classic10 charm_A33M_20260323-1608_V01` |
| Android / SDK | `6.0.1` / `23` |
| Manufacturer / board / hardware | `joyhong` / `exdroid` / `sun8i` |
| Build fingerprint | `joy/astar_ococci/astar-ococci:6.0.1/MOB30R/20260323:user/test-keys` |
| CPU ABI | `armeabi-v7a` |
| Display / density | `1280x800` / `160` |
| Stock app | Frameo, `net.frameo.frame` v1.29.14 (60300) — **not** VPhoto |
| Vendor test app | `com.joyhong.test` v2.0.34 (the owner's "ADB mode" setting lives here) |
| Vendor updater | `com.waophoto.fota` |
| Stock WebView | `106.0.5249.126` — modern; the repo kiosk runs as is |
| ADB shell identity | `uid=0(root)`, context `u:r:su:s0`, full capabilities (`CapEff: ffffffffffffffff`) |
| SELinux | Permissive |
| Other | `/sbin/busybox` present; `com.android.systemui` ships **disabled** (no status or navigation bar); no VPhoto; `pm list packages -3` empty out of the box; `/system/xbin/su` present but not setuid (untested — the shell is already root) |

This is a different model from the
[Dragon Touch Modern10 Charm](dragontouch-modern10-charm.md) (VPhoto, WebView 44) and from
the [Frameo 102K](frameo-102k-a33.md), though all three are Allwinner A33 `astar_*` boards.
The chip was not physically inspected. The partition map matches the 102K's from
`bootloader` (p2, 32 MiB at sector 73728) through `recovery` (p9); `cache` is 256 MiB and
the partitions after it sit at different offsets. The eMMC user area is 30,777,344 sectors
(15,758,000,128 bytes) — the same size as the Modern10 Charm unit. There is no p4; a
2-sector `mmcblk0p3` sits at sector 1.

## ADB access

With the frame on Wi-Fi, TCP port 5555 was open at boot (`service.adb.tcp.port=5555`) and
`adb connect <frame-ip>:5555` returned a root shell immediately — no authorization prompt,
and none could appear: `com.android.systemui` is disabled, so there is no UI to show one.
The same no-AUTH-over-Wi-Fi signature was reported for the Modern10 Charm and for the
Classic15 Pro (issue #146). `persist.sys.usb.config=mtp,adb` suggests a USB gadget config,
but the only USB port observed is a USB-A receptacle, and a USB-A-to-USB-C cable to the
Mac enumerated nothing — the same result as the Modern10 Charm report. USB ADB was not
pursued further; Wi-Fi was enough.

**Security hand-off:** this is an unauthenticated root shell open to anyone who can reach
the frame on the network. Keep it on a trusted LAN, never port-forward it, and re-check
the ADB toggle in the vendor app (or block the port) before putting it on an untrusted
network.

## Backup

Before installing anything, every partition except `UDISK` (`/data`) and `cache` was read
over ADB and verified: exact byte counts, SHA-256, gzip readback hash, and fresh re-reads
of each partition plus a 16 MiB sample 128 MiB into `system` (avoiding the mutable ext4
superblock). All checks matched, and a second `system` sample read an hour later was
byte-identical, so the filesystem was not being written while running. `mmcblk0boot0` and
`mmcblk0boot1` (4 MiB each) were captured too. `/sbin/busybox dd` was used throughout, so
the >2 GiB `dd` limit noted for the Modern10 Charm never applied.

A pipeline trap worth recording: **this device's `adbd` appends busybox `dd`'s statistics
line to `adb exec-out` stdout** (`32+0 records in` / `32+0 records out`, 25–41 trailing
bytes depending on digit count). The payload is intact and the junk is strictly trailing,
but any exact-size `cmp` against the stream phantom-fails unless the stream is truncated
to the partition's exact size first (`… | head -c <size> | cmp - image`). Small partitions
"match" by accident because both sides carry the same tail; a sliced compare against a
clean range is where it bites. Trimming the saved images to their exact sizes and
re-verifying produced the matching hashes.

## No app on this unit claims HOME

The complete `dumpsys package` output contains **zero** `android.intent.category.HOME`
filters on this build — Frameo included — and `<preferred-activities />` in
`package-restrictions.xml` is empty. Frameo starts by its own mechanism at boot, not via
the HOME intent. Consequences:

- After installing the kiosk and running it with the `home` extra, it is the **only**
  HOME handler: no chooser ever appears and `am start -c android.intent.category.HOME`
  goes straight to the kiosk. (On the 102K, Frameo claims HOME and a chooser appears.)
- With `com.android.systemui` disabled there is no navigation bar, so the kiosk's
  accessibility **Home HQ navigation** service (floating Back/Dashboard buttons) is the
  only way back from other apps. Enabled with root:

  ```sh
  adb shell pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS
  adb shell settings put secure enabled_accessibility_services com.wesbos.homehq/com.wesbos.homehq.NavigationService
  adb shell settings put secure accessibility_enabled 1
  ```

  The service was confirmed bound (`dumpsys accessibility`) and the buttons visible in a
  Settings screenshot outside the kiosk. The two-finger gesture itself was not tested;
  per README rule 9 the owner should still check the menu and buttons by hand on the
  panel, since screencaps do not prove touch input.

## What was set up (all owner-approved writes)

| Change | Undo |
| --- | --- |
| `adb install -r dashboard/kiosk/build/homehq.apk` (built from this repo, `minSdk 23`) | `adb uninstall com.wesbos.homehq` |
| Dashboard URL saved and HOME alias enabled: `am start -n com.wesbos.homehq/.MainActivity --es url <url> --ez home true` (demo URL in this trial) | `am start -n com.wesbos.homehq/.MainActivity --ez home false` |
| `WRITE_SECURE_SETTINGS` grant, so the kiosk re-adds its navigation service itself | `pm revoke com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS` |
| Accessibility service enabled (commands above) | disable in Settings → Accessibility |
| `pm disable com.waophoto.fota` (updater disabled while the frame is online) | `pm enable com.waophoto.fota` |
| `settings put global stay_on_while_plugged_in 7` (previous value `0`) | `adb shell settings put global stay_on_while_plugged_in 0` |

The dashboard was verified rendering full-screen by screenshot after install, with the
correct date and time (the clock-jump behaviour seen on the Modern10 Charm has not been
observed here, but it was only checked once). Frameo and the vendor test app remain
installed and enabled; Frameo just does not claim HOME on this build, so it never comes
back unless started explicitly.

## Not tested

- Factory-reset behaviour and firmware restore (backups exist; restore is unproven).
- USB ADB through other cables, or the `mtp,adb` gadget config on a device-mode port.
- A second computer with a fresh ADB key (the no-key-check observation is one host only).
- Whether other units from this listing ship this firmware.
- The kiosk HOME role and the FOTA disable across a real reboot (state verified only).
