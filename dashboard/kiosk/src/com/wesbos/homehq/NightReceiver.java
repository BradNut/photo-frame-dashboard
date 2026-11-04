package com.wesbos.homehq;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.admin.DevicePolicyManager;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.PowerManager;
import android.util.Log;
import java.util.TimeZone;

/**
 * Turns the screen off and on at the night schedule's times. Frames like the Pastigio FRAME156
 * have no working clock chip (/dev/rtc0 is missing), so their own "scheduled power on" never
 * fires; this keeps the frame running and only turns the screen off. AlarmManager alarms wake the
 * CPU while the screen is off because the frame is still running.
 *
 * Each alarm checks the schedule again before acting: at boot a frame without a clock battery
 * starts in 1969 and an alarm set then fires the moment network time arrives.
 */
public class NightReceiver extends BroadcastReceiver {
  static final String ACTION_SLEEP = "com.wesbos.homehq.NIGHT_SLEEP";
  static final String ACTION_WAKE = "com.wesbos.homehq.NIGHT_WAKE";
  static final String EXTRA_NIGHT_EVENT = "night_event"; // to MainActivity: "sleep" or "wake"
  static final long WAKE_HOLD_MS = 10000;

  @Override
  public void onReceive(Context context, Intent intent) {
    String action = intent.getAction();
    NightSchedule night = schedule(context);
    boolean isNight = night.isNight(System.currentTimeMillis(), TimeZone.getDefault());
    if (ACTION_SLEEP.equals(action) && isNight) {
      Log.i(MainActivity.TAG, "Night: screen off");
      if (!lockScreen(context)) open(context, "sleep"); // no device admin: the kiosk goes black
    } else if (ACTION_WAKE.equals(action) && !isNight) {
      Log.i(MainActivity.TAG, "Morning: screen on");
      PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
      @SuppressWarnings("deprecation")
      PowerManager.WakeLock wake = pm.newWakeLock(PowerManager.FULL_WAKE_LOCK
          | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE, "homehq:morning");
      wake.acquire(WAKE_HOLD_MS); // the kiosk's keep-screen-on flag takes over once it's in front
      open(context, "wake");
    } else {
      Log.i(MainActivity.TAG, "Night alarm " + action + " no longer due (clock or schedule changed)");
    }
    arm(context);
  }

  static NightSchedule schedule(Context context) {
    return NightSchedule.parse(context.getSharedPreferences(MainActivity.PREFS, Context.MODE_PRIVATE)
        .getString(MainActivity.PREF_NIGHT, null));
  }

  /** Sets (or, with the schedule off, cancels) the next screen-off and screen-on alarms. */
  static void arm(Context context) {
    AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
    PendingIntent sleep = pending(context, ACTION_SLEEP);
    PendingIntent wake = pending(context, ACTION_WAKE);
    am.cancel(sleep);
    am.cancel(wake);
    NightSchedule night = schedule(context);
    if (!night.enabled) return;
    long now = System.currentTimeMillis();
    TimeZone tz = TimeZone.getDefault();
    am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, night.next(false, now, tz), sleep);
    am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, night.next(true, now, tz), wake);
  }

  private static PendingIntent pending(Context context, String action) {
    Intent i = new Intent(action).setClass(context, NightReceiver.class);
    return PendingIntent.getBroadcast(context, 0, i,
        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
  }

  static ComponentName admin(Context context) {
    return new ComponentName(context, ScreenOffAdmin.class);
  }

  static boolean canLock(Context context) {
    DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
    return dpm != null && dpm.isAdminActive(admin(context));
  }

  /** Turns the screen off for real; false without device admin. */
  static boolean lockScreen(Context context) {
    if (!canLock(context)) return false;
    DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
    try {
      dpm.lockNow();
      return true;
    } catch (SecurityException e) {
      Log.w(MainActivity.TAG, "Could not turn the screen off", e);
      return false;
    }
  }

  private static void open(Context context, String event) {
    context.startActivity(new Intent(context, MainActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        .putExtra(EXTRA_NIGHT_EVENT, event));
  }
}
