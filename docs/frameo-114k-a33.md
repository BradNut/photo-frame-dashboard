# Frameo "Digital Photo Frame 114K" (Allwinner A33 `astar_xr819`, Android 6.0.1)

Record of one unit, tested on 2026-10-14. Host: macOS 27 on Apple silicon. Observations are kept
separate from guesses. The serial, MAC address and IP address are left out.

**Short version:** USB ADB works, but only through a powered USB hub. The shipped `/system/bin/su`
gives UID 0 with `su 0 <cmd>`, but without the capabilities to set the clock or remount `/system`.
WebView 106 is preinstalled, so the [kiosk](../dashboard/kiosk/README.md) runs as is.
`setprop persist.adb.tcp.port 5555` keeps ADB on Wi-Fi across reboots, and the key check is
enforced over Wi-Fi. Nothing was written to `/system` or the boot partition.

**Same board family as the [Frameo 102K](frameo-102k-a33.md) and the [Uhale 114KZ](uhale-114kz.md).**
The fingerprint (`astar_xr819`, build date `20231010`) is identical to the Uhale 114KZ's, and the
firmware string shares its `114119_HK9365_SWM0810` prefix. The brand property is `ALONG`, as on the
102K, and the partition starts match the 102K's. The box and label name the maker as Shenzhen
Kejinming; no build property mentions Kejinming. Check the fingerprint before following any of these pages.

## Identity

| Item | Observed value |
| --- | --- |
| Sold as | Frameo "Digital Photo Frame 114K" (Shenzhen Kejinming). Listing not recorded |
| `adb devices -l` | `product:Digital Photo Frame model:Digital_Photo_Frame device:Digital Photo Frame` |
| Brand / manufacturer | `ro.product.brand=ALONG`, `ro.product.manufacturer=Allwinner` |
| Firmware | `ro.build.display.id=114119_HK9365_SWM0810_frameo_v1.29.13_20260114` |
| Fingerprint | `Allwinner/astar_xr819/astar-xr819:6.0.1/MOB30R/20231010:eng/test-keys`. `ro.build.type` is `user` |
| SoC | Allwinner A33 (`ro.board.platform=astar`, `ro.hardware=sun8i`), board `exdroid` |
| Kernel | Linux 3.4.39, `#398 SMP PREEMPT`, built 2026-01-14 |
| Android | 6.0.1, security patch 2016-07-05 |
| Display | 1280x800, density 160, `ro.sf.rotation=90` |
| RAM | 1,026,980 kB. `ro.config.low_ram=true` and `ro.config.512m=true` are set anyway (effect not tested; there is no `/system/etc/lowmem_package_filter.xml`) |
| eMMC | 61,341,696 sectors (the same count as the Uhale 114KZ); `/data` 26.8 GB |
| Wi-Fi | XR819 (`xradio_wlan`, `xradio_core`). Works |
| Frameo | `net.frameo.frame` v1.29.13 (60080), in `/system/priv-app/Manufacturertest` |
| WebView | `com.android.webview` 106.0.5249.126 in `/system/app/webview` |
| SELinux | Permissive |
| Time zone | `persist.sys.timezone` and `ro.frameo.default.timezone` are `America/New_York` in `/system/build.prop` |

## Hardware

- **Sensors:** `mir3da` accelerometer (used for auto-rotate) and a "Temperature sensor" that is
  the SoC thermal sensor (`sunxi-ths`). No light, proximity or motion sensor.
- **Cameras:** none. The camera HAL (`V4L2Camera Module`) loads but reports 0 devices, and there is
  no `/dev/video*`.
- **Input:** `gslX680` touch, `axp22-supplyer` (power key), `headset`, `sunxi-ths`, `mir3da`.
- **Power:** no battery (`dumpsys battery`: present false). **No RTC battery:** after a power cut the
  clock starts at 1969-12-31. The SoC RTC (`sunxi-rtc`) keeps time across a warm `adb reboot`.
- USB Ethernet modules are loaded (`asix`, `cdc_ether`, `mcs7830`, `qf9700`); not tested.

## USB

| Host side | Cable | Result |
| --- | --- | --- |
| Mac USB port directly | USB-A to USB-C | The Mac can't power the frame; no usable connection |
| Anker 332 USB-C hub, with a charger on its PD-IN port | USB-A to USB-C data cable | Enumerates as `1f3a:1001`. `adb devices` shows `device` |

`dumpsys battery` reports `USB powered: true` through the hub. Guess, not verified: like the
[Uhale 114KZ](uhale-114kz.md#usb-configuration-and-power-problem), this board draws more than a
bare Mac port gives it, and the hub's charger fills the gap.

USB ADB was turned on with Frameo's own toggle: Settings → About → Beta Program → ADB Access.
With the hub setup above, the Mac connected at once, with no prompt on screen (SystemUI ships
disabled, so no prompt could appear). Afterwards `/data/misc/adb/adb_keys` held exactly one key,
the Mac's. Guess, not verified: Frameo's toggle, or this build's `adbd`, accepts the first USB host
and saves its key. A second computer over USB was not tried; over Wi-Fi a new key is refused (see
[Persistent ADB over Wi-Fi](#persistent-adb-over-wi-fi)).

**Warning:** the first computer to connect over USB was authorized with no prompt, and it gets root
through `su`. Plug the frame only into computers you trust until your own key is saved.

## ADB and root

- `/system/build.prop`: `ro.adb.secure=1`, `persist.sys.usb.config=adb,mtp`,
  `persist.service.adb.enable=1`. `/default.prop`: `ro.secure=1`, `ro.debuggable=0`.
  At runtime `persist.sys.usb.config` read `mtp,adb` and `sys.usb.config=adb`.
- `adbd` runs as `shell`. `adb root` is blocked. `service.adb.tcp.port` and
  `persist.adb.tcp.port` are empty out of the box, so nothing listens on 5555.
  `adb tcpip 5555` works until the next reboot.
- `/system/bin/su` is setuid root (17,920 bytes). `su 0 id` gives `uid=0(root)`, context `u:r:shell:s0`.
  `su -c` is not supported.
- **`su 0` keeps only `CAP_SETUID` and `CAP_SETGID`** (`CapEff: ffffffe0000000c0`), as on the
  [102K](frameo-102k-a33.md#root) and the [Uhale 114KZ](uhale-114kz.md#uid-0-does-not-provide-all-root-capabilities). In practice:
  - `date -s` can't work (no `CAP_SYS_TIME`), and `/system` can't be remounted (no `CAP_SYS_ADMIN`).
  - Root can't read files it doesn't own. `su 0 dd` of `misc` and `frp` fails; `su 1000 dd` reads them.
    `su 0` also can't read `/data/system/users/0/package-restrictions.xml`; `su 1000` can.
  - `su 0 pm disable` and `su 0 setprop persist.*` work.

### Persistent ADB over Wi-Fi

```sh
adb shell su 0 setprop persist.adb.tcp.port 5555     # undo: su 0 setprop persist.adb.tcp.port "" and reboot
```

The value is stored in `/data/property/persist.adb.tcp.port`. After an `adb reboot` and after a
30-second power cut, `adb connect <frame-ip>:5555` gave `device` without `adb tcpip`, about 50 s
after power-on. `adbd` listens on `0.0.0.0:5555` and USB ADB keeps working.

Keep a frame with persistent network ADB on an isolated network. Anyone holding an authorized key
gets root over Wi-Fi.

**The key check is enforced over Wi-Fi.** A second adb server with a freshly generated key that the
frame had never seen got `failed to authenticate` / `unauthorized`. The authorized Mac connected
normally. This differs from the [Joyhong](joyhong-jt101f-i02.md#adb-and-root) and the
[102K](frameo-102k-a33.md#adb), where the key check appeared to be off.

Once, right after a reboot, a Wi-Fi ADB shell failed with `error: closed` while the TCP connection
was established. `adb disconnect` then `adb connect` fixed it.

## Clock

Android's own `NetworkTimeUpdateService` does the job; no boot script is needed. With
`auto_time=1`, it polls about once a minute until it succeeds (the `...NetworkTimeUpdateService.action.POLL`
alarm in `dumpsys alarm`), then every 24 hours. After a power cut, the logs start at `12-31 19:00`, and
`UsageStatsService: Time changed` appeared about 42 s after boot.

On this unit the frame sits behind a firewall that allows only UDP 123 out. Each poll showed up
in conntrack (`su 0 cat /proc/net/nf_conntrack`) as a request to port 123 marked `[UNREPLIED]`,
which showed the frame was trying and the network was dropping it. The cause was the firewall's
rule order. After the rules were reordered, the clock synced within a minute.

Notes for frames that can't reach an NTP server:

- `su 0 date -s` won't work here (see [ADB and root](#adb-and-root)). The repo's
  [`frame-timesync.sh`](../scripts/pf1007l-boot/device/frame-timesync.sh) also won't work unchanged:
  this build's toybox `nc` has no `-u` (UDP) option, and there is no `/system/xbin/nc`.
- Guess, not tested: `su 0 service call alarm 2 i64 <epoch-ms>` (AlarmManager `setTime`) should
  work, because the permission check happens in `system_server` and UID 0 passes it.

## Software of interest

| Package | Location | Notes |
| --- | --- | --- |
| `net.frameo.frame` v1.29.13 | `/system/priv-app/Manufacturertest` | Frameo, and the default **HOME** app. No `INSTALL_PACKAGES`. Offline it keeps trying `connect.frameo.biz` and Crashlytics |
| `com.adups.fota` 5.28 | `/system/app/FotaUpdate` | Adups FOTA. Holds `RECOVERY` and `REBOOT`, starts at boot, has an FCM push service. `ro.fota.oem=alongA33_6.0` |
| `com.softwinner.dragonfire` | `/system/app/DragonFire` | Allwinner factory test. Holds `INSTALL_PACKAGES`, `DELETE_PACKAGES` and `REBOOT` |
| `com.softwinner.dragonaging`, `dragonphone`, `com.along.factorytest`, `com.android.agingtest` | `/system/app`, `/system/priv-app` | Factory and aging tests |
| `com.android.launcher` (Launcher2) | `/system/priv-app/Launcher2` | **Not a Home app on this build.** Its `com.android.launcher2.Launcher` intent filter is only `MAIN` + `MONKEY` (no `HOME`), so the kiosk's **Open launcher** falls back to Android Settings |
| `com.android.browser` | `/system/app/Browser` | Stock browser |
| `com.android.systemui` | `/system/priv-app/SystemUI` | Present, disabled out of the box |

## Partition table

eMMC `mmcblk0`, 512-byte sectors, from `/sys/block/mmcblk0/mmcblk0p*/start`. The starts are the same
as the [102K](frameo-102k-a33.md#partition-table)'s, and `/data` is larger, as the eMMC is.

| Partition | Name | Start | Size (sectors) |
| --- | --- | --- | --- |
| p2 | bootloader | 73728 | 65536 |
| p5 | env | 139264 | 32768 |
| p6 | boot | 172032 | 32768 |
| p7 | system | 204800 | 2097152 |
| p8 | misc | 2301952 | 32768 |
| p9 | recovery | 2334720 | 65536 |
| p10 | cache | 2400256 | 1572864 |
| p11 | metadata | 3973120 | 32768 |
| p12 | private | 4005888 | 32768 |
| p13 | frp | 4038656 | 1024 |
| p14 | empty | 4039680 | 31744 |
| p15 | alog | 4071424 | 163840 |
| p16 | media_data | 4235264 | 32768 |
| p1 | UDISK (`/data`) | 4268032 | 57073664 |

## Boot image

Stock, read before any change and never written.

| Item | Value |
| --- | --- |
| Header | `ANDROID!`, page 2048, kernel 10,221,792 bytes, ramdisk 4,650,744 bytes, no second stage, empty cmdline |
| Android image (first 14,876,672 bytes) SHA-256 | `4d503349ea948ebfd91573c1de2d646b82c63ab403eac590c420e3125d01bb1b`. The rest of the partition is zeros |
| Boot partition (16 MiB) SHA-256 | `85fdb88071e045e053c44600bd922119945d3c222f0daa1c9f2f1c341d4ec023` |
| 31,028 sectors from 172032 SHA-256 | `d4dd5fdb9b673a03f0545543937832019349e2b00405db9b046747d3416213f9` |

## Backup

Every partition except `UDISK` and `cache`, plus raw eMMC sectors 0 to 73,727, was read over USB ADB:

```sh
adb exec-out "su 0 dd if=/dev/block/by-name/<name> bs=1048576" > <name>.img   # su 1000 for misc and frp
```

Every image's MD5 matched `md5sum` on the frame. Fresh re-reads of `boot`, `bootloader` and the first
64 MiB of `system` matched, and no 1 MiB block is all `0xCC`. This is not the README's full eMMC backup:
nothing written in this session needed it, because all changes are in `/data`.

## What was set up (approved writes, all in `/data`)

| Step | Command | Undo |
| --- | --- | --- |
| Persistent Wi-Fi ADB | `su 0 setprop persist.adb.tcp.port 5555` | `su 0 setprop persist.adb.tcp.port ""`, reboot |
| Disable the vendor updater | `su 0 pm disable com.adups.fota` | `su 0 pm enable com.adups.fota` |
| Install the kiosk alongside Frameo | `adb install homehq.apk` (only change: `DEFAULT_URL`) | `adb uninstall com.wesbos.homehq` |
| Navigation buttons | Owner enabled Settings → Accessibility → Home HQ navigation; `pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS` | `pm revoke` the same, turn the service off |
| Offer the kiosk as Home | `am start -n com.wesbos.homehq/.MainActivity --ez home true` | the same with `--ez home false` |
| Disable Frameo | `su 0 pm disable net.frameo.frame` | `su 0 pm enable net.frameo.frame` |

**`pm disable` was lost on the first try.** The package showed `enabled=2` and its process stopped,
but after an `adb reboot` it was enabled and running again, with no entry for it in
`package-restrictions.xml`. The second time, the entry was checked on disk before rebooting
(`su 1000 grep com.adups.fota /data/system/users/0/package-restrictions.xml` →
`enabled="2" enabledCaller="shell:0"`), and it survived the reboot. Guess, not verified: the first
reboot came before PackageManager's delayed write of that file.

### Kiosk

The kiosk was built with `kiosk/build.sh` (Homebrew `openjdk@17`, `android-commandlinetools`,
build-tools 34.0.0, platform 34) without problems. `test-navigation.py` passed. Installing it did not
make it a Home app.

The dashboard is a Home Assistant page over plain HTTP on the LAN, so the 2016 certificate store
did not matter. Home Assistant's login page and dashboard render in WebView 106. With "Keep me
logged in" checked, the login survived `am force-stop com.wesbos.homehq` and a relaunch.
`screencap` captures the WebView. Chromium logs `eglChooseConfig failed with error EGL_BAD_ATTRIBUTE`
at start, with no visible effect.

The owner checked by hand on the panel that the two-finger hold opens the Home HQ menu with
**Open launcher**, **Android settings**, **Wi-Fi settings** and **Reload dashboard**.

The floating **Back** and **Dashboard** buttons from the navigation service worked in Android Settings
(checked by the owner on the panel).

At the first launch the screen was off. Guess, not verified: Frameo's night sleep schedule
(`net.frameo.frame/.feature.sleep_schedule.StandbyBroadcastReceiver` holds an alarm).
`input keyevent KEYCODE_WAKEUP` turned it on.

### Kiosk as Home, Frameo disabled

Out of the box there is no saved Home preference, yet Frameo starts as Home with no chooser:
Frameo was the only Home app, because Launcher2 has no `HOME` category here (see
[Software of interest](#software-of-interest)). Enabling the kiosk's Home alias while Frameo was
enabled changed nothing visible. After `pm disable net.frameo.frame` (checked on disk in
`package-restrictions.xml` first), the Home key went straight to `com.wesbos.homehq/.Home`. No
chooser appeared and no preferred activity was saved, because Home HQ was the only Home app.

After a 30-second power cut the frame booted into the dashboard on its own. Home HQ started about
30 s after power-on, its first loads failed with `ERR_INTERNET_DISCONNECTED`, it retried every 5 s,
logged `Wi-Fi connected, retrying now` about 15 s later, and then showed the dashboard, still logged
in. NTP set the clock, Wi-Fi ADB came back and the navigation service was bound.

## Not tested

- Whether `ro.config.low_ram=true` kills the kiosk when it is in the background.
- Whether a second computer is accepted over USB without a prompt (see [USB](#usb)).
- `service call alarm 2` as a way to set the clock without NTP.
- USB-C to USB-C, and USB Ethernet.

## Second unit (sold as 101K)

Record of one unit, tested on 2026-10-15. Host: macOS 27 on an Apple M4 Mac mini.
Observations are kept separate from guesses. The serial, MAC addresses and eMMC CID are left
out; they stay in the owner's ignored `backups/` and `diagnostics/` folders.

**Short version:** Frameo's About screen lists the hardware as `101k`. ADB Access in Frameo's
Beta Program, then an authorisation prompt over USB. The shipped `/system/bin/su` gives UID 0 with
`su 0 <cmd>`. `setprop persist.adb.tcp.port 5555` as root keeps network ADB on across a power
cycle, so after one USB session the frame was used over Wi-Fi only. WebView 106 is preinstalled.
No boot patch, FEL or SD card was needed, and nothing was written to `/system` or the boot
partition. Adups FOTA and Frameo were then disabled, the kiosk set as Home, and ISRG Root X1 added
to the *user* trust store so WebView 106 accepts current Let's Encrypt chains.

**The hard part was power, not access.** The frame has one USB-C port for both power and data, and
restarted in a loop when powered from the Mac through a USB-C to USB-A adapter. See [USB and
power](#usb-and-power-101k).

### Identity (101K)

| Item | Observed value |
| --- | --- |
| Frameo About | Hardware `101k`, Frameo `v1.29.13 (60080)` |
| `adb devices -l` | `product:Digital Photo Frame model:Digital_Photo_Frame device:Digital Photo Frame` |
| Brand / manufacturer | `ro.product.brand=ALONG`, `ro.product.manufacturer=Allwinner` |
| Firmware | `ro.build.display.id=114119_HK9365_SWM0810_frameo_v1.29.13_20260114` |
| Fingerprint | `Allwinner/astar_xr819/astar-xr819:6.0.1/MOB30R/20231010:eng/test-keys`. `ro.build.type` is `user` |
| FOTA identity | `ro.fota.oem=alongA33_6.0`, `ro.fota.platform=AW_A33_6.0`, `ro.fota.device=Digital Photo Frame`, `ro.fota.version` = the firmware string |
| SoC | Allwinner A33 (`ro.board.platform=astar`, `ro.hardware=sun8i`, `ro.sys.cputype=QuadCore-A33`), Cortex-A7 (`CPU part 0xc07`), 32-bit ARMv7 |
| Board | `ro.product.board=exdroid` |
| Kernel | Linux 3.4.39, `#398 SMP PREEMPT`, built 2026-01-14 |
| Android | 6.0.1, API 23, security patch 2016-07-05 |
| Display / GPU | 1280x800, density 160, `ro.sf.rotation=90`. `ARM, Mali-400 MP, OpenGL ES 2.0` |
| RAM | 1,026,980 kB |
| Storage | eMMC `mmcblk0`, 60,620,800 sectors; `/data` 26.4 GB |
| Wi-Fi | XR819 (`xradio_wlan`, `xradio_core`, `xradio_mac` modules). Round-trip times of 100–470 ms on a home network; network ADB reads ran at roughly 200 KB/s |
| Power | `dumpsys battery`: AC powered, no battery present |
| Sensors / input | `mir3da` and `mc32x0` accelerometer modules, `gslX680new` touch. USB Ethernet modules (`asix`, `cdc_ether`, `mcs7830`, `qf9700`) are loaded; not tested |
| Frameo | `net.frameo.frame` v1.29.13, in `/system/priv-app/Manufacturertest` |
| Vendor updater | `com.adups.fota` |
| WebView | `com.android.webview` 106.0.5249.126 |
| SELinux | Permissive |
| Time zone | `ro.frameo.default.timezone=America/New_York`; `persist.sys.timezone` became `<local zone>` after Frameo setup |

#### Closest relatives in this repo

- The [114K unit above](#identity): **the same firmware string and fingerprint.** That unit's eMMC
  is larger (61,341,696 sectors), it showed no ADB prompt (this one did), and it needed a powered hub
  for USB. Its findings on `su` capabilities, `pm disable` persistence and the Wi-Fi key check
  probably apply here too; they were not all repeated on this unit.
- [Uhale 114KZ](uhale-114kz.md): the firmware string starts with the same
  `114119_HK9365_..._SWM0810` and has the same date (`20260114`), with Uhale in place of Frameo.
  That unit was unstable on USB data (a suspected power limit, as here) and needed a boot ramdisk
  patch for network ADB. On this unit, root `setprop` was enough.
- [Frameo 102K (A33)](frameo-102k-a33.md): the same `astar_xr819` fingerprint family, brand, Frameo
  version, WebView and `su` behaviour. Its firmware string starts with `102K-MS33-HK9365`. The
  partition layout matches except for the size of `UDISK`.

### USB and power (101K)

- One USB-C port (power and data) and one USB-A host port. The USB-A port is a host port and can't
  be used to reach ADB.
- **USB-C to USB-C (Mac mini to frame): no power and no data.** Guess: the frame's USB-C port has no
  CC pull-down resistors, so a USB-C source never turns on VBUS.
- **USB-A to USB-C cable through a USB-C to USB-A adapter on the Mac mini: data works, but the
  frame flickered and restarted in a loop.** `adb devices` showed `unauthorized` in the short
  windows when it was up.
- A Steam Deck dock with no charger on its PD input made it worse (the frame stayed up for less
  time).
- What worked: a different USB-A to USB-C cable, through the same adapter on the Mac. The frame's
  Wi-Fi was off at the time. It stayed up long enough to authorise the host key and run the
  commands below. Guess: the second cable dropped less voltage.
- After `persist.adb.tcp.port` was set, USB was no longer needed: the frame runs from its own
  adapter and is reached over Wi-Fi.

### ADB (101K)

- Frameo → Settings → About → Beta Program → ADB Access turns on USB ADB.
- `ro.adb.secure=1`. An "Allow USB debugging?" prompt appeared on screen once the frame stayed
  powered long enough; "Always allow" was ticked. SystemUI ships disabled on this build and the
  114K above saw no prompt, so this may have been Frameo's own dialog; not confirmed.
- Before any change, `service.adb.tcp.port` and `persist.adb.tcp.port` were empty and port 5555
  was closed on the network (`adb connect` gave `Connection refused`).
- `su 0 setprop persist.adb.tcp.port 5555`, then `adb tcpip 5555`. `adb connect <frame-ip>:5555`
  worked at once.
- **After a power cycle on the frame's own adapter with no USB** (uptime 79 s),
  `service.adb.tcp.port` was empty, `persist.adb.tcp.port` was `5555`, and `adb connect` worked. So
  `adbd` on this build reads `persist.adb.tcp.port` at start.
- Network ADB still checks the host key (`ro.adb.secure=1`); only the authorised computer was
  tested on this unit. On the [114K above](#persistent-adb-over-wi-fi), with the same firmware, a
  freshly generated key was refused over Wi-Fi.
- Keep a frame with persistent network ADB on an isolated network. Anyone holding an authorized key
  gets root over Wi-Fi.
- `persist.sys.usb.config=mtp,adb`; at runtime `sys.usb.config=adb`.

### Root (101K)

- `/system/bin/su` is setuid root (`-rwsr-sr-x root root`, 17,920 bytes). No `/system/xbin/su`.
- `su 0 id` gives `uid=0(root)`, context `u:r:shell:s0`, over USB and over network ADB.
  `su -c id` fails with `invalid uid/gid '-c'`.
- As on the [102K](frameo-102k-a33.md#root), use `su 1000` to read `misc` and `frp`, which are
  owned by `system`.

`su` is setuid with no manager app and no prompt, so treat every app on this frame as if it has root.

### Partition table (101K)

eMMC `mmcblk0`, 512-byte sectors, from `/sys/block/mmcblk0/mmcblk0p*/{start,size}` and
`/dev/block/by-name`.

| Partition | Name | Start | Size (sectors) |
| --- | --- | --- | --- |
| p2 | bootloader | 73728 | 65536 |
| p5 | env | 139264 | 32768 |
| p6 | boot | 172032 | 32768 |
| p7 | system | 204800 | 2097152 |
| p8 | misc | 2301952 | 32768 |
| p9 | recovery | 2334720 | 65536 |
| p10 | cache | 2400256 | 1572864 |
| p11 | metadata | 3973120 | 32768 |
| p12 | private | 4005888 | 32768 |
| p13 | frp | 4038656 | 1024 |
| p14 | empty | 4039680 | 31744 |
| p15 | alog | 4071424 | 163840 |
| p16 | media_data | 4235264 | 32768 |
| p1 | UDISK (`/data`) | 4268032 | 56352768 |

All rows except `UDISK` match the [102K](frameo-102k-a33.md#partition-table). This unit's eMMC is
smaller (60,620,800 sectors), and `UDISK` is shorter by the difference.

### Boot image (101K)

Stock, read before any change and never written. **Identical to the 114K's** ([Boot image](#boot-image) above).

| Item | Value |
| --- | --- |
| Header | `ANDROID!`, page 2048, kernel 10,221,792 bytes, ramdisk 4,650,744 bytes, no second stage |
| Android image (first 14,876,672 bytes) SHA-256 | `4d503349ea948ebfd91573c1de2d646b82c63ab403eac590c420e3125d01bb1b`. The rest of the partition is zeros |
| Boot partition (16 MiB) SHA-256 | `85fdb88071e045e053c44600bd922119945d3c222f0daa1c9f2f1c341d4ec023` |

### Backup (101K)

Every partition except `UDISK` and `cache`, plus raw eMMC from sector 0 for 36 MiB, was read over
network ADB (about 200–400 KB/s; 1.25 GiB took about an hour):

```sh
adb exec-out "su 0 dd if=/dev/block/by-name/<name> bs=1048576 2>/dev/null" > <name>.img   # su 1000 for misc and frp
```

Every image passed: exact size (`/sys/block/mmcblk0/<part>/size` × 512), an MD5 match with
`md5sum` on the frame, no 1 MiB block that is all `0xCC`, fresh re-reads of `boot`, `bootloader`
and `env` with the same SHA-256, and gzip copies that pass `gzip -t` and decompress to the same
SHA-256. No read needed a retry.

A first attempt stopped partway through `bootloader` when the read was interrupted; the partial file
was deleted. A short read is caught by the size check.

### Vendor apps

- `su 0 pm disable com.adups.fota` and later `su 0 pm disable net.frameo.frame`. Both show
  `enabled="2" enabledCaller="shell:0"` in `/data/system/users/0/package-restrictions.xml` (read with
  `su 1000`). Both stayed disabled across two reboots, and four hours after the last one neither
  had a process or an alarm (`ps`, `dumpsys alarm`). The 114K above lost its first `pm disable`
  to an early reboot; checking that file before rebooting avoids that.
- Before Frameo was disabled it kept running behind the kiosk: it set `screen_brightness` back to
  15 and held its own 22:00 sleep-schedule alarm (`StandbyBroadcastReceiver`).
- SystemUI ships disabled (no navigation bar).

### Kiosk as Home

The repo's [kiosk](../dashboard/kiosk/README.md) installed and ran with the owner's URL. With
Frameo still enabled, pressing Home showed a chooser between Frameo and Home HQ; the owner picked
Home HQ and **Always**. After Frameo was disabled, Home still opened Home HQ, and after a power
cycle the dashboard was on screen about 58 s after boot. The navigation service needed
`pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS` and the owner enabling it
in Accessibility; the owner checked by hand that its Dashboard button returns from Android Settings.

### HTTPS: Let's Encrypt root in the user store

The dashboard is served from `workers.dev` and fetches ESPN over HTTPS. WebView 106 rejected
both with `net_error -202` (`ERR_CERT_AUTHORITY_INVALID`): the `workers.dev` chain was
YE1 → Root YE → ISRG Root X2 → ISRG Root X1, and Android 6's store has no ISRG root.

The [BIUFRAME guide](biuframe-setup-guide.md) adds the roots to `/system`. Here they were added to
the **user** store instead, which needs no `/system` write.

| Item | Value |
| --- | --- |
| Source | <https://letsencrypt.org/certs/isrgrootx1.pem> |
| SHA-256 fingerprint | `96:BC:EC:06:26:49:76:F3:74:60:77:9A:CF:28:C5:A7:CF:E8:A3:C0:AA:E1:1A:8F:FC:EE:05:C0:BD:DF:08:C6` (matches letsencrypt.org and the macOS system store) |
| File name | `6187b673.0` (`openssl x509 -noout -subject_hash_old`) |
| Path | `/data/misc/user/0/cacerts-added/6187b673.0`, `system:system 0644` |
| Folder | `cacerts-added` did not exist; created as `system`, `0755` |

`/data/misc/user/0` belongs to `system`, so `su 1000` is used for it (`su 0` gets `Permission
denied` listing the folder). Android 6 apps trust the user store whatever SDK they target, and the repo's kiosk also opts in
on newer Android through its network security config. The `/system` route in the BIUFRAME guide
works too. After a kiosk force-stop the dashboard
loaded with no X509 errors in `logcat`. Undo: `su 1000 rm` the file (and `rmdir` the folder), then
force-stop the kiosk. ISRG Root X2 was not added; X1 was enough for these sites.

### Backlight

Android's brightness setting can't go below 20 of 255 here, so the panel is never dark. The sunxi
display driver's `/sys/class/disp/disp/attr/lcdbl` (`root:root 0664`) can be written as root:

```sh
adb shell su 0 sh -c "'echo 0 > /sys/class/disp/disp/attr/lcdbl'"     # backlight off
adb shell su 0 sh -c "'echo 255 > /sys/class/disp/disp/attr/lcdbl'"   # back on
```

`0` turns the backlight fully off while the touch screen keeps working, so a tap can turn it back
on. The owner's local kiosk build uses this for a night mode (not part of this repo). Guess, not
verified: Android doesn't read `lcdbl` back, so the next brightness change from Android overwrites it.

### Changes made (approved, all in `/data`)

| Change | Undo |
| --- | --- |
| `su 0 setprop persist.adb.tcp.port 5555` | `su 0 setprop persist.adb.tcp.port ""`, then reboot |
| `su 0 pm disable com.adups.fota` | `su 0 pm enable com.adups.fota` |
| Kiosk installed, set as Home (chooser, **Always**) | `adb uninstall com.wesbos.homehq` |
| `pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS` | `pm revoke` the same |
| `settings put system screen_brightness 255` (was 15) | Set it back in Settings |
| ISRG Root X1 in `/data/misc/user/0/cacerts-added/6187b673.0` | `su 1000 rm` it, force-stop the kiosk |
| `su 0 pm disable net.frameo.frame` | `su 0 pm enable net.frameo.frame` (Frameo's sleep schedule and brightness come back) |

`adb tcpip 5555` only lasts until the next reboot.

### Not tested (101K)

- Whether `su 0` here lacks `CAP_SYS_ADMIN`/`CAP_SYS_TIME` as on the 102K and 114K.
- Whether another computer can connect over the network without the prompt.
- Whether a powered hub fixes the USB restarts (none was available).
