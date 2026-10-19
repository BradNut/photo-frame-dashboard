# Skyrhyme 168 (10.1" Frameo, RK3126, Android 6.0.1)

Record of one unit, bought new on [eBay](https://www.ebay.com/itm/920018877467), 2026-10-18, macOS host
(Mac mini). Observations are kept separate from guesses.
Unique identifiers (serial, MAC, IP) are left out; they live in the ignored `backups/` and `frames/`
folders.

**Short version:** same SoC, vendor (Harmony / ZhiHeXing build tree, `rk915` Wi-Fi) and partition
layout as the [Rollei Smart Frame 107](rollei-smartframe-107.md), but with the old WebView 44 of the
[Denver PFF-1015](denver-pff-1015.md). Frameo's ADB toggle turns on ADB over USB **and** the network
(port 5555), and the shipped `su` gives root with no prompt. `scripts/biuframe-setup.sh check`
refuses this unit by design (different fingerprint). Two quirks matter: the firmware's `daemonsu`
service restarts every 5 s and remounts `/system` each time, and Frameo keeps two root shells open.

## Observations (read-only unless noted)

### Identity

| | |
| --- | --- |
| About screen | `Skyrhyme 168`, Frameo v1.32.12 (78070); it updated itself to v1.32.16 (80320) once online |
| Brand / model | `ro.product.brand=hmcx_dpf`, model `K1003BTCX`, device `rk312x`, product `hm_rk312x`, manufacturer `rockchip` |
| Firmware | `K1003BTCX.user.2023-12-05+18:57:06` |
| Fingerprint | `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.zhihec.20231205.185505:user/release-keys` |
| SoC | Rockchip RK3126 (`ro.board.platform=rk312x`, `ro.hardware=rk30board`), 32-bit (`armeabi-v7a`) |
| Kernel | Linux 3.10.0, built by `zhihec` |
| Android | 6.0.1, API 23, security patch 2016-07-05, `user` build, `ro.debuggable=0`, `ro.secure=1`, `ro.adb.secure=1` |
| SELinux | Permissive |
| Display | 1280x800, 160 dpi |
| RAM / storage | about 1 GB RAM (`MemTotal: 1024192 kB`), 128 MB zram, 29 GB eMMC (`mmcblk0`), userdata 27 GB. Not a low-RAM build (`ro.config.low_ram` unset) |
| WebView | `com.android.webview` 44.0.2403.119 in `/system/app/webview`, too old for the dashboard |
| Wi-Fi | Onboard radio works (`wlan0`, 2.4 GHz), driver module `rk915` |
| SystemUI | `com.android.systemui` is **disabled**: no status or navigation bar |
| Frameo | `net.frameo.frame`, the HOME app. System APK `/system/priv-app/v1.19.3_frameo.apk`, updated in `/data/app` |
| Ports | Barrel-jack power, micro-USB, microSD, reset button |

### USB and ADB

- **ADB:** the owner turned on Frameo's ADB access toggle in Frameo's settings. With it on, `sys.usb.config` and
  `persist.sys.usb.config` are `adb`.
- **The same toggle turns on network ADB.** The vendor init script sets
  `service.adb.tcp.port 5555` at every boot (`/init.rk30board.rc:132`), so whenever `adbd` runs it
  also listens on port 5555. `adbd` only runs while the USB config includes `adb`
  (`/init.usb.rc`), so with the toggle off there should be no network ADB either (not tested).
- **USB** is the micro-USB port, with an ordinary micro-USB data cable: `2207:0006`, product name
  `K1003BTCX`, 480 Mb/s.
- **Authorization:** `adb connect <frame-ip>:5555` printed `failed to authenticate`, then listed
  the frame as `device` (authorized). `/data/misc/adb/adb_keys` then held the Mac's key next to a
  factory key from another computer. The owner saw no prompt on the screen (SystemUI is disabled,
  so there is nothing to show one). What wrote the key is not known (see Guesses).

### Root

`adb shell su -c id` and `adb shell su 0 id` both return `uid=0(root)` with no prompt.
`/system/xbin/su` and `/system/xbin/daemonsu` (133,472 bytes each, dated 2023-12-05) ship in the
firmware. **Any app on the frame can probably get root without asking.**

**Frameo holds root.** `net.frameo.frame` (uid 10015) has two `su` children, served by
`daemonsu:10015`, which keep two root `sh` processes open for as long as Frameo runs.

**`daemonsu` restart loop.** `/init.rc:747` runs `service daemonsu /system/xbin/daemonsu
--auto-daemon`. A `daemonsu:master` from an earlier start is already running, so each new start
exits, and init restarts it about every 5 s (`init.svc.daemonsu=restarting`). Each start remounts
`/system` read-write and back, and touches `/system/xbin/su` and `daemonsu`. **`/system` is
mounted read-write for a moment every few seconds, so a power cut at the wrong time can damage it.**

- The ext4 mount count of `system` went from 12,046 to 12,381 in about 30 minutes, 3 more every
  15 s, with or without ADB activity.
- Consequence: **`system` never hashes the same twice.** Two reads differ only in MiB 0 (the
  superblock and the two `su` inodes) and MiB 513-514 (the journal). The other 1,021 MiB matched
  the backup exactly.
- Consequence: a write to `/system` can find it read-only again between two commands. Remount
  read-write before each write and check the result (see Changes made).

### Software of interest

| Package | Location | Notes |
| --- | --- | --- |
| `net.frameo.frame` v1.32.16 | system app, updated in `/data/app` | Slideshow app and HOME activity. Cloud connected, holds root shells. |
| `android.rockchip.update.service` | system | Rockchip updater, running. |
| `com.cghs.stresstest` | system | Factory stress test, running. |
| `com.DeviceTest` | system | Factory test app. |

No Adups FOTA, no browser, no third-party apps.

### Partition table (eMMC `mmcblk0`, 512-byte sectors)

From `mtdparts` on the kernel command line; eMMC sector = loader sector + 8192. Identical to the
[Rollei 107](rollei-smartframe-107.md#partition-table-emmc-mmcblk0-512-byte-sectors), including
`userdata` starting at eMMC sector 2,842,624.

| Partition | Name | Start | Size (sectors) |
| --- | --- | --- | --- |
| p1 | uboot | 16384 | 8192 |
| p2 | misc | 24576 | 8192 |
| p3 | resource | 32768 | 32768 |
| p4 | kernel | 65536 | 24576 |
| p5 | boot | 90112 | 24576 |
| p6 | recovery | 114688 | 65536 |
| p7 | backup | 180224 | 131072 |
| p8 | cache | 311296 | 262144 |
| p9 | metadata | 573440 | 32768 |
| p10 | kpanic | 606208 | 8192 |
| p11 | system | 614400 | 2097152 |
| p12 | radical_update | 2711552 | 131072 |
| p13 | userdata | 2842624 | rest |

## Backup (2026-10-18, verified)

eMMC sectors 0-2,842,624, everything before `userdata`: 1,455,423,488 bytes raw, 320 MB gzipped.

- Taken over **network ADB** before the working USB cable turned up. Plain `dd` over Wi-Fi ran at
  about 0.3 MB/s; compressing on the frame (`dd ... | busybox gzip -1` inside `su -c`, streamed with
  `adb exec-out`) took 23 minutes for the whole range.
- Exact length on readback, `gzip -t` passes (gzip's CRC covers the data as read on the frame), no
  512-byte sector entirely `0xCC`, `ANDROID!` headers on `boot` and `recovery`.
- Independent re-reads over USB (`busybox sha256sum` on the frame) match the backup for the loader
  area (sectors 0-16383), `uboot`, `misc`, `resource`, `kernel`, `boot`, `recovery`, `backup`,
  `kpanic` and `radical_update`. `system` differs only in the 3 MiB the `daemonsu` loop rewrites
  (see Root). `cache` and `metadata` are mounted read-write and were not re-read.

| Image | SHA-256 |
| --- | --- |
| `boot` (p5, `ANDROID!` header) | `c991e4f6d83ad9168626bdd765d02f5870b7e94021d6a77168daa440c4c8bb9f` |
| `recovery` (p6, `ANDROID!` header) | `a685c0cb28054b515b53a99292dbf82a305e072c525b635c440e020c9b918ac2` |
| `kernel` (p4) | `fc2c78d04dcb979423404f8465d145b279f88390e553ef70c5eacde5569c2305` |

Hashes cover the whole partition, padding included. Restore would need Rockchip loader mode and
`rkdeveloptool`; neither has been tried on this unit.

## Status against the README phase map

| Phase | State |
| --- | --- |
| 1 Identify | Done. Not a BIUFRAME; its setup script refuses this fingerprint. |
| 2 ADB | Done: Frameo's ADB toggle, over USB (once a data cable was found) and the network. |
| 3 Loader mode | Not needed. Not tested. |
| 4 Back up | Done and verified (see Backup). Restore path untested. |
| 5 Root | Shipped `su` works. |
| 6 Make it useful | Done: WebView 106, and the kiosk is the Home app and boots into the dashboard. |
| 7 Networking | Onboard Wi-Fi works. |
| 8 Vendor updates | Done: Rockchip updater and Frameo disabled. |
| 9 Security hand-off | Done (see Security notes). |

## Changes made to the frame (2026-10-18)

Made after the verified backup, one at a time, each followed by a reboot and a check.

| Change | How | Undo |
| --- | --- | --- |
| Rockchip updater off | `su -c 'pm disable android.rockchip.update.service'` | `su -c 'pm enable android.rockchip.update.service'` |
| Stress test off | `su -c 'pm disable com.cghs.stresstest; pm hide com.cghs.stresstest'` | `su -c 'pm unhide com.cghs.stresstest; pm enable com.cghs.stresstest'` |
| Device test off | `su -c 'pm disable com.DeviceTest'` | `su -c 'pm enable com.DeviceTest'` |
| WebView 44 → 106.0.5249.126 | The BIUFRAME `step_webview` files: same pinned LineageOS APK, `lib/arm/*.so` extracted, `oat/` removed, `webview.apk.bak` kept. Run as a script that remounts `/system` read-write before **each** command (the `daemonsu` loop remounts it read-only every 5 s), then MD5s checked against the source | Copy `webview.apk.bak` back, `rm -rf lib`, reboot |
| Kiosk installed | `adb install -r dashboard/kiosk/build/homehq.apk`, unmodified build of `main` | `adb uninstall com.wesbos.homehq` |
| Kiosk as Home | `am start -n com.wesbos.homehq/.MainActivity --ez home true`, then on the frame: Home chooser → Home HQ → Always | Pick another Home app in Settings → Apps → Default apps, then the same command with `--ez home false` |
| Frameo off | `su -c 'pm disable net.frameo.frame'`, after the owner checked by hand that the kiosk menu reaches Android Settings → Apps (README rule 9) | `su -c 'pm enable net.frameo.frame'` (its data is untouched) |

After the WebView reboot: `versionName=106.0.5249.126`, and `RelroFileCreator` loads
`/system/app/webview/lib/arm/libwebviewchromium.so` with no `Failed to load library`.

After the final reboot: the resumed activity is `com.wesbos.homehq/.Home`, all four packages are
`enabled=2`, none of them is running, and USB and network ADB both work. The first page load fails
with `ERR_INTERNET_DISCONNECTED` until Wi-Fi is up; the kiosk's retry then loads it.

**Wait about 10 s after `pm disable` before rebooting.** Android 6 writes
`/data/system/users/0/package-restrictions.xml` about 10 s after a change, and `adb reboot` does not
flush it. The first time Frameo was disabled the frame was rebooted within seconds, and Frameo came
back enabled. Checking that the file shows `enabled="2"` before rebooting fixed it.

The dashboard's demo HTTPS certificate chains to GlobalSign Root CA through GTS Root R4. GlobalSign
Root CA is in this frame's CA store (valid until 2028), so the Let's Encrypt roots step was not
needed for the demo URL.

## Guesses (unverified)

- What added the Mac's key to `adb_keys` with no prompt on the screen: Frameo's ADB access
  feature through its root shells, or a vendor change to `adbd`. Not tested with Frameo disabled or
  from a second computer.
- Whether network ADB is really off while Frameo's ADB toggle is off. `/init.usb.rc` stops `adbd`
  when the USB config is `none`, which suggests so.
- Why the `daemonsu` service loops: it may expect to be the first start, while `daemonsu:master` was
  started earlier in boot (its parent is init).

## Security notes for the owner

- `su` gives root with no prompt, so any app installed on this frame can take root. Install nothing
  untrusted.
- With ADB on, network ADB listens on port 5555 with root `su`. Whether unknown keys are rejected
  is untested, and `adb_keys` already holds a factory host's key, so **treat 5555 as open to the
  factory and possibly to anyone on the network.** Keep the frame on an isolated guest or IoT network.
- Android 6.0.1 with a 2016-07 security patch; SELinux is permissive.
- Frameo self-updates while online and runs root shells. Disabling it stops both; re-enabling it
  (or a factory reset) brings them back.
- Check for `/system/bin/iotv` and a `run_iotv` service: the [Runxion RK3126](runxion-zn-dp1002-rk3126.md#hidden-root-agent-iotv) shares this partition layout and ships that hidden root agent. Not checked on this unit.

## Host note

macOS, Mac mini. The kiosk built with Homebrew `openjdk@17` and the `android-commandlinetools`
cask (build-tools 34.0.0, platform 34), with `JAVA_HOME=/opt/homebrew/opt/openjdk@17`.
