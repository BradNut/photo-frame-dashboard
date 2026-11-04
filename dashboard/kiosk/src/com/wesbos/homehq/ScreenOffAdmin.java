package com.wesbos.homehq;

import android.app.admin.DeviceAdminReceiver;

/**
 * Device admin with one policy, force-lock, so the night schedule can turn the screen off
 * (DevicePolicyManager.lockNow). Optional: without it the kiosk only blacks out the screen.
 *   adb shell dpm set-active-admin com.wesbos.homehq/.ScreenOffAdmin
 */
public class ScreenOffAdmin extends DeviceAdminReceiver {}
