# SOMY ZC002 (Frameo, Allwinner A33, Android 6.0.1): userdata-key root

Record of one unit, started 2026-10-12. Observations are kept separate from guesses. No
serials, MACs, IPs, Wi-Fi details, Peer ID, private keys, or whole-disk hashes are included;
they live in the ignored `backups/`/`diagnostics/` folders. Host: macOS on Apple silicon.

The About screen shows **hardware brand and model number `DPF ZC002`**; `ro.product.brand` is
`SOMY`. This is the same Allwinner A33 family as the [PF1007L](pf1007l-start-here.md) and the
[Joyhong JT101F-I02](joyhong-jt101f-i02.md), under yet another vendor build (Frameo, not AiMOR,
not Joyhong's). See [#38](https://github.com/wesbos/photo-frame-dashboard/issues/38) for the
full investigation thread, including a dead end (no network ADB, Frameo's own
Settings → About → Beta Program → ADB Access toggle does nothing useful here) before the route
below. [#39](https://github.com/wesbos/photo-frame-dashboard/issues/39) and
[#64](https://github.com/wesbos/photo-frame-dashboard/pull/64) cover a similarly-named but
hardware-different Pastigio ZC002/Rockchip unit and another Allwinner ZC002 unit rooted with a
boot-image/`adbd`-binary patch; this report is a different unit, rooted a different way.

**Short version:** stock ADB is present over USB (`1f3a:1001`, not the `1f3a:1000`/`1002` seen
on the PF1007L) but stays `unauthorized` forever: this build has no SystemUI, so the
authorization popup has nowhere to render, and Frameo's own ADB toggle doesn't change that.
The fix used here does **not** touch the boot image, patch any binary, or weaken SELinux: it
adds the host's own ADB **public** key straight into `/data/misc/adb/adb_keys`, written through
a guarded, byte-range-verified patch to the live `/data` partition, using a writable variant of
this repo's existing read-only PF1007L U-Boot.

## Observations (read-only unless noted)

### Identity

| | |
| --- | --- |
| About screen | Hardware brand and model number `DPF ZC002` |
| Frameo version | v1.29.14 (60300) |
| Fingerprint | `Allwinner/astar_xr819/astar-xr819:6.0.1/MOB30R/20260313:eng/test-keys` |
| Build display ID | `ZC002_20260313`, built 2026-03-13 |
| `ro.product.model` / `device` / `brand` | `ZC002` / `ZC002` / `SOMY` |
| SoC | Allwinner A33 (confirmed by FEL: `soc=00001667(A33)`), 32-bit ARMv7 |
| Android | 6.0.1, SDK 23 |
| Wi-Fi module | XRadio XR819 (inferred from the `astar_xr819` platform name, same naming scheme as the PF1007L's `astar_m86_8723cs` and the Joyhong's `astar_ococci`) |
| eMMC | 31,268,536,320 bytes total addressable (differs from the PF1007L's 30,535,680/30,777,344-sector units) |

### USB

- USB-C to USB-C direct into a Mac: **no power, no data at all** (screen off). Same CC
  pull-down resistor issue as the PF1007L. A USB-A to USB-C cable through a USB-A hub/dock
  works.
- Stock boot: `1f3a:1001`, product string "Android". `adb devices` shows `unauthorized`, with
  **no on-screen authorization prompt ever**, confirmed by no status bar/notification shade
  reachable (no SystemUI). Network ADB (port 5555) is closed.
- Frameo's own **Settings → About → Enable Beta Program → ADB Access** toggle (the
  [documented route](https://support.frameo.com/hc/en-us/articles/6126183308434--How-to-Enable-ADB-on-Your-Frame),
  confirmed working on the Rockchip units in #21/#35) does not help here: toggling it on/off,
  unplugging/replugging and rebooting never produces a prompt, because there is no SystemUI to
  show one.
- FEL mode: `1f3a:efe8`, `sunxi-fel version` → `soc=00001667(A33)`.

### Partition table (from a full eMMC backup, MBR + one EBR chain)

| Partition | Start sector | Size (sectors) | Notes |
| --- | --- | --- | --- |
| bootloader | 73728 | 65536 | same start as the PF1007L/Joyhong |
| env | 139264 | 32768 | same start as the PF1007L/Joyhong |
| **boot** | **172032** | 32768 | same start as the PF1007L/Joyhong; `ANDROID!` header |
| system | 204800 | 2097152 (1 GiB) | same start/size as the Joyhong |
| misc | 2301952 | 32768 | same start as the Joyhong |
| recovery | 2334720 | 65536 | same start as the Joyhong; also `ANDROID!` header |
| cache | 2400256 | 1572864 (805 MB) | **larger** than the Joyhong's 524288 (256 MB); every later logical partition's offset differs from the Joyhong/PF1007L from here on, consistent with the bigger eMMC |
| metadata/private/frp/empty/alog/media_data | 3973120 onward | various | not individually identified by name; alog and the UDISK partition confirmed ext4 by superblock magic |
| UDISK (`/data`) | 4268032 | 56901632 declared, **29,083,303,936 bytes actually addressable** | declared size runs past the end of the eMMC, same note as the PF1007L guide; ext4, confirmed `Last mounted on: /data` |

### Boot image

Standard legacy `ANDROID!` header, page size 2048, kernel 10,165,848 bytes, ramdisk 4,741,158
bytes, no second stage, cmdline `vmalloc=384M`. Computed length from the header: 29,124 sectors
(not the PF1007L template's 31,028 sectors — different kernel/ramdisk size). SHA-256 over that
computed length: `379da4ba0b8c5f0b73401ee526dd8d8184eb18a709222de90a555dbeabe8f0b1`.

### Why ADB stays unauthorized (from the ramdisk, read-only)

The ramdisk's `default.prop`: `ro.secure=1`, `ro.debuggable=0`, `persist.sys.usb.config=none`.
But `init.rc` starts `adbd` **unconditionally** (`service adbd /sbin/adbd
--root_seclabel=u:r:su:s0` ... `start adbd`), not gated behind `ro.debuggable=1` like stock
AOSP. Something at runtime (not identified further; plausibly Frameo itself, a
system-privileged app here as on the Joyhong/Pastigio units) sets `persist.sys.usb.config` away
from `none` to something that includes `adb` without `mass_storage`, matching the unique
`1f3a:1001` ID. With `ro.secure=1`, the RSA key-authorization dialog is still required, and
with no SystemUI there is nowhere for it to render — so it can never be accepted, by any route
(USB, network, or Frameo's own toggle).

`com.android.systemui` is present in `/system/priv-app/SystemUI/SystemUI.apk` (4,678,006
bytes) — it is not missing from the firmware. `/data/system/users/0/package-restrictions.xml`
shows `<pkg name="com.android.systemui" enabled="2" enabledCaller="shell:0" />`: deliberately
disabled by a `pm disable` call (`enabledCaller="shell:0"`), same vendor-lockdown pattern as
other A33/Frameo units in this repo. **Not tested**: whether re-enabling it (now easy, with
root) would also make the authorization popup start working on this build; on a different
ZC002 unit, SystemUI was present yet ADB still needed a boot-image patch (#38 issue thread), so
this is not assumed to be the sole cause.

## Backup

Full eMMC backup taken through this repo's existing read-only PF1007L U-Boot route
([allwinner-a33-mainline-uboot.md](allwinner-a33-mainline-uboot.md)) — no changes needed to that
route; it worked on this unit as published. `emmc-macos.py backup` passed: two independent
read passes matched, zero `0xCC` filler runs, gzip readback verified.

## The fix: a writable U-Boot + a guarded userdata patch

This does not touch the boot image, system image, or any binary, and does not change SELinux
policy. It adds one file.

### 1. A writable variant of the read-only U-Boot

[`pf1007l-uboot-write.patch`](../scripts/a33-uboot/pf1007l-uboot-write.patch) is the same board
config (DRAM 456 MHz/ZQ 15291, eMMC on MMC2 8-bit, USB OTG forced to peripheral) as
[`pf1007l-uboot.patch`](../scripts/a33-uboot/pf1007l-uboot.patch), with the two
write-blocking hunks (`cmd/usb_mass_storage.c`'s `ums_write_sector`, and
`f_mass_storage.c`'s `initially_ro`) removed, so `ums` exposes attached storage as normal,
writable USB disks.

```sh
scripts/a33-uboot/build-uboot-write.sh
```

Builds to the ignored `diagnostics/a33-uboot-write-out/`, same SPL safety check as the
read-only build (SPL code must end before `0x5e00`; here it ends at `0x456a`, identical to the
read-only build, since the only changes are in the mass-storage write path, not SPL).

### 2. Prepare the userdata edit, offline, against your own backup

On a **copy** of the `/data` partition extracted from the backup (never the backup itself):

```sh
# add the host's public ADB key, with the ownership/mode/context already used
# by this device's own files on a sibling file in the same directory:
debugfs -w -R "write host_adbkey.pub /misc/adb/adb_keys" data-partition-copy.img
debugfs -w -R "sif /misc/adb/adb_keys uid 1000"   data-partition-copy.img
debugfs -w -R "sif /misc/adb/adb_keys gid 2000"   data-partition-copy.img
debugfs -w -R "sif /misc/adb/adb_keys mode 0100640" data-partition-copy.img
debugfs -w -R "ea_set -f selinux_ctx.bin /misc/adb/adb_keys security.selinux" data-partition-copy.img
e2fsck -n -f data-partition-copy.img   # confirm the edited filesystem is still clean
```

`selinux_ctx.bin` holds the literal bytes `u:object_r:adb_keys_file:s0\0` (28 bytes,
null-terminated) — read directly off this device's own `/misc/adb` directory with `ea_list`
first, rather than assumed from AOSP convention.

Then diff the edited copy against the pristine extracted copy:

```sh
python3 -I scripts/a33-uboot/data-patch-prepare.py \
  data-partition-pristine.img data-partition-copy.img <data-partition-start-sector>
```

On this unit: **9 byte ranges, 7,680 bytes total** (the new inode, its data block, the parent
directory's new entry, and the affected bitmaps/free-counts — scattered across two block
groups, one near the start of `/data` and one near the end, consistent with the allocator
picking a mostly-empty high-numbered group for the new inode/block). Writes
`diagnostics/a33-data-patch/plan.json` plus the original and new bytes for each range.

[`data-patch-write-macos.py`](../scripts/a33-uboot/data-patch-write-macos.py) (`check` /
`write` / `restore`) was tested against a simulated disk image (a sparse file seeded with the
plan's recorded original bytes) before being run against the real device, to confirm the
check/write/verify/restore round trip behaves correctly in isolation.

### 3. Apply it

With the frame in FEL (same stub-SD-card method as the read-only route) and the owner
approving this write:

```sh
sunxi-fel -v -p uboot diagnostics/a33-uboot-write-out/u-boot-sunxi-with-spl.bin \
  write 0x43100000 diagnostics/a33-uboot-write-out/ums-write.scr
```

Identify the eMMC the same way as the read-only route (by size; `WritableMedia` should now
read `true`, not `false` — if it still reads `false`, the read-only build loaded instead, stop).

```sh
sudo python3 -I scripts/a33-uboot/data-patch-write-macos.py check  diskN <exact-bytes>
sudo python3 -I scripts/a33-uboot/data-patch-write-macos.py write  diskN <exact-bytes>
```

`check` reads every planned range and confirms the live disk still holds exactly the backed-up
original bytes; it refuses to let `write` proceed if anything has already changed. `write` then
writes each range and reads it back immediately to verify, one range at a time.

Power-cycle (remove the FEL card, disconnect/reconnect), let it boot normally:

```text
adb devices -l
<redacted serial>   device usb:... product:ZC002 model:ZC002 device:ZC002

adb shell id
uid=2000(shell) ...

adb shell su 0 id
uid=0(root) gid=0(root) ...
```

Normal Frameo boot, authorized ADB, shipped `/system/bin/su` gives full root with `su 0
<command>` (this `su` does not accept the usual `su -c "<command>"` form; use `su 0
<command>` or `su root <command>`).

**Undo:** `data-patch-write-macos.py restore` writes the original bytes back to each of the 9
ranges and verifies, using the same plan.

## Scope of this report

Covers boot access and ADB authorization only; dashboard/kiosk setup on this unit is outside
its scope so far. SystemUI stays disabled (this fix didn't need it); navigation will need the
usual `adb shell input keyevent KEYCODE_HOME` / HOME-intent approach used on other
no-SystemUI A33 units in this repo. The writable U-Boot and guarded writer were built and
tested for this one fix; they are not a general-purpose live-write tool and should not be
pointed at a different byte range without re-deriving and re-verifying a plan the same way.
