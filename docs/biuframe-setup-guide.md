# BIUFRAME 10.1" frame: browser setup guide

Turns a BIUFRAME 10.1-inch picture frame (or compatible variants like the Akimart ZN-DP1002) into a touchscreen browser device. It adds Firefox, a normal launcher, WebView 106, a larger swap, and a navigation bar, and it switches off vendor apps.

Tested on one BIUFRAME unit (2026-09-30) and one Akimart ZN-DP1002 unit (2026-10). The research log behind every step is [biuframe.md](biuframe.md).
Automation: [`scripts/biuframe-setup.sh`](../scripts/biuframe-setup.sh).

**Check the SoC, not just the brand.** Frames sold under the same brand or model name can ship with different hardware. This RK3126 guide and its `apply` script do **not** apply to:
- Allwinner A33 / AiMOR frames; use the [Allwinner PF1007L guide](allwinner-a33-pf1007l.md).
- RK3326 SSA frames (Android 8.1, NAND storage); see issue [#67](https://github.com/wesbos/photo-frame-dashboard/issues/67).

**For agents:** follow the steps in order. Stop at the first failed check and report it; do not
improvise around a mismatch. Every command runs from the repository root on a host machine with the frame connected over USB.

## Read this first

This frame cannot be made secure. Know these limits before you use it:

- **Any app can get root without a prompt.** The firmware ships SuperSU's `su` and a
  `daemonsu` service but no SuperSU manager app, so nothing asks for approval. Install nothing you
  do not trust.
- **The last security patch is from July 2016** (Linux 3.10, SELinux permissive).
- **The vendor apps contact external servers.** This guide disables them.
- **Do not sign into a primary Google, Apple, or bank account on it.** Use a separate
  account, a read-only calendar link (Google Calendar's "Secret address in iCal format"), or a
  dashboard you host yourself. Use Firefox rather than WebView-based apps for logins; its engine is newer.
- Keep the frame on a guest or IoT Wi-Fi network.

## What you need

- A Mac or Linux machine with `adb` (`brew install android-platform-tools` or distribution package), `curl`, `openssl`, `unzip`, and about 3 GB free.
- A **USB-A to USB-C data cable** plugged directly into the host machine. (On some units, the included cable is power-only, and USB-C to USB-C cables from modern host ports supply no power or data).
- The frame on Wi-Fi (Firefox and certificate downloads need internet on the host, not the frame).

## Step 1: Connect and authorize ADB

1. Power the frame and connect USB to the host computer.
2. Run `adb devices -l`.
   - `unauthorized`: tap **Allow** on the frame's "Allow USB debugging?" prompt, tick
     **Always allow**, and run it again.
   - Nothing listed: try another cable or port. Check `lsusb` or `system_profiler SPUSBHostDataType | grep -A3 0x2207`. VID `0x2207` is Rockchip.
3. Expected: an authorized device in `device` state.

ADB is enabled in stock firmware; no developer settings menu is needed.

## Step 2: Confirm hardware profile

```sh
scripts/biuframe-setup.sh check
```

This changes nothing. The script will identify your unit and test its pinned parameters:

| Check | BIUFRAME Profile | AKIMART Profile |
| --- | --- | --- |
| Fingerprint | `...MXC89K/user.thzy.20240919.143320...` | `...MXC89K/user.cdm.20240816.163346...` |
| Model | `10X1` | `ZN-DP1002` |
| Manufacturer | `Synergy` | `rockchip` |
| CPU | `Rockchip RK3126` | `Rockchip RK3126` |
| Wi-Fi driver | `ssv6x5x` loaded | `rk915` loaded |
| Root | `su gives root` | `su gives root` |
| Boot layout | eMMC sector 90112 | eMMC sector 90112 |

**Any mismatch: stop.** Do not continue if `check` reports an unrecognized fingerprint or partition mismatch.

## Step 3: Back up the firmware

```sh
scripts/biuframe-setup.sh backup
```

- Reads all eMMC sectors before `userdata` over ADB with root into `backups/<serial>/emmc-0-<sectors>.img.gz`.
- Verifies exact length, matches readback SHA-256 against stream hash, and re-reads `boot`, `recovery`, and 16 MiB of `system` data to compare with the backup file.
- The `system` verification check reads 16 MiB well past the partition start to skip dynamic ext4 superblock and journal areas that change while mounted.
- Does not include `userdata` (photos, Wi-Fi passwords). Keep the backup private.

## Step 4: Apply the setup

```sh
scripts/biuframe-setup.sh apply
```

Each step verifies its execution before proceeding. At the end, the frame reboots once and the script runs a final verification check (`verify`).

| # | Step | What changes | Check |
| --- | --- | --- | --- |
| 1 | Vendor apps off | `pm disable` & `pm hide` for vendor apps | Packages report `enabled=2`/`3` and `hidden=true` |
| 2 | Swap 128 → 512 MB | Adds `/system/su.d/50zram` & `/system/bin/install-recovery.sh` hook | `/proc/swaps` reports `524280` |
| 3 | Apps | Installs Firefox 143.0.4 and Rootless Pixel Launcher 3.9.1 | Both present in `pm list packages` |
| 4 | WebView 44 → 106 | Replaces `/system/app/webview/webview.apk`, deletes `oat/`, unpacks `lib/arm/*.so` | MD5s match; no `Failed to load library` errors |
| 5 | Let's Encrypt roots | Adds `6187b673.0` (X1) & `8794b4e3.0` (X2) to system CA store | Files present, mode 0644 |
| 6 | Navigation bar | Appends `qemu.hw.mainkeys=0` to `/system/build.prop` | NavigationBar window present |

Downloads are pinned and checked by SHA-256 before use.

## Step 5: Finish on the frame

1. Press **Home** (or run `adb shell input keyevent KEYCODE_HOME`), pick **Rootless Pixel Launcher**, and select **Always**.
2. Open Firefox from the dock. (Optional: Settings → Customize → Theme → **Dark** makes navigation bar icons easier to see against light content).

## Akimart ZN-DP1002 (RK3126) differences

Units matching the `AKIMART` profile share this same setup pipeline with these differences:
- **Build Fingerprint:** `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.cdm.20240816.163346:user/release-keys` (`ZN-DP1002`, manufacturer `rockchip`).
- **Vendor Apps:** Preloaded with Frameo (`net.frameo.frame`), Muxintu OTA (`com.muxintu.app.mxota`), Device Test (`com.szclink.app.cldevicetest`), and Rockchip update service (`android.rockchip.update.service`). All are disabled/hidden during debloat.
- **Wi-Fi Driver:** Uses the `rk915` kernel module instead of `ssv6x5x` (verified via `lsmod`).
- **Partition Bounds:** Userdata starts at sector 2,859,008 (backup covers 2,859,008 sectors / ~1.36 GiB). `system` is verified at sector 663,552 (skipping 16 MiB past partition start at 630,784).

## Known limits

- **No Home or Recents button:** This firmware's SystemUI hard-codes them invisible; the bar only displays volume and Back.
- **White navigation icons:** Transparent navigation bar styling in apps like Firefox makes white icons invisible against light page backgrounds. Use dark themes.
- **1 GB RAM:** Heavy modern sites are slow; 512 MB zRAM swap prevents freezing.
- Fixed software versions: Firefox 143 and Chromium WebView 106 are the final releases supporting Android 6.

## Undo

| Change | Undo (run with `adb shell su -c '...'`) |
| --- | --- |
| Vendor apps (BIUFRAME) | `pm unhide com.adups.fota; pm unhide com.cghs.stresstest`, then `pm enable <pkg>` |
| Vendor apps (AKIMART) | `pm unhide com.muxintu.app.mxota; pm unhide com.szclink.app.cldevicetest`, then `pm enable <pkg>` for them and `net.frameo.frame`, `android.rockchip.update.service` |
| WebView | `mount -o remount,rw /system; cp /system/app/webview/webview.apk.bak /system/app/webview/webview.apk; rm -rf /system/app/webview/lib /system/app/webview/oat; mount -o remount,ro /system`, reboot |
| Swap | `mount -o remount,rw /system; cp /system/bin/install-recovery.sh.bak /system/bin/install-recovery.sh; rm -f /system/su.d/50zram; mount -o remount,ro /system`, reboot |
| CA roots | `mount -o remount,rw /system; rm -f /system/etc/security/cacerts/6187b673.0 /system/etc/security/cacerts/8794b4e3.0; mount -o remount,ro /system` |
| Navigation bar | `mount -o remount,rw /system; cp /system/build.prop.bak /system/build.prop; mount -o remount,ro /system`, reboot |
| Apps | `adb uninstall org.mozilla.firefox`, `adb uninstall amirz.rootless.nexuslauncher` |