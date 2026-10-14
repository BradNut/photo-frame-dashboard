#!/usr/bin/env bash
# Change the URL the Home HQ kiosk shows (dashboard/kiosk). The URL is saved on the frame and
# used at every launch, including after a reboot.
#
# Usage: scripts/set-kiosk-url.sh <url>     save <url> and open it
#        scripts/set-kiosk-url.sh           print the saved URL
#
# Over Wi-Fi instead of USB: ADB_SERIAL=<frame-ip>:5555 scripts/set-kiosk-url.sh <url>

set -euo pipefail

PKG=com.wesbos.homehq
adb_() { adb ${ADB_SERIAL:+-s "$ADB_SERIAL"} "$@"; }

if [ $# -eq 0 ]; then
  # Root reads the app's private prefs; prints nothing if no URL was ever saved (kiosk default).
  adb_ shell "su -c 'cat /data/data/$PKG/shared_prefs/*.xml'" | tr -d '\r' | sed -n 's:.*<string name="url">\(.*\)</string>.*:\1:p'
  exit 0
fi

url=$1
case "$url" in
  http://*|https://*) ;;
  *) echo "URL must start with http:// or https://" >&2; exit 1 ;;
esac

adb_ shell am start -n "$PKG/.MainActivity" --es url "'$url'" >/dev/null
echo "Saved and opened: $url"
