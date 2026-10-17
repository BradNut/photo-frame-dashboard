# PF1508 / AiMOR 6.0.100 (Allwinner A333, Android 15)

One unit, an Anna Bella 15.6" frame from [Amazon US](https://www.amazon.com/dp/B0H4VVFPG6?tag=webo080-20),
tested 2026-10-17 from macOS (Apple silicon, `adb` 37.0.0). Observations are separate from
guesses, and guesses are marked.

This is a different platform from the other AiMOR frames in this repo: Android 15, 64-bit, on an
Allwinner A333. Persistent USB ADB took about five minutes, through the factory test app from
[#135](https://github.com/wesbos/photo-frame-dashboard/issues/135). No SD card, network,
flashing or root was needed. Don't run the A33 (PF1007L) or A133 (PF1506) routes on it.

## Identify it

AiMOR Settings → About showed:

- Firmware version `YHK.F-null-A333-1506-D2048-C2-V10-PF1508-OS.0.20260725`
- Model `PF1508`
- AiMOR version `6.0.100`

Over ADB:

| Property | Value |
| --- | --- |
| `ro.build.fingerprint` | `Allwinner/a537_pro_arm64/a537-pro:15/AP3A.241105.008/26072516:user/release-keys` |
| `ro.build.display.id` | `PF1508_20260725` |
| `ro.hardware` / `ro.board.platform` | `sun65iw1p1` / `earth`. The build's resource overlays are named `a333_q83_arm64` |
| Android | 15 (SDK 35), `user` build, `ro.debuggable=0`, `ro.adb.secure=1`, verified boot `green` |
| ABI / kernel | `arm64-v8a` only / Linux 6.6.102 |
| RAM / storage | 2 GB (`MemTotal` 1,842,284 kB) / 16 GB free on a new unit |
| Display | 1920×1080 at 160 dpi. The Amazon listing says 1280×800 |
| WebView | `com.android.webview` 124.0.6367.219, the only provider |
| Ports | DC barrel jack for power and one USB-C port. No SD slot |

Guess: the fingerprint's `a537_pro_arm64` is a reused product name; the firmware string and
overlays say A333.

## Get ADB

Before the unlock, USB with a USB-A-to-C data cable (through a hub) showed `1f3a:4ee1`, product
`PF1508`, with one interface, `MTP`. No ADB. On macOS, the Image Capture helper holds that
interface.

1. Open AiMOR Settings → About. Tap **Model** repeatedly (about 10 times) until the
   "Open test app" password box appears.
2. Enter `YHK88888888` (from #135).
3. The test app on this firmware is `com.yhk.devicenewtest`, a Chinese grid of green test
   tiles, not the "IS CLOSED" screen from #135. Tick the small **adb调试** ("adb debugging")
   checkbox at the top right, under the MAC address.
4. Android asks "Allow USB debugging?" with the computer's RSA key fingerprint. Check
   **Always allow from this computer**, then **Allow**.

Avoid the bottom buttons 恢复出厂 (factory reset) and 清除测试数据 (clear test data). 退出 is Exit.
AiMOR brings its own main screen back after about 2 minutes without a touch, even over the test
app, so don't pause.

Afterwards USB shows `1f3a:4ee7` (ADB only), `persist.sys.usb.config=adb` and
`adb_enabled=1`. ADB came back on its own, without a new prompt, after each of four reboots.

The shell is `uid=2000(shell)`, not root. No root route was tried. With a `user` build and
verified boot `green`, `/system` can't be changed, so none of the WebView swaps or boot patches in
this repo apply. None are needed: WebView 124 is new enough for the dashboard.

Not tried: the `license.properties` card route from #104. With no SD slot, it would need a USB
stick on an OTG adapter, and it's unknown whether the USB-C port does host mode.

## What the vendor left on it

- **A saved factory Wi-Fi network**, `A8-20` (WPA2/WPA3), before any Wi-Fi setup. The frame
  would join it whenever it's in range. Removed with `adb shell cmd wifi forget-network 0`; it
  stayed gone after reboots.
- **AiMOR** (`com.efercro.os.aimor`, in `/system/system_ext/priv-app/AUMIOS_MoShare`) runs as the
  `system` user and was the Home app (`cn.nineox.robot.aimor.activity.NavigationActivity`). Its
  `CommunicationService` was running. Guess: that's the same vendor command channel as on the
  other AiMOR frames ([aimor-remote-root-shell.md](aimor-remote-root-shell.md)).
- While AiMOR is Home, it **turns Wi-Fi on at every boot**. `dumpsys wifi` names it
  (`WifiEnabled ... packageName=com.efercro.os.aimor`) about 22 s after boot.
- AiMOR's startup screen ("Welcome, aimor / AiMOR loading complete") has a **Recovery Mode**
  button. It's part of AiMOR, not Android recovery. Guess, from strings in the APK: it opens
  AiMOR's restore-from-backup screen. Not pressed.
- Other vendor packages: `com.yhk.qeota` (OTA, runs as `system` at boot), `com.softwinner.update`,
  `com.softwinner.runin` (Allwinner's factory burn-in app, runs at boot), `com.yhk.devicenewtest`
  (the test app), `com.yhk.rabbit.yhkages`.
- No listening TCP ports, no device owner, no accounts.

## A Home app that isn't AiMOR

There is no Launcher3 on this firmware. The only Home handlers are AiMOR and Settings'
`FallbackHome`, so install a launcher before anything else. KISS 3.26.0 from F-Droid worked:

```sh
# https://f-droid.org/repo/fr.neamar.kiss_224.apk
# SHA-256 da6ab0b1219ad3b5ee573698523fb15d60a918083e0843f94a03c1b12e1098c9 (matches F-Droid's index-v2.json)
adb install fr.neamar.kiss_224.apk
adb shell cmd package set-home-activity fr.neamar.kiss/.MainActivity
# undo: adb shell cmd package set-home-activity com.efercro.os.aimor/cn.nineox.robot.aimor.activity.NavigationActivity
```

`set-home-activity` works on this build (the HOME role moved from AiMOR to KISS). After a reboot,
the boot animation ended normally and KISS came up. The stuck boot animation from #118 didn't
happen.

With another app as Home, **AiMOR doesn't start at all**: no process after boot, so no
`CommunicationService`, no 2-minute return to its screen, and Wi-Fi stayed off after
`cmd wifi set-wifi-enabled disabled` and a reboot. Nothing was disabled to get there.

## The kiosk app on Android 15

The kiosk from `dashboard/kiosk` (built unchanged, targetSdk 23) doesn't install:

```text
Failure [INSTALL_FAILED_DEPRECATED_SDK_VERSION: App package must target at least SDK version 24, but found 23]
```

`adb install --bypass-low-target-sdk-block` installs it. Each launch then shows Android's "This
app was built for an older version of Android" dialog. After **OK**, the kiosk runs full screen
and showed its "Connect to Wi-Fi?" screen (the frame was offline). The dashboard itself wasn't
loaded.

## Not tested

- The dashboard on the frame, and the kiosk as Home.
- By hand on the panel: KISS → Android Settings → Apps (README rule 9).
- Disabling AiMOR, `com.yhk.qeota` or `com.softwinner.update`. On the Joyhong C-2, disabling a
  vendor updater made every activity crash at boot, so do one package at a time with ADB
  connected.
- Network ADB, root, factory reset, OTA behavior, and whether the USB-C port does host mode.
- Exactly how many taps on **Model** open the password box.
