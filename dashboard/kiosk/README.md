# Home HQ kiosk navigation

Hold two fingers still on the dashboard for 1.5 seconds to open the native controls:

- **Open launcher** opens another installed Home app, such as Rootless Launcher.
  If none is available, it opens Android Settings.
- **Android settings** opens the device's Settings app.
- **Reload dashboard** reloads the current URL.
- **Back to dashboard** dismisses the controls.

## Frames without Home or Back buttons

Some frame firmware omits Android's navigation bar. The two-finger gesture only
works inside Home HQ, so it cannot bring you back from another app's settings.

Enable **Home HQ navigation** in Android **Settings → Accessibility**. The
optional service adds floating **Back** and **Dashboard** buttons outside Home HQ:

- **Back** performs Android's normal Back action.
- **Dashboard** returns directly to Home HQ, keeping the current dashboard URL.
- Drag the dots to move the buttons. Their position is saved.

The buttons hide while Home HQ is active and return when you leave it. Android
keeps the service enabled across reboots. It requests no accessibility events or
screen-content access and does not require root. Disable **Home HQ navigation**
in Accessibility settings to remove the buttons.

Keep an ADB connection available while enabling the service on a frame with no
other way back. If needed, return to the kiosk with:

```sh
adb shell am start -n com.wesbos.homehq/.MainActivity
```

This service supplies navigation controls only. To start the dashboard at boot,
make Home HQ the default Home app (below).

## Start at boot as the Home app

Home HQ is registered as a Home app. Android 6 has no command to set the default
Home, so pick it on the frame once. Keep another launcher installed (for example
Rootless Launcher) so **Open launcher** has somewhere to go.

```sh
adb shell am start -a android.intent.action.MAIN -c android.intent.category.HOME
```

On the frame, tap **Home HQ**, then **Always**. Check that it was saved:

```sh
adb shell 'grep -A2 "<preferred-activities" /data/system/users/0/package-restrictions.xml'
```

The kiosk saves the last URL it was given and opens it at every boot:

```sh
adb shell 'am start -a android.intent.action.VIEW -d "http://192.168.1.20:8080/" -n com.wesbos.homehq/.MainActivity'
```

Any URL you open this way, including one used while testing, replaces the saved
URL. If the frame boots before Wi-Fi is up, the kiosk retries every 5 seconds
until the page loads.

## Build and install

Use JDK 17, Android build-tools 34.0.0, and platform 34. From `dashboard/`:

```sh
ANDROID_HOME=/path/to/android-sdk bash kiosk/build.sh
adb install -r kiosk/build/homehq.apk
```

The kiosk loads the existing hosted dashboard over the frame's Wi-Fi. A USB
connection is only needed for installation or diagnostics, not normal use.

To build your own dashboard for a PF1007L frame, see
[building-for-the-frame.md](../../docs/building-for-the-frame.md): what WebView 106 supports,
what to avoid, and how to test on the frame.
