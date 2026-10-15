# ARZOPA frame (RK3126, Android 6.0.1, firmware `dpf01m1a_user_JVSHI_202505261448`)

Record of one unit, tested from Windows 11 (WSL2 Ubuntu + usbipd-win for loader mode) on
2026-10-15. Observations are kept separate from guesses. Unique identifiers (serial, MAC) are
left out.

**Result:** ADB over USB through a code-protected toggle in the Arzopa app, and shipped SuperSU
root. A verified loader-mode backup of everything before `userdata` was taken first. No write
to flash was needed.

## How it relates to the known RK3126 frames

Same platform build as the [YIAISIGN 10X1](yiaisign-10x1.md) and the
[Uhale 102KZ](uhale-102kz.md), but a different partition layout, Wi-Fi chip and vendor app.

| | This frame | YIAISIGN 10X1 | Uhale 102KZ |
| --- | --- | --- | --- |
| Model / manufacturer | `ARZOPA frame` / `incar` | `10X1` / `incar` | `102KZ` / `incar` |
| Build fingerprint | `…/user.fyl.20170927.202757:userdebug/test-keys` | same | same |
| USB, Android running | `2207:0012` (MTP + ADB) | `2207:0011` | `2207:0006` |
| Home app | Arzopa, `com.arzopa.frame.server` (`/system/app/Jvshi`) | `com.shenju.biuframe` | `com.zeasn.frame` |
| ADB | On, but `unauthorized` until the app's ADB toggle is enabled with a code (below) | Prompt shown | Prompt hidden behind the kiosk |
| Wi-Fi | AICSemi AIC8800 (`aic8800_fdrv`) | Realtek SDIO | not recorded |
| Partition layout | userdata at loader `0x2C9000` (`radical_update` and `custom` partitions) | userdata at 2,846,720 | same as YIAISIGN |

## Identity

| | |
| --- | --- |
| About screen | Firmware `dpf01m1a_user_JVSHI_202505261448`, software version `4.3.6`, frame name `Arzopa<digits>` |
| `ro.product.model` / `brand` / `manufacturer` | `ARZOPA frame` / `rockchip` / `incar` |
| `ro.product.device` / `board` / `board.platform` | `rk312x` / `rk30sdk` / `rk312x` |
| Build fingerprint | `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.fyl.20170927.202757:userdebug/test-keys` |
| Android | 6.0.1 (SDK 23), security patch 2016-11-01, kernel 3.10.0, SELinux permissive |
| `ro.secure` / `ro.debuggable` / `ro.adb.secure` | `1` / `1` / `1` |
| `/proc/cpuinfo` | `Hardware : Rockchip RK3126` |
| RAM | 1 GB (`MemTotal: 1021148 kB`); `ro.config.low_ram` not set |
| Display | 1280 × 800, 160 dpi |
| WebView | `com.android.webview` 44.0.2403.119 |
| USB, Android running | `2207:0012`, manufacturer string `incar`, product string `ARZOPA frame`. Windows shows an MTP device ("camera") whose storage only exposes `Pictures` and `DCIM` |
| USB, loader mode | `2207:310d`; `rkdeveloptool ld` reports `Loader` |
| Chip query (`rci`) | `41 32 31 33 37 31 30 32 37 31 34 30 30 30 32 56`, the same as the BIUFRAME (RK312x) |
| eMMC (`rfi`) | 61,079,552 sectors of 512 bytes (about 29.8 GB), the same count as the YIAISIGN |
| Parameter block | `FIRMWARE_VER:6.0.0`, `MACHINE_MODEL:rk312x`, `MANUFACTURER:PHILCO` |
| `boot` partition (loader `0x14000`, `0x7000` sectors) | Starts with `ANDROID!`. SHA-256 of the whole 14,680,064-byte partition read: `790b30c320e084d9e1985360315710446dc887e48c3195812bc65f5a41132f2b` |
| Vendor software | `com.arzopa.frame.server` 4.3.6, `com.adups.fota` (Adups FOTA updater) |

## Getting ADB

1. Plugged into the PC, ADB was already on: Windows lists an "ADB Interface" and
   `adb devices` shows `unauthorized`. No "Allow USB debugging?" prompt appeared, and the Arzopa
   settings have no developer options.
2. In the Arzopa app, **Settings → About**, tap **Software version** five times. A toast counts
   down and an **ADB** row appears (`AboutFragment.setAdbStatus`).
3. Turn the ADB toggle on. It asks for a code. The code is a fixed string in the app,
   **`arzopazxcv`** (`AboutFragment.showFramePassDialog`); nothing on screen is a challenge. A
   correct code sets `Settings.Global.adb_enabled=1`.
4. `adb devices -l` then showed `device product:ARZOPA frame model:ARZOPA_frame device:rk312x`.
5. `adb shell su -c id` → `uid=0(root)`. SuperSU's `su` and `daemonsu` are in `/system/xbin`.
   **Any app can get root.**

The About screen also has a **Test mode** row (`ll_test_mode`). It does not affect ADB: it sets
`persist.sys.test.mode`, and with `1` the app talks to Arzopa's test server instead of
production (`Api.getTestMode`). Leave it off.

Finding the code took the vendor APK, which needed loader mode (below) because ADB was not
authorized yet. Owners of this firmware can skip straight to the code.

## Loader mode and backup

- Unplugged, holding the reset pinhole while plugging USB-C in landed in **stock recovery**
  (the same menu as the BIUFRAME's: "Any button cycles highlight. Long-press activates.").
  Loader mode showed up for about 4 seconds on the way.
- From recovery, **Reboot to bootloader** reliably gave loader mode (`2207:310d`), and it
  stayed there until `rkdeveloptool rd`.
- Windows host: usbipd-win with an AutoBind policy for `2207:310d`, attached to WSL2 Ubuntu.
  Ubuntu's `rkdeveloptool` package (1.32+pine64) takes the `rl` length in **bytes**, not sectors.
  `scripts/backup-flash.py` was run through a one-line wrapper that multiplies by 512.
- The first read in one session hung, after which even `rci` timed out; a power cycle and a fresh
  loader session fixed it. Later reads ran at about 20 MiB/s.
- Reads above 32 MiB returned real data, as on the BIUFRAME.
- Backup: loader LBA 0 to `0x2C9000` (everything before `userdata`), 1,495,269,376 bytes. Two
  independent passes had the same SHA-256, gzip readback passed and no `0xCC` runs were found.
  A separate read of `boot` matched the same slice of the backup.

## Partition layout

From the parameter block (`mtdparts=rk29xxnand:…`). Loader LBAs in 512-byte sectors.

| Partition | Start | Sectors |
| --- | --- | --- |
| uboot | `0x2000` | `0x2000` |
| misc | `0x4000` | `0x2000` |
| resource | `0x6000` | `0x8000` |
| kernel | `0xE000` | `0x6000` |
| boot | `0x14000` | `0x7000` |
| recovery | `0x1B000` | `0x10000` |
| backup | `0x2B000` | `0x20000` |
| cache | `0x4B000` | `0x40000` |
| metadata | `0x8B000` | `0x8000` |
| kpanic | `0x93000` | `0x2000` |
| system | `0x95000` | `0x200000` (ext4) |
| radical_update | `0x295000` | `0x20000` |
| custom | `0x2B5000` | `0x14000` (ext4, holds `License.txt`) |
| userdata | `0x2C9000` | rest |

## Hardware

| Part | Observed | Evidence |
| --- | --- | --- |
| SoC | Rockchip RK3126 | `/proc/cpuinfo`, chip query |
| Wi-Fi | AICSemi AIC8800 on SDIO (vendor `0xc8a1`) | `lsmod`: `aic8800_fdrv`, `aic8800_bsp`; `/sys/bus/sdio/devices` |

## Not done yet

- Phase 6 (launcher, browser, kiosk) and disabling `com.adups.fota` before the frame goes online.
  The [BIUFRAME setup guide](biuframe-setup-guide.md) applies to this platform, but
  `biuframe-setup.sh check` is expected to fail (different fingerprint and manufacturer), as on
  the YIAISIGN; run its steps one at a time.
- Whether the ADB setting survives a reboot.
