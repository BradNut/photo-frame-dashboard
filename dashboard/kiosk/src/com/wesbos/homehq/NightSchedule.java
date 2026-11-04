package com.wesbos.homehq;

import java.util.Calendar;
import java.util.Locale;
import java.util.TimeZone;

/**
 * When the screen is off at night. Stored as "HH:MM-HH:MM" (off time, then on time) in the
 * "night" pref; anything else means the screen stays on. Plain Java (no Android classes) so
 * test-night-schedule.py can run it on a computer.
 */
final class NightSchedule {
  static final int DEFAULT_OFF = 21 * 60;
  static final int DEFAULT_ON = 7 * 60;

  final int offMinute; // minutes after midnight
  final int onMinute;
  final boolean enabled;

  NightSchedule(int offMinute, int onMinute, boolean enabled) {
    this.offMinute = offMinute;
    this.onMinute = onMinute;
    // Equal times would mean off and on at the same moment.
    this.enabled = enabled && offMinute != onMinute;
  }

  static final NightSchedule OFF = new NightSchedule(DEFAULT_OFF, DEFAULT_ON, false);

  /** "21:00-07:00" turns it on; null, "off" or anything unreadable is off. */
  static NightSchedule parse(String s) {
    if (s == null) return OFF;
    String[] parts = s.trim().split("-");
    if (parts.length != 2) return OFF;
    int off = minuteOf(parts[0]);
    int on = minuteOf(parts[1]);
    if (off < 0 || on < 0) return OFF;
    return new NightSchedule(off, on, true);
  }

  /** "7:05" or "07:05" as minutes after midnight, or -1. */
  static int minuteOf(String hhmm) {
    String[] p = hhmm.trim().split(":");
    if (p.length != 2) return -1;
    try {
      int h = Integer.parseInt(p[0]);
      int m = Integer.parseInt(p[1]);
      if (h < 0 || h > 23 || m < 0 || m > 59 || p[1].length() != 2) return -1;
      return h * 60 + m;
    } catch (NumberFormatException e) {
      return -1;
    }
  }

  static String clock(int minute) {
    return String.format(Locale.ROOT, "%02d:%02d", minute / 60, minute % 60);
  }

  /** The value to keep in the "night" pref, or null to remove it. */
  String stored() {
    return enabled ? clock(offMinute) + "-" + clock(onMinute) : null;
  }

  NightSchedule withOff(int minute) {
    return new NightSchedule(minute, onMinute, true);
  }

  NightSchedule withOn(int minute) {
    return new NightSchedule(offMinute, minute, true);
  }

  NightSchedule withEnabled(boolean on) {
    return new NightSchedule(offMinute, onMinute, on);
  }

  /** Whether the screen should be off at this minute after midnight. */
  boolean isNight(int minute) {
    if (!enabled) return false;
    if (offMinute < onMinute) return minute >= offMinute && minute < onMinute; // e.g. 01:00-06:00
    return minute >= offMinute || minute < onMinute; // across midnight, e.g. 21:00-07:00
  }

  boolean isNight(long nowMs, TimeZone tz) {
    Calendar c = Calendar.getInstance(tz, Locale.ROOT);
    c.setTimeInMillis(nowMs);
    return isNight(c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE));
  }

  /** The next time the screen turns off (wantOn false) or on (wantOn true), after nowMs. */
  long next(boolean wantOn, long nowMs, TimeZone tz) {
    int minute = wantOn ? onMinute : offMinute;
    Calendar c = Calendar.getInstance(tz, Locale.ROOT);
    c.setTimeInMillis(nowMs);
    c.set(Calendar.HOUR_OF_DAY, minute / 60);
    c.set(Calendar.MINUTE, minute % 60);
    c.set(Calendar.SECOND, 0);
    c.set(Calendar.MILLISECOND, 0);
    if (c.getTimeInMillis() <= nowMs) c.add(Calendar.DAY_OF_MONTH, 1); // keeps wall time across DST
    return c.getTimeInMillis();
  }

  /** The controls row. */
  String label() {
    return enabled ? "Screen off at night: " + clock(offMinute) + " to " + clock(onMinute)
        : "Screen off at night: off";
  }
}
