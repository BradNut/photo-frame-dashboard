# Veidoo Frame 10.1" (F10, RK3126, Android 6.0.1)

Record of one unit, started 2026-10-13, Windows host. Observations are kept separate from guesses. Unique identifiers (serial, MAC, IP) live in the ignored `backups/` and `diagnostics/` folders.

Same SoC and Android version as the [BIUFRAME](biuframe.md) and [Rollei Smart Frame 107](rollei-smartframe-107.md), but a different vendor board (`ChipTrip` / `WeiDu`, Wi-Fi chip `rk915`, eMMC storage).

---

## Observations (read-only unless noted)

### Identity

| Parameter | Value |
| --- | --- |
| Retail name | Veidoo Frame 10.1", IPS touchscreen, 16/32 GB eMMC |
| Brand / Model | `veidoo` / `Frame` (`ro.product.device=F10`, manufacturer `ChipTrip`) |
| Firmware ID | `F606C_WeiDu_Frameo-V1.0.1202603071359.release-keys`, built 2026-03-07 |
| Build Fingerprint | `rockchip/rk312x/rk312x:6.0.1/MXC89K/user.wanghy.20260307.135729:user/release-keys` |
| SoC / Platform | Rockchip RK3126 (`ro.board.platform=rk312x`, `ro.hardware=rk30board`), 32-bit (`armeabi-v7a`) |
| Kernel | Linux 3.10.0 #1 SMP PREEMPT Sat Mar 7 13:56:13 CST 2026 |
| Android | 6.0.1, API 23, security patch 2016-07-05, `user` build, `ro.debuggable=0`, `ro.secure=1` |
| SELinux | **Permissive** (`androidboot.selinux=permissive` on kernel command line) |
| Display | 1280x800, 160 dpi, landscape orientation |
| RAM / Storage | 1 GB RAM, 128 MB ZRAM swap, 30 GB eMMC (`mmcblk0`) |
| WebView | `com.google.android.webview` 107.0.5304.36 (Chrome 107), modern enough for the Vite dashboard |
| Wi-Fi | Onboard radio (`wlan0`), driver module `rk915` |
| SystemUI | `com.android.systemui` is disabled: no status bar or soft navigation keys |
| Shipped Home | `net.frameo.frame` v1.32.15, disabled during onboarding |

---

### USB, ADB, and Root Access

- **ADB Access:** Enabled via Frameo Settings -> About -> Beta Program -> ADB Access.
- **USB ADB:** Recognized as `2207:0006` (MTP/ADB).
- **Network ADB:** Active on port 5555 (`service.adb.tcp.port=5555`), accessible over Wi-Fi (`adb connect <ip>:5555`).
- **Root Shell:** Pre-installed `/system/xbin/su` (SuperSU 2.45, UID 0). `adb shell su -c id` returns `uid=0(root)` immediately without manager prompts.
- **Persistence Mechanism:** SuperSU's daemon (`daemonsu`) automatically executes executable scripts located in `/system/su.d/` on boot.

---

### Security & Privacy Audit Findings

A complete decompilation and binary audit of the stock firmware identified aggressive vendor updaters and telemetry:

1. **Adups FOTA Subsystem (`com.adups.fota` and `com.adups.fota.sysoper`):**
   - Contains hardcoded C2 endpoints (`fota5p.adups.com`, `fota5p.adups.cn`, `fruet.adups.com`).
   - Plaintext data exfiltration (IMEI, MAC, Android ID, Advertising ID, cellular carrier, build fingerprint).
   - Remote DES-encrypted push commands over FCM capable of silent firmware flashing and background code execution.
   - **Remediation:** Disable and hide both packages:
     ```sh
     adb shell su -c pm disable-user --user 0 com.adups.fota
     adb shell su -c pm hide com.adups.fota
     adb shell su -c pm disable-user --user 0 com.adups.fota.sysoper
     adb shell su -c pm hide com.adups.fota.sysoper
     ```
2. **Rockchip Vendor Updater & Test Suite:**
   - `android.rockchip.update.service` (OTA updater targeting `www.rockchip.com:2300`) and `com.DeviceTest` (factory hardware test utility) can be safely disabled:
     ```sh
     adb shell su -c pm disable-user --user 0 android.rockchip.update.service
     adb shell su -c pm disable-user --user 0 com.DeviceTest
     ```
3. **Frameo Application (`net.frameo.frame`):**
   - Cloud telemetry and slideshow service disabled; replaced by an alternative launcher (such as Rootless Pixel Launcher 3.9.1; see [android-launcher.md](android-launcher.md)):
     ```sh
     adb shell su -c pm disable-user --user 0 net.frameo.frame
     ```

---

### System TLS Certificate Store Modernization

The stock Android 6.0.1 certificate store (`/system/etc/security/cacerts`) contained 227 legacy certificates with 48 expired roots, causing HTTPS handshake failures to modern web endpoints (e.g. Let's Encrypt ISRG Root X1, Google Trust Services):

- **Backup:** Original store archived before modification.
- **Modernization:** Deployed 209 modern, deduplicated, unexpired CA certificates incorporating modern LineageOS/AOSP, Mozilla CA bundle, GTS Root R1-R4/E1-E4, and Let's Encrypt ISRG Root X1/X2.
- **Verification:** Clean TLS 1.2/1.3 handshakes verified in modern browsers with valid security locks.

---

### System, Kernel, and Performance Optimization Suite

To convert the device into a snappy, responsive 24/7 Home Assistant / Web Dashboard, the system settings, kernel parameters, I/O queues, and daemons were tuned:

#### 1. Storage Block Layer (`/sys/block/mmcblk0/queue`)
- **I/O Scheduler:** Switched from spinning-disk `[cfq]` to `deadline`. Eliminates rotational seek sorting on eMMC flash.
- **Readahead:** Reduced from `2048 KB` to `512 KB` to avoid thrashing page cache on 1 GB RAM.
- **Entropy Overhead:** Disabled `add_random` (`0`) to eliminate block-level hashing overhead.
- **Core Affinity:** Set `rq_affinity = 2` to complete I/O interrupts on the submitting CPU core.

#### 2. CPU Interactive Governor (`/sys/devices/system/cpu/cpufreq/interactive`)
- **Ramp Threshold:** Lowered `go_hispeed_load` from `99` to `80`. The quad-core Cortex-A7 now scales to 1.008 GHz smoothly during page rendering instead of stuttering at 816 MHz.
- **I/O Wait Boost:** Enabled `io_is_busy = 1` so disk reads are treated as busy time, preventing clock drops during asset loads.
- **Sample Time:** Set `min_sample_time = 30000` (30 ms) and `above_hispeed_delay = 20000` (20 ms).

#### 3. Virtual Memory & ZRAM (`sysctl`)
- **Swappiness:** Raised `vm.swappiness` from `60` to `80`. Activates the 128 MB ZRAM swap partition to compress dormant background pages, preserving vital file caches for the dashboard browser.
- **Min Free Headroom:** Increased `vm.min_free_kbytes` from `2797 KB` (2.8 MB) to `8192 KB` (8 MB) to prevent direct-reclaim frame drops.
- **VFS Cache:** Set `vm.vfs_cache_pressure = 70` to retain directory structure in memory.
- **Dirty Flushes:** Set `vm.dirty_ratio = 15` and `vm.dirty_background_ratio = 5` to smooth eMMC writes.

#### 4. Background Daemons & CPU Churn
- **Disabled `rild`:** Hardware lacks cellular modem (`ro.baseband=N/A`). Stopped `ril-daemon` to eliminate background polling of `/dev/ttyACM0`.
- **Throttled KSM:** Increased Kernel Samepage Merging (`ksmd`) scan interval from `500 ms` to `2000 ms` (`/sys/kernel/mm/ksm/sleep_millisecs`), cutting wakeup CPU churn by 75%.
- **Disabled GPS Polling:** Set `location_mode = 0` and cleared `location_providers_allowed` (`ro.factory.hasGPS=false`).

#### 5. 24/7 Display & Android Settings
- **Stay Awake:** Set `global stay_on_while_plugged_in = 3` (AC + USB) to keep the display on 24/7.
- **Animation Scales:** Configured `animator_duration_scale = 0.5` (was null/1.0), `window_animation_scale = 0.5`, `transition_animation_scale = 0.5`.
- **Forced 2D GPU Acceleration:** Enabled `persist.sys.ui.hw = 1` to route 2D view rendering through the Mali-400 GPU.
- **Wallpaper Surface:** Enabled `sys.wallpaper.rgb565 = 1` to save 50% wallpaper surface memory.
- **Disabled Screensaver:** Set `secure screensaver_enabled = 0` to prevent DeskClock daydream from interrupting the dashboard.
- **Wi-Fi Background Scans:** Disabled open Wi-Fi notification scans (`wifi_networks_available_notification_on = 0`) and Google captive portal checks (`captive_portal_detection_enabled = 0`).
- **TCP Optimizations:** Configured `net.ipv4.tcp_tw_reuse = 1`, `net.ipv4.tcp_slow_start_after_idle = 0`, and `net.ipv4.tcp_keepalive_time = 300`.

---

### Boot Persistence Script

All kernel parameters under `/sys/` and `/proc/sys/` are made persistent across reboots via `/system/su.d/01_optimizations.sh` (`chmod 0755 root:root`). SuperSU `daemonsu` executes scripts in `/system/su.d/` automatically during early boot:

```sh
#!/system/bin/sh
# /system/su.d/01_optimizations.sh
# Automatically executed on boot by daemonsu via /system/su.d/

# 1. Stop unnecessary background daemons
# Hardware lacks cellular modem (ro.baseband=N/A); stop polling /dev/ttyACM0
stop ril-daemon

# 2. Storage & Block I/O Optimization (eMMC flash memory)
if [ -e /sys/block/mmcblk0/queue/scheduler ]; then
    echo deadline > /sys/block/mmcblk0/queue/scheduler
fi
if [ -e /sys/block/mmcblk0/queue/read_ahead_kb ]; then
    echo 512 > /sys/block/mmcblk0/queue/read_ahead_kb
fi
if [ -e /sys/block/mmcblk0/queue/add_random ]; then
    echo 0 > /sys/block/mmcblk0/queue/add_random
fi
if [ -e /sys/block/mmcblk0/queue/rq_affinity ]; then
    echo 2 > /sys/block/mmcblk0/queue/rq_affinity
fi

# 3. CPU Interactive Governor Optimization
if [ -e /sys/devices/system/cpu/cpufreq/interactive/go_hispeed_load ]; then
    echo 80 > /sys/devices/system/cpu/cpufreq/interactive/go_hispeed_load
fi
if [ -e /sys/devices/system/cpu/cpufreq/interactive/io_is_busy ]; then
    echo 1 > /sys/devices/system/cpu/cpufreq/interactive/io_is_busy
fi
if [ -e /sys/devices/system/cpu/cpufreq/interactive/above_hispeed_delay ]; then
    echo 20000 > /sys/devices/system/cpu/cpufreq/interactive/above_hispeed_delay
fi
if [ -e /sys/devices/system/cpu/cpufreq/interactive/min_sample_time ]; then
    echo 30000 > /sys/devices/system/cpu/cpufreq/interactive/min_sample_time
fi

# 4. Kernel Samepage Merging (KSM) Rate Limiting
if [ -e /sys/kernel/mm/ksm/sleep_millisecs ]; then
    echo 2000 > /sys/kernel/mm/ksm/sleep_millisecs
fi

# 5. Virtual Memory & ZRAM (sysctl) Tunables
sysctl -w vm.swappiness=80
sysctl -w vm.min_free_kbytes=8192
sysctl -w vm.vfs_cache_pressure=70
sysctl -w vm.dirty_ratio=15
sysctl -w vm.dirty_background_ratio=5

# 6. TCP Network Stack Tunables
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_slow_start_after_idle=0
sysctl -w net.ipv4.tcp_keepalive_time=300
```
