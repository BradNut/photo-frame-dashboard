#!/usr/bin/env bash
# Set up a BIUFRAME 10.1" frame (USB "Synergy 10X1", RK3126, Android 6.0.1) or an
# Akimart ZN-DP1002 frame (RK3126, Android 6.0.1) as a browser device.
# Guides: docs/biuframe-setup-guide.md and docs/akimart-setup-guide.md
#
# Usage: scripts/biuframe-setup.sh <command>
#   check     Confirm the frame matches the known unit. Changes nothing.
#   backup    Save the eMMC up to the start of userdata to backups/<serial>/ and verify it.
#   verify-backup <file>  Compare boot, recovery and part of system on the frame with a backup.
#   apply     Run every setup step (each checks and skips work already done), then reboot.
#   verify    Check the end state after apply.
#
# Every step stops the script on the first failed check.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="${BIUFRAME_CACHE:-$ROOT/diagnostics/biuframe-downloads}"
DEV_TMP=/data/local/tmp/biuframe

FIREFOX_URL="https://archive.mozilla.org/pub/fenix/releases/143.0.4/android/fenix-143.0.4-android-armeabi-v7a/fenix-143.0.4.multi.android-armeabi-v7a.apk"
FIREFOX_SHA256="af560738627d4efc9ace75e708fc48aad6a24c78ef43a89daca27e16ff3829f8"
LAUNCHER_URL="https://f-droid.org/repo/amirz.rootless.nexuslauncher_30911.apk"
LAUNCHER_SHA256="7fa44d560dc4577374d45176220de2c0b00a71e09d6d148cdea4e0a52d38404a"
LIGHTNING_URL="https://f-droid.org/repo/acr.browser.lightning_101.apk"
LIGHTNING_SHA256="820f4f9977a20b060b4091db2b35cff8cd360e060f94aa742255c845747a2d7f"
WEBVIEW_URL="https://raw.githubusercontent.com/LineageOS/android_external_chromium-webview_prebuilt_arm/4b0ae494a7dd/webview.apk"
WEBVIEW_SHA256="e2edc1f89ec1608b169da9e7ffc037190b70c7825f0be29694f4cae719980580"
WEBVIEW_VERSION="106.0.5249.126"
ISRG_X1_URL="https://letsencrypt.org/certs/isrgrootx1.pem"
ISRG_X1_FP="96:BC:EC:06:26:49:76:F3:74:60:77:9A:CF:28:C5:A7:CF:E8:A3:C0:AA:E1:1A:8F:FC:EE:05:C0:BD:DF:08:C6"
ISRG_X2_URL="https://letsencrypt.org/certs/isrg-root-x2.pem"
ISRG_X2_FP="69:72:9B:8E:15:A8:6E:FC:17:7A:57:AF:B7:17:1D:FC:64:AD:D2:8C:2F:CA:8C:F1:50:7E:34:45:3C:CB:14:70"

# --- DEVICE PROFILES ---
PROFILE=""

load_profile() {
  local fp
  fp="$(sh_dev getprop ro.build.fingerprint)"
  case "$fp" in
    "rockchip/rk312x/rk312x:6.0.1/MXC89K/user.thzy.20240919.143320:user/release-keys")
      PROFILE="BIUFRAME"
      EXPECT_MODEL="10X1"
      EXPECT_MANUFACTURER="Synergy"
      EXPECT_WIFI_DRIVER="^ssv6x5x"
      EXPECT_BOOT_SECTOR="90112"
      EXPECT_NO_PROCESSES="adups|stresstest|biuframe|rockchip.update|DeviceTest|com.android.rk"
      VENDOR_DISABLE=(com.shenju.biuframe com.adups.fota android.rockchip.update.service com.cghs.stresstest com.DeviceTest com.android.rk com.android.rk.mediafloat)
      VENDOR_HIDE=(com.adups.fota com.cghs.stresstest)
      ;;
      
    "rockchip/rk312x/rk312x:6.0.1/MXC89K/user.cdm.20240816.163346:user/release-keys")
      PROFILE="AKIMART"
      EXPECT_MODEL="ZN-DP1002"
      EXPECT_MANUFACTURER="rockchip"
      EXPECT_WIFI_DRIVER=""
      EXPECT_BOOT_SECTOR="" # Validated purely dynamically via sysfs
      EXPECT_NO_PROCESSES="frameo|mxota|cldevicetest|rockchip.update"
      VENDOR_DISABLE=(net.frameo.frame com.muxintu.app.mxota com.szclink.app.cldevicetest android.rockchip.update.service)
      VENDOR_HIDE=(com.muxintu.app.mxota com.szclink.app.cldevicetest)
      ;;
      
    *)
      die "Unknown or unsupported build fingerprint: $fp"
      ;;
  esac
}
# -----------------------

say() { printf '\n==> %s\n' "$*"; }
ok() { printf '    ok: %s\n' "$*"; }
die() { printf '    FAIL: %s\n' "$*" >&2; exit 1; }

sh_dev() { adb shell "$@" | tr -d '\r'; }

# dev_has <grep -E pattern> <command...>: capture output first so grep -q cannot break the pipe.
dev_has() { local pat=$1 out; shift; out="$(sh_dev "$@")"; grep -qE -- "$pat" <<<"$out"; }
has_pkg() { dev_has "^package:$1\$" pm list packages; }

# Run a script on the frame as root. The script is pushed as a file to avoid quoting problems.
root_script() {
  local file="$(mktemp)"
  cat > "$file"
  adb push "$file" "$DEV_TMP/step.sh" >/dev/null
  rm -f "$file"
  adb shell "su -c 'sh $DEV_TMP/step.sh'" | tr -d '\r'
}

fetch() {  # fetch <url> <sha256> <name>
  local url=$1 sha=$2 out="$CACHE/$3"
  mkdir -p "$CACHE"
  if [ ! -f "$out" ] || [ "$(shasum -a 256 "$out" | cut -d' ' -f1)" != "$sha" ]; then
    curl -sfL -o "$out.partial" "$url" || die "download failed: $url"
    mv "$out.partial" "$out"
  fi
  [ "$(shasum -a 256 "$out" | cut -d' ' -f1)" = "$sha" ] || die "SHA-256 mismatch for $3"
  echo "$out"
}

wait_boot() {
  adb wait-for-device
  for _ in $(seq 1 90); do
    [ "$(sh_dev getprop sys.boot_completed 2>/dev/null)" = 1 ] && { sleep 10; return; }
    sleep 2
  done
  die "frame did not finish booting"
}

# Dynamically lookup partition start/size from sysfs by its uevent PARTNAME
get_part_info() {
  local name=$1
  local pdirs="$(sh_dev "ls -d /sys/block/mmcblk0/mmcblk0p* 2>/dev/null")"
  for pdir in $pdirs; do
    if dev_has "PARTNAME=$name\$" cat "$pdir/uevent" 2>/dev/null; then
      local pstart="$(sh_dev "cat $pdir/start")"
      local psize="$(sh_dev "cat $pdir/size")"
      if [[ "$pstart" =~ ^[0-9]+$ ]] && [[ "$psize" =~ ^[0-9]+$ ]]; then
        echo "$pstart $psize"
        return 0
      fi
    fi
  done
  return 1
}

cmd_check() {
  say "Checking the frame matches a known unit"
  command -v adb >/dev/null || die "adb not found (brew install android-platform-tools)"
  local state="$(adb get-state 2>/dev/null || true)"
  [ "$state" = device ] || die "no authorized ADB device (state: ${state:-none}). Accept the prompt on the frame."
  
  load_profile
  ok "fingerprint matched ($PROFILE profile)"
  
  [ "$(sh_dev getprop ro.product.model)" = "$EXPECT_MODEL" ] || die "model is not $EXPECT_MODEL"
  [ "$(sh_dev getprop ro.product.manufacturer)" = "$EXPECT_MANUFACTURER" ] || die "manufacturer is not $EXPECT_MANUFACTURER"
  ok "model $EXPECT_MANUFACTURER $EXPECT_MODEL"
  
  dev_has 'Rockchip RK3126' cat /proc/cpuinfo || die "CPU is not Rockchip RK3126"
  ok "RK3126"
  
  if [ -n "$EXPECT_WIFI_DRIVER" ]; then
    dev_has "$EXPECT_WIFI_DRIVER" lsmod || die "Wi-Fi driver $EXPECT_WIFI_DRIVER not loaded"
    ok "Wi-Fi driver loaded"
  fi
  
  [ "$(sh_dev "su -c id" | cut -d' ' -f1)" = "uid=0(root)" ] || die "su did not give root"
  ok "su gives root"
  
  local b_info="$(get_part_info boot)" || die "boot partition not found in sysfs"
  if [ -n "$EXPECT_BOOT_SECTOR" ]; then
    [ "${b_info% *}" = "$EXPECT_BOOT_SECTOR" ] || die "boot partition is not at eMMC sector $EXPECT_BOOT_SECTOR"
  fi
  ok "partition layout securely readable via sysfs"
}

cmd_backup() {
  cmd_check
  
  local ud_info backup_sectors
  ud_info="$(get_part_info userdata)" || die "Could not find userdata partition in sysfs"
  backup_sectors="${ud_info% *}"
  [ "$backup_sectors" -gt 0 ] || die "Invalid userdata start sector"
  
  local serial="$(sh_dev getprop ro.serialno)"
  local dir="$ROOT/backups/$serial"
  local out="$dir/emmc-0-$backup_sectors.img.gz"
  
  mkdir -p "$dir"
  [ -e "$out" ] && die "$out already exists"
  say "Reading $backup_sectors sectors ($((backup_sectors / 2048)) MiB) over ADB"
  
  adb exec-out "su -c 'dd if=/dev/block/mmcblk0 bs=512 count=$backup_sectors 2>/dev/null'" \
    | tee >(shasum -a 256 | cut -d' ' -f1 > "$out.sha256.raw") | gzip -1 > "$out.partial"
  mv "$out.partial" "$out"
  
  local size="$(gunzip -c "$out" | wc -c | tr -d ' ')"
  [ "$size" = $((backup_sectors * 512)) ] || die "backup is $size bytes, expected $((backup_sectors * 512))"
  local raw="$(cat "$out.sha256.raw")"
  [ "$(gunzip -c "$out" | shasum -a 256 | cut -d' ' -f1)" = "$raw" ] || die "gzip readback does not match stream hash"
  
  ok "$size bytes, SHA-256 $raw"
  echo "$raw" > "$out.sha256"
  rm -f "$out.sha256.raw"
  
  cmd_verify_backup "$out"
  ok "backup saved to $out"
}

cmd_verify_backup() {
  [ -n "$PROFILE" ] || load_profile
  local out=${1:?usage: verify-backup <backup.img.gz>} name start count a b
  [ -f "$out" ] || die "$out not found"
  say "Re-reading boot, recovery and 16 MiB of system data to compare with $(basename "$out")"
  
  local b_info r_info s_info b_start b_size r_start r_size s_start
  b_info="$(get_part_info boot)" || die "boot partition not found"
  r_info="$(get_part_info recovery)" || die "recovery partition not found"
  s_info="$(get_part_info system)" || die "system partition not found"
  
  b_start="${b_info% *}"; b_size="${b_info#* }"
  r_start="${r_info% *}"; r_size="${r_info#* }"
  s_start="${s_info% *}"
  
  # system data; the start of system holds the ext4 superblock and journal, which
  # change while mounted (SuperSU remounts /system several times a minute).
  # Skip 180224 sectors (~90 MiB) to bypass dynamic areas securely across variants.
  local s_check_start=$((s_start + 180224))
  
  for region in "boot $b_start $b_size" "recovery $r_start $r_size" "system $s_check_start 32768"; do
    read -r name start count <<<"$region"
    a="$(adb exec-out "su -c 'dd if=/dev/block/mmcblk0 bs=512 skip=$start count=$count 2>/dev/null'" | shasum -a 256 | cut -d' ' -f1)"
    # dd stops reading early; ignore gunzip's broken pipe.
    b="$({ gunzip -c "$out" 2>/dev/null || true; } | dd bs=512 skip="$start" count="$count" 2>/dev/null | shasum -a 256 | cut -d' ' -f1)"
    [ "$a" = "$b" ] || die "$name differs between backup and re-read"
    ok "$name matches"
  done
}

step_debloat() {
  say "Disabling vendor apps"
  local p
  for p in "${VENDOR_DISABLE[@]}"; do
    sh_dev "su -c 'pm disable $p'" >/dev/null
  done
  for p in "${VENDOR_HIDE[@]}"; do
    sh_dev "su -c 'pm hide $p'" >/dev/null
  done
  for p in "${VENDOR_DISABLE[@]}"; do
    dev_has 'enabled=[23]' dumpsys package "$p" || die "$p is not disabled"
  done
  for p in "${VENDOR_HIDE[@]}"; do
    dev_has 'hidden=true' dumpsys package "$p" || die "$p is not hidden"
  done
  ok "${#VENDOR_DISABLE[@]} disabled, ${#VENDOR_HIDE[@]} hidden"
}

step_zram() {
  say "Swap: zram 128 MB -> 512 MB at every boot"
  adb push "$ROOT/scripts/biuframe-su.d-50zram" "$DEV_TMP/50zram" >/dev/null
  root_script <<EOF
set -e
mount -o remount,rw /system
mkdir -p /system/su.d
cp $DEV_TMP/50zram /system/su.d/50zram
[ -f /system/bin/install-recovery.sh.bak ] || cp /system/bin/install-recovery.sh /system/bin/install-recovery.sh.bak
grep -q 50zram /system/bin/install-recovery.sh || echo '[ -x /system/su.d/50zram ] && /system/su.d/50zram' >> /system/bin/install-recovery.sh
mount -o remount,rw /system
chmod 0700 /system/su.d /system/su.d/50zram
chown 0:0 /system/su.d /system/su.d/50zram
sync
mount -o remount,ro /system
/system/su.d/50zram
EOF
  dev_has 50zram "su -c 'tail -1 /system/bin/install-recovery.sh'" || die "boot hook missing"
  dev_has 524280 cat /proc/swaps || die "swap is not 512 MB"
  ok "swap 512 MB, boot hook in install-recovery.sh"
}

step_apps() {
  say "Installing Firefox 143.0.4 and Rootless Pixel Launcher 3.9.1"
  local ff la li
  ff="$(fetch "$FIREFOX_URL" "$FIREFOX_SHA256" firefox-143.0.4-armeabi-v7a.apk)"
  la="$(fetch "$LAUNCHER_URL" "$LAUNCHER_SHA256" rootless-pixel-launcher-3.9.1.apk)"
  has_pkg org.mozilla.firefox || adb install "$ff" >/dev/null
  has_pkg amirz.rootless.nexuslauncher || adb install "$la" >/dev/null
  if [ "${BIUFRAME_LIGHTNING:-0}" = 1 ]; then
    li="$(fetch "$LIGHTNING_URL" "$LIGHTNING_SHA256" lightning-5.1.0.apk)"
    has_pkg acr.browser.lightning || adb install "$li" >/dev/null
  fi
  has_pkg org.mozilla.firefox || die "Firefox not installed"
  has_pkg amirz.rootless.nexuslauncher || die "launcher not installed"
  ok "installed"
}

step_webview() {
  say "System WebView 44 -> $WEBVIEW_VERSION"
  local apk libs
  apk="$(fetch "$WEBVIEW_URL" "$WEBVIEW_SHA256" webview-$WEBVIEW_VERSION.apk)"
  libs="$CACHE/webview-libs"
  rm -rf "$libs"
  mkdir -p "$libs"
  unzip -q -j "$apk" 'lib/armeabi-v7a/*' -d "$libs"
  sh_dev "mkdir -p $DEV_TMP/wvlib"
  adb push "$apk" "$DEV_TMP/webview.apk" >/dev/null
  adb push "$libs"/. "$DEV_TMP/wvlib/" >/dev/null
  root_script <<EOF
set -e
W=/system/app/webview
mount -o remount,rw /system
[ -f \$W/webview.apk.bak ] || cp \$W/webview.apk \$W/webview.apk.bak
cp $DEV_TMP/webview.apk \$W/webview.apk
rm -rf \$W/oat
mkdir -p \$W/lib/arm
cp $DEV_TMP/wvlib/*.so \$W/lib/arm/
mount -o remount,rw /system
chmod 0644 \$W/webview.apk \$W/lib/arm/*.so
chmod 0755 \$W/lib \$W/lib/arm
chown -R 0:0 \$W/webview.apk \$W/lib
sync
mount -o remount,ro /system
EOF
  local want got f
  for f in "$apk" "$libs"/*.so; do
    want="$(md5 -q "$f")"
    case "$f" in
      *.apk) got="$(sh_dev "md5sum /system/app/webview/webview.apk" | cut -d' ' -f1)" ;;
      *) got="$(sh_dev "md5sum /system/app/webview/lib/arm/$(basename "$f")" | cut -d' ' -f1)" ;;
    esac
    [ "$want" = "$got" ] || die "$(basename "$f") on the frame does not match"
  done
  dev_has '^-rw-r--r--' "ls -l /system/app/webview/lib/arm/libwebviewchromium.so" || die "WebView library is not 0644"
  ok "APK and $(ls "$libs" | wc -l | tr -d ' ') native libraries in place (active after reboot)"
}

step_certs() {
  say "Adding Let's Encrypt roots (ISRG Root X1, X2) to the system CA store"
  local pem fp h tmp
  tmp="$(mktemp -d)"
  for pair in "$ISRG_X1_URL $ISRG_X1_FP" "$ISRG_X2_URL $ISRG_X2_FP"; do
    read -r url fp <<<"$pair"
    pem="$tmp/$(basename "$url")"
    curl -sfL -o "$pem" "$url" || die "download failed: $url"
    [ "$(openssl x509 -in "$pem" -noout -fingerprint -sha256 | cut -d= -f2)" = "$fp" ] || die "fingerprint mismatch for $url"
    h="$(openssl x509 -in "$pem" -noout -subject_hash_old)"
    { openssl x509 -in "$pem" -outform PEM; openssl x509 -in "$pem" -noout -text -fingerprint; } > "$tmp/$h.0"
    adb push "$tmp/$h.0" "$DEV_TMP/$h.0" >/dev/null
    root_script <<EOF
set -e
mount -o remount,rw /system
cp $DEV_TMP/$h.0 /system/etc/security/cacerts/$h.0
mount -o remount,rw /system
chmod 0644 /system/etc/security/cacerts/$h.0
chown 0:0 /system/etc/security/cacerts/$h.0
sync
mount -o remount,ro /system
EOF
    dev_has '^-rw-r--r--' "ls -l /system/etc/security/cacerts/$h.0" || die "$h.0 is not 0644"
    ok "$h.0 $(openssl x509 -in "$pem" -noout -subject | sed 's/.*CN *= *//')"
  done
  rm -rf "$tmp"
}

step_navbar() {
  say "Turning on the navigation bar (Back and volume only on this firmware)"
  root_script <<'EOF'
set -e
mount -o remount,rw /system
[ -f /system/build.prop.bak ] || cp /system/build.prop /system/build.prop.bak
grep -q '^qemu.hw.mainkeys=' /system/build.prop || echo 'qemu.hw.mainkeys=0' >> /system/build.prop
mount -o remount,rw /system
chmod 0644 /system/build.prop
sync
mount -o remount,ro /system
EOF
  dev_has '^qemu.hw.mainkeys=0$' cat /system/build.prop || die "build.prop not updated"
  ok "qemu.hw.mainkeys=0 (active after reboot)"
}

cmd_verify() {
  [ -n "$PROFILE" ] || load_profile
  say "Verifying end state"
  [ "$(sh_dev "dumpsys package com.android.webview" | grep -m1 versionName | sed 's/.*=//')" = "$WEBVIEW_VERSION" ] || die "WebView is not $WEBVIEW_VERSION"
  ok "WebView $WEBVIEW_VERSION"
  dev_has 'webviewchromiumloader: Failed to load library' logcat -d && die "WebView native library failed to load"
  ok "WebView native library loaded"
  dev_has 524280 cat /proc/swaps || die "swap is not 512 MB after boot"
  ok "swap 512 MB after boot"
  dev_has 'Window\{.* NavigationBar\}' dumpsys window windows || die "no navigation bar window"
  ok "navigation bar present"
  
  local running
  running="$(sh_dev ps | grep -E "$EXPECT_NO_PROCESSES" || true)"
  [ -z "$running" ] || die "vendor processes still running: $running"
  ok "no vendor processes"
  
  sh_dev "ls /system/etc/security/cacerts/6187b673.0 /system/etc/security/cacerts/8794b4e3.0" >/dev/null || die "Let's Encrypt roots missing"
  ok "Let's Encrypt roots present"
}

cmd_apply() {
  cmd_check
  sh_dev "mkdir -p $DEV_TMP"
  step_debloat
  step_zram
  step_apps
  step_webview
  step_certs
  step_navbar
  say "Rebooting"
  adb reboot
  sleep 15
  wait_boot
  cmd_verify
  sh_dev "rm -rf $DEV_TMP"
  say "Done. On the frame: press Home, pick Rootless Pixel Launcher, tap Always."
}

case "${1:-}" in
  check) cmd_check ;;
  backup) cmd_backup ;;
  verify-backup) cmd_verify_backup "${2:-}" ;;
  apply) cmd_apply ;;
  verify) cmd_verify ;;
  *) sed -n '6,12p' "$0"; exit 1 ;;
esac