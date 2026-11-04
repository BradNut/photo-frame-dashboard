#!/usr/bin/env python3
"""Run the kiosk's night schedule rules (src/.../NightSchedule.java): when the screen is off,
when the next screen-off and screen-on alarms go, and what the "night" pref and extra accept.

Requires Python 3 and a JDK on PATH. No Android device, SDK or third-party packages.
This checks the rules, not the alarms, device admin or the screen itself.
"""
from pathlib import Path
import subprocess
import tempfile


SRC = Path(__file__).resolve().parent / "src/com/wesbos/homehq"

HARNESS = r'''
package com.wesbos.homehq;

import java.util.Calendar;
import java.util.Locale;
import java.util.TimeZone;

public class NightScheduleHarness {
  static final TimeZone LA = TimeZone.getTimeZone("America/Los_Angeles");

  static void check(String name, boolean ok) {
    if (!ok) throw new AssertionError(name);
    System.out.println("PASS " + name);
  }

  static long at(int y, int mo, int d, int h, int mi) {
    Calendar c = Calendar.getInstance(LA, Locale.ROOT);
    c.clear();
    c.set(y, mo - 1, d, h, mi, 0);
    return c.getTimeInMillis();
  }

  static int m(int h, int mi) {
    return h * 60 + mi;
  }

  public static void main(String[] args) {
    NightSchedule n = NightSchedule.parse("21:00-07:00");
    check("parse: off and on times", n.enabled && n.offMinute == m(21, 0) && n.onMinute == m(7, 0));
    check("stored form round-trips", "21:00-07:00".equals(n.stored())
        && NightSchedule.parse(n.stored()).stored().equals(n.stored()));
    check("single-digit hours are fine", "07:05-06:30".equals(NightSchedule.parse("7:05-6:30").stored()));
    check("no pref: off", !NightSchedule.parse(null).enabled && NightSchedule.parse(null).stored() == null);
    check("\"off\": off", !NightSchedule.parse("off").enabled);
    check("garbage: off", !NightSchedule.parse("25:00-07:00").enabled && !NightSchedule.parse("21-7").enabled
        && !NightSchedule.parse("21:0-07:00").enabled && !NightSchedule.parse("a:bc-07:00").enabled);
    check("same off and on time: off", !NightSchedule.parse("07:00-07:00").enabled);

    check("across midnight: 20:59 is day", !n.isNight(m(20, 59)));
    check("across midnight: 21:00 is night", n.isNight(m(21, 0)));
    check("across midnight: 03:00 is night", n.isNight(m(3, 0)));
    check("across midnight: 06:59 is night", n.isNight(m(6, 59)));
    check("across midnight: 07:00 is day", !n.isNight(m(7, 0)));
    NightSchedule early = NightSchedule.parse("01:00-06:00");
    check("same day: 00:59 is day, 01:00 night, 06:00 day",
        !early.isNight(m(0, 59)) && early.isNight(m(1, 0)) && !early.isNight(m(6, 0)));
    check("off schedule: never night", !NightSchedule.OFF.isNight(m(3, 0)));

    long morning = at(2026, 11, 4, 9, 0);
    check("from 09:00: screen off tonight at 21:00", n.next(false, morning, LA) == at(2026, 11, 4, 21, 0));
    check("from 09:00: screen on tomorrow at 07:00", n.next(true, morning, LA) == at(2026, 11, 5, 7, 0));
    long nine = at(2026, 11, 4, 21, 0);
    check("exactly at 21:00: next screen-off is tomorrow", n.next(false, nine, LA) == at(2026, 11, 5, 21, 0));
    long late = at(2026, 11, 4, 23, 30);
    check("from 23:30: screen on at 07:00 next morning", n.next(true, late, LA) == at(2026, 11, 5, 7, 0));
    check("night by the clock: 23:30 PST", n.isNight(late, LA));

    // DST ends 2026-11-01 02:00 in Los Angeles: the day is 25 hours long.
    long beforeFallBack = at(2026, 10, 31, 22, 0);
    check("over the clock change: still 07:00 local", n.next(true, beforeFallBack, LA) == at(2026, 11, 1, 7, 0)
        && n.next(true, beforeFallBack, LA) - beforeFallBack == 10 * 3600 * 1000L);

    // A frame with no clock battery boots in 1969 and sets alarms then. Each alarm re-checks the
    // schedule: once network time arrives (09:00) the stale "screen off" alarm must not act.
    check("boot clock 1969-12-31 16:00 is day", !n.isNight(at(1969, 12, 31, 16, 0), LA));
    check("stale screen-off alarm at 09:00 is not night", !n.isNight(morning, LA));

    check("label on", "Screen off at night: 21:00 to 07:00".equals(n.label()));
    check("label off", "Screen off at night: off".equals(NightSchedule.OFF.label()));
    check("picking a time turns it on", NightSchedule.OFF.withOff(m(22, 30)).enabled
        && "22:30-07:00".equals(NightSchedule.OFF.withOff(m(22, 30)).stored()));
    check("turning it off keeps the times", n.withEnabled(false).offMinute == m(21, 0)
        && n.withEnabled(false).stored() == null);
  }
}
'''

with tempfile.TemporaryDirectory(prefix="homehq-night-schedule-") as directory:
    root = Path(directory)
    java = root / "NightScheduleHarness.java"
    java.write_text(HARNESS, encoding="utf-8")
    subprocess.run(["javac", "--release", "8", "-d", str(root), str(SRC / "NightSchedule.java"), str(java)],
                   check=True, timeout=30)
    subprocess.run(["java", "-cp", str(root), "com.wesbos.homehq.NightScheduleHarness"],
                   check=True, timeout=30)
