#!/usr/bin/env python3
"""Check the Home HQ kiosk's dashboard list on a connected, rooted frame (dashboard/kiosk).

Sends the "url" extra the way scripts/set-kiosk-url.sh does and reads the kiosk's prefs with root:
  - the URL saved before multiple dashboards becomes the only dashboard,
  - a new URL is added and becomes current, and sending it again doesn't add it twice,
  - set-kiosk-url.sh still prints the current URL.
The kiosk's prefs are backed up first and put back afterwards, so the frame ends as it started.
Doesn't check the two-finger dialogs; try those by hand.

Usage: scripts/test-kiosk-dashboards-on-device.py   (ADB_SERIAL=<serial> to pick a device)
"""
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

PKG = "com.wesbos.homehq"
PREFS = f"/data/data/{PKG}/shared_prefs/kiosk.xml"
BACKUP = "/data/local/tmp/homehq-kiosk-prefs.xml"
NEW = "https://example.com/"
SET_URL = Path(__file__).resolve().parent / "set-kiosk-url.sh"


def adb(*args, check=True):
    serial = ["-s", os.environ["ADB_SERIAL"]] if os.environ.get("ADB_SERIAL") else []
    return subprocess.run(["adb", *serial, *args], check=check, capture_output=True, text=True,
                          timeout=60).stdout.replace("\r", "")


def su(command, check=True):
    return adb("shell", f"su -c '{command}'", check=check)


def prefs():
    """(saved url or None, [dashboard urls]) from the kiosk's prefs file."""
    text = su(f"cat {PREFS}", check=False)
    if "<map" not in text:
        return None, []
    values = {s.get("name"): s.text or "" for s in ET.fromstring(text).iter("string")}
    lines = values["dashboards"].split("\n") if "dashboards" in values else []
    return values.get("url"), [line.split("\t", 1)[1] for line in lines if "\t" in line]


def send(url):
    adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity", "--es", "url", f"'{url}'")
    time.sleep(2)  # SharedPreferences.apply() writes the file shortly after


def check(name, ok):
    if not ok:
        raise AssertionError(name)
    print("PASS " + name)


had_prefs = "<map" in su(f"cat {PREFS}", check=False)
if had_prefs:
    su(f"cp -p {PREFS} {BACKUP}")
try:
    saved, listed = prefs()
    if saved and not listed:
        send(saved)
        check("update: the saved URL is the only dashboard", prefs() == (saved, [saved]))
    else:
        print("SKIP update check: the kiosk already has a dashboard list or no saved URL")
    before = prefs()[1]

    send(NEW)
    check("new URL: added last and current", prefs() == (NEW, before + [NEW] if NEW not in before else before))
    send(NEW)
    check("same URL again: not added twice", prefs()[1].count(NEW) == 1)

    printed = subprocess.run([str(SET_URL)], check=True, capture_output=True, text=True,
                             env=dict(os.environ, PATH=os.environ["PATH"]), timeout=60).stdout.strip()
    check("set-kiosk-url.sh prints the current URL", printed == NEW)
finally:
    # Stop the kiosk first, or it writes its prefs back over the restored file.
    adb("shell", "am", "force-stop", PKG)
    if had_prefs:
        owner = su(f"stat -c %u:%g /data/data/{PKG}").strip()
        su(f"cp {BACKUP} {PREFS} && chown {owner} {PREFS} && chmod 660 {PREFS} && rm {BACKUP}")
    else:
        su(f"rm -f {PREFS}")
    adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
    print("Restored the kiosk's prefs and restarted it")
