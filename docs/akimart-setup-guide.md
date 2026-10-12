# Akimart ZN-DP1002 frame: browser setup guide

Turns an Akimart 10.1-inch digital picture frame into a touchscreen browser device. It adds Firefox,
a normal launcher, WebView 106, a larger swap, and a navigation bar, and it switches off the vendor apps.

This frame is functionally identical to the RK3126 BIUFRAME. The major difference is that its partition 
table does not map to `/dev/block/by-name/`, requiring dynamic sysfs lookups for backup capabilities.

Automation: [`scripts/akimart-setup.sh`](../scripts/akimart-setup.sh).

## Read this first

This frame cannot be made secure. Know these limits before you use it:

- **Pre-Rooted:** The firmware ships with an exposed `su` binary. Any app can get root without a prompt.
- **The last security patch is from 2016** (Android 6.0.1, SELinux permissive).
- **The vendor apps contact external servers** (OTA, Cloud services). This guide disables them.
- **Do not sign into a primary Google, Apple, or bank account on it.** Use a separate account or an unauthenticated dashboard.
- Keep the frame on a guest or IoT Wi-Fi network.

## What you need

- A Mac or Linux machine with `adb`, `curl`, `openssl`, `unzip`, and about 3 GB free.
- A USB-C **data** cable plugged **directly** into the computer.
- You must find the exact package name of the Akimart photo frame application before running the apply script.

## Step 1: Find your specific Vendor Bloatware

We need to add the primary Akimart photo app to the disable script. Connect your frame to your PC and run:
```sh
adb shell pm list packages -s | grep -E "akimart|photo|frame|muxintu"
```
Look for the app that runs the photo frame UI (e.g., `com.muxintu.photoframe` or similar).

Once found, open `scripts/akimart-setup.sh` in a text editor and add the package name to the `VENDOR_DISABLE` array near line 25:
```bash
VENDOR_DISABLE=(com.muxintu.app.mxota com.your.app.name.here)
```

## Step 2: Confirm Hardware

```sh
scripts/akimart-setup.sh check
```

This changes nothing. Every line must be `ok`:

| Check | Expected |
| --- | --- |
| Build fingerprint | `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.cdm.20240816.163346:user/release-keys` |
| Model | `ZN-DP1002` |
| CPU | `Rockchip RK3126` |
| Root | `su gives root` |

## Step 3: Back up the firmware

```sh
scripts/akimart-setup.sh backup
```

- Reads everything on the eMMC prior to the `userdata` partition over ADB with root. It will dynamically calculate the sector count.
- Compares the readback to ensure validity.

## Step 4: Apply the setup

```sh
scripts/akimart-setup.sh apply
```

Each step checks its own result. At the end the frame reboots once and the script verifies the result.

| Step | What changes |
| --- | --- |
| Vendor apps off | `pm disable` / `pm hide` for the OTA updater and frame app. |
| Swap 128 → 512 MB | Adds `/system/su.d/50zram` and `/system/bin/install-recovery.sh` hook. |
| Apps | Installs Firefox 143.0.4 (armeabi-v7a) and Rootless Pixel Launcher 3.9.1. |
| WebView 44 → 106 | Replaces `/system/app/webview/webview.apk`, extracts native libraries correctly. |
| Let's Encrypt roots | Adds ISRG Root X1 & X2 to `/system/etc/security/cacerts/`. |
| Navigation bar | Appends `qemu.hw.mainkeys=0` to `/system/build.prop`. |

## Step 5: Finish on the frame

1. Press **Home** (or run `adb shell input keyevent KEYCODE_HOME`), pick **Rootless Pixel Launcher**, tap **Always**.
2. Open Firefox from the dock. (Settings → Customize → Theme → **Dark** makes the new navigation bar visible).

## Undo

If you wish to revert changes, you can execute the corresponding commands manually via `adb shell su -c '...'`:
- **Apps:** `pm unhide com.muxintu.app.mxota`, `pm enable com.muxintu.app.mxota`
- **WebView:** `mount -o remount,rw /system; cp /system/app/webview/webview.apk.bak /system/app/webview/webview.apk; rm -rf /system/app/webview/lib /system/app/webview/oat`, reboot.
- **Nav Bar:** `mount -o remount,rw /system; cp /system/build.prop.bak /system/build.prop`, reboot.