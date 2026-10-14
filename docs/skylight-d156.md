# Skylight Calendar, firmware D156 (userdebug build)

One unit, tested 2026-10-13 from a Linux host. Observations are separate from guesses, and guesses
are marked. This firmware is **not** the same as the 150-CAL unit in
[next-session.md](next-session.md): that one was a locked `user` build that needed a patched boot
image. This one has USB ADB and root out of the box.

## Identify it

Settings → About in the Skylight app showed:

- Software Version `26.28.0 (26020)`
- Firmware Version `D156.V0.10`

Over ADB:

| Property | Value |
| --- | --- |
| `ro.build.fingerprint` | `rockchip/D156/D156:12/AndroidS/D156.V0.10:userdebug/release-keys` |
| `ro.board.platform` / `ro.hardware` | `rk356x` / `rk30board` (Rockchip RK356x, arm64) |
| Android | 12 (SDK 32), `ro.build.type=userdebug`, `ro.debuggable=1`, SELinux permissive |
| Boot | `ro.boot.flash.locked=0`, verified boot state `orange` |
| Display | 1920×1080, 240 dpi (CSS viewport 1280×720) |
| WebView | `com.android.webview` 95.0.4638.74 |
| Vendor packages | `com.skylight` (the app), `skylight.watchdog` (installs app updates), `skylight.keyboard` (default IME) |
| Sensors | Light sensor |

Guess: "D156" suggests a 15.6" panel. The case and model label were not checked.

## ADB and root

- **USB ADB was already on.** The port is micro-USB. The first cable tried was power-only, and
  `adb devices` stayed empty until a data cable was used. No authorization prompt appeared.
- **Network ADB (5555) was off** (connection refused).
- **Root:** `/system/xbin/su` is AOSP's userdebug `su`. The syntax is `adb shell su 0 id`.
  `su -c id` fails with `invalid uid/gid '-c'`. AOSP `su` only works for the shell and root uids,
  so an app on the frame can't use it.
- The hidden 5-tap manufacturer menu from [app-analysis.md](app-analysis.md) was not needed or
  tried. The app version here is 26.28.0, much newer than the 9.29.3 that was analyzed.

## Back up first

With root, every partition except userdata was streamed to the host and checked against the
device's own hash. Size each partition first with `blockdev --getsize64`:

```sh
S=<adb-serial>
for p in security uboot trust misc dtbo vbmeta boot recovery backup cache metadata baseparameter super; do
  adb -s $S exec-out "su 0 cat /dev/block/by-name/$p" | tee >(sha256sum > $p.sha) | gzip -1 > $p.img.gz
  adb -s $S shell "su 0 sha256sum /dev/block/by-name/$p"; cat $p.sha   # the two must match
done
```

On this unit, `super` is 2.4 GB (0.9 GB gzipped) and userdata is 4 GB. Keep the images private
(see the README's privacy section).

## Make it a kiosk

1. **Add Wi-Fi through Android Settings first.** Skylight's onboarding saves the Wi-Fi network
   as owned by `com.skylight`. On Android 12, disabling that app deletes its networks
   (`WifiConfigManager: Remove all networks for app … com.skylight`), and the frame drops off
   Wi-Fi. Add the network in Android Settings before step 4, or be ready to re-enter it on the
   frame.
2. Install your kiosk APK (for example [`dashboard/kiosk`](../dashboard/kiosk)) with `adb install`.
3. Make it the home app and turn on the navigation service:
   ```sh
   adb -s $S shell cmd package set-home-activity com.wesbos.homehq/.MainActivity
   adb -s $S shell settings put secure enabled_accessibility_services com.wesbos.homehq/com.wesbos.homehq.NavigationService
   adb -s $S shell settings put secure accessibility_enabled 1
   ```
4. Stop the vendor app and its updater. This is reversible with `pm enable`:
   ```sh
   adb -s $S shell pm disable-user --user 0 skylight.watchdog
   adb -s $S shell pm disable-user --user 0 com.skylight
   ```
   Leave `skylight.keyboard` enabled. It is the default input method.
5. **Time zone.** The system zone was GMT; the Skylight app handled time itself. Set it as root
   (as shell this fails with a SecurityException):
   ```sh
   adb -s $S shell su 0 cmd time_zone_detector suggest_manual_time_zone --zone_id America/Los_Angeles
   ```

A web dashboard at 1920×1080 rendered correctly in WebView 95.

## Not tried yet

- **A root boot hook.** `/vendor/etc/init/vendor_flash_recovery.rc` defines
  `service vendor_flash_recovery /vendor/bin/install-recovery.sh` (class main, oneshot, runs as
  root), and that file does not exist. With the bootloader unlocked and SELinux permissive,
  `adb root`, `adb disable-verity`, a reboot and `adb remount` should allow adding one. Untested.
  It changes `/vendor` and needs a reboot.

## Undo

`pm enable com.skylight`, `pm enable skylight.watchdog`, uninstall the kiosk, and pick Skylight
as the home app. Skylight then needs activation again. Nothing was flashed on this unit.
