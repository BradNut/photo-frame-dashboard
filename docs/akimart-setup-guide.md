# Akimart ZN-DP1002 frame: browser setup guide

Turns an Akimart 10.1-inch digital picture frame into a touchscreen browser device. It adds Firefox,
a normal launcher, WebView 106, a larger swap, and a navigation bar, and it switches off the vendor apps.

> ⚠️ **IMPORTANT: Check your hardware first!** ⚠️
> There are multiple entirely different circuit boards sold under the "Akimart", "SSA", and "Frame" brand names. 
> This guide is strictly for the **Rockchip RK3126** / **Android 6.0.1** version (eMMC storage). 
> If `adb shell getprop ro.build.fingerprint` reveals `rk3326_go` / Android 8.1 / `rknand0`, **DO NOT USE THIS SCRIPT**.

This specific RK3126 frame is functionally identical to the BIUFRAME, so they share the exact same setup script. The major difference is that its partition table does not map to `/dev/block/by-name/`, requiring dynamic `sysfs` lookups for safe modification.

Automation: [`scripts/biuframe-setup.sh`](../scripts/biuframe-setup.sh).

## Read this first

This frame cannot be made secure. Know these limits before you use it:

- **Pre-Rooted:** The firmware ships with an exposed `su` binary. Any app can get root without a prompt.
- **The last security patch is from 2016** (Android 6.0.1, SELinux permissive).
- **The vendor apps contact external servers** (OTA, Cloud services). This guide disables them.
- **Do not sign into a primary Google, Apple, or bank account on it.** Use a separate account or an unauthenticated dashboard.
- Keep the frame on a guest or IoT Wi-Fi network.

## What you need

- A Mac or Linux machine with `adb`, `curl`, `openssl`, `unzip`, and about 3 GB free.
- A **USB-A to USB-C data cable**. (The cable that comes in the box is power-only. A USB-C to USB-C cable connected to a laptop's Type-C port may provide no power or data to the frame due to missing CC resistors on the frame's motherboard).

## Step 1: Confirm Hardware matches

Connect your frame to the PC and run:
```sh
scripts/biuframe-setup.sh check
```

This changes nothing. Every line must be `ok`:

| Check | Expected |
| --- | --- |
| Build fingerprint | `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.cdm.20240816.163346:user/release-keys` |
| Model | `ZN-DP1002` (AKIMART profile) |
| CPU | `Rockchip RK3126` |
| Root | `su gives root` |
| Partitions | Layout bounds securely readable dynamically via `sysfs` uevents |

*If this fails, STOP. Your frame is likely the RK3326 variant mentioned at the top of this guide.*

## Step 2: Back up the firmware

```sh
scripts/biuframe-setup.sh backup
```

- Reads everything on the eMMC prior to the `userdata` partition over ADB with root. It will dynamically calculate the sector boundary.
- Automatically verifies exact bytes and hashes against a second pass to ensure a flawless recovery image.

## Step 3: Apply the setup

```sh
scripts/biuframe-setup.sh apply
```

Each step verifies its own execution natively against the Android system before proceeding. At the end, the frame reboots once and the script runs a final verification check.

| Step | What changes |
| --- | --- |
| Vendor apps off | Safely disables/hides Frameo, MXOTA, and Factory Device Test apps. |
| Swap 128 → 512 MB | Adds `/system/su.d/50zram` and `/system/bin/install-recovery.sh` hook. |
| Apps | Installs Firefox 143.0.4 (armeabi-v7a) and Rootless Pixel Launcher 3.9.1. |
| WebView 44 → 106 | Replaces `/system/app/webview/webview.apk`, natively extracts required `.so` libraries. |
| Let's Encrypt roots | Adds ISRG Root X1 & X2 to `/system/etc/security/cacerts/`. |
| Navigation bar | Appends `qemu.hw.mainkeys=0` to `/system/build.prop`. |

## Step 4: Finish on the frame

1. Press **Home** (or run `adb shell input keyevent KEYCODE_HOME`), pick **Rootless Pixel Launcher**, tap **Always**.
2. Open Firefox from the dock. (Settings → Customize → Theme → **Dark** makes the new navigation bar visible against white websites).

## Undo

If you wish to revert changes, execute these commands via `adb shell su -c '...'`:

| Change | Command |
| --- | --- |
| **Vendor Apps** | `pm unhide com.muxintu.app.mxota; pm unhide com.szclink.app.cldevicetest`, then `pm enable <pkg>` for them and `net.frameo.frame`, `android.rockchip.update.service` |
| **WebView** | `mount -o remount,rw /system; cp /system/app/webview/webview.apk.bak /system/app/webview/webview.apk; rm -rf /system/app/webview/lib /system/app/webview/oat`, reboot |
| **Swap / ZRAM** | `mount -o remount,rw /system; cp /system/bin/install-recovery.sh.bak /system/bin/install-recovery.sh; rm -r /system/su.d`, reboot |
| **Certificates** | `mount -o remount,rw /system; rm /system/etc/security/cacerts/6187b673.0 /system/etc/security/cacerts/8794b4e3.0` |
| **Nav Bar** | `mount -o remount,rw /system; cp /system/build.prop.bak /system/build.prop`, reboot |
| **Apps** | `adb uninstall org.mozilla.firefox`, `adb uninstall amirz.rootless.nexuslauncher` |