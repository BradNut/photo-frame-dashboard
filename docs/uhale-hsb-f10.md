# Uhale HSB / F10: USB input before ADB

One Uhale frame tested on Arch Linux / Omarchy on 18 and 19 October 2026.
**An Android Open Accessory keyboard opened the browser while ADB was off.** A
downloaded terminal APK then exposed the shipped `su`, which enabled authenticated
root ADB. A locally modified Home HQ kiosk displays the owner's hosted dashboard
and starts after reboot without a USB data cable.

Android 6.0 and the existing WebView 107 remain installed. No firmware was flashed,
no certificate was installed, and no vendor package was persistently disabled.
This is a report of one unit, not a general HSB or F10 flashing guide.

## Match the unit first

| Field | Observed value |
| --- | --- |
| Android model | `HSB` |
| Device | `f10_v11_bl_f10_tbd_wifi_1280x800_37v_1v8` |
| Board / platform | `sp7731gea` / `sc8830`, Spreadtrum; exact chip variant not independently confirmed |
| Firmware | `F10_V1.01_20260826_195506` |
| Android / SDK / ABI | `6.0` / `23` / `armeabi-v7a` |
| Uhale | `FSTR - 5.1.5`, version code `5010508`, package `com.zeasn.frame` |
| Existing WebView | `107.0.5304.36` |
| Display | Physical mode `800×1280`; landscape screenshots `1280×800`, density `160` |
| RAM | Approximately 1 GiB |
| Initial USB | Spreadtrum `1782:4011`, PTP interface, no ADB interface |
| Working USB configuration | `mtp,adb`, `1782:4002` |

The [SI006 report](si006-uhale.md) is useful background, but its partition offsets,
system-key edits and WebView replacement are not this unit's procedure. Neither
the Allwinner FEL routes nor the Rockchip loaders apply to this Spreadtrum board.

## Before opening the frame's browser

Use a trusted, isolated setup network and keep the frame's separate power adapter
connected. The Android version and shipped root access are not a safe basis for
using sensitive accounts on an untrusted network. See [vendor updates](app-updates.md)
for the risks of connecting stock frame software to the internet.

The following routes were tried and did **not** expose Android Settings on this
firmware:

- Repeated taps on Uhale's System version or Build Number.
- Repeated taps on the exact "Powered by" text, rather than the blue logo.
- USB ADB before enabling it in Android; network ADB was not listening either.

The [Quokka Uhale assessment](https://go.quokka.io/hubfs/App-Intel/Technical_Uhale-Digital-Picture-Frame-Security-Assessment.pdf)
and an older vendor APK helped identify possible entry points, but their hidden
menu behavior did not match this installed Uhale version. The older APK was
inspected on the host, not installed on the frame.

## Working entry route without ADB

### 1. Open the browser through USB HID

Open Uhale's **PC transfer** page and confirm that the Linux host sees the PTP
device. ADB being absent does not rule out USB input.

The frame accepted the [Android Open Accessory HID protocol](https://source.android.com/docs/core/interaction/accessories/aoa2#hid-support).
The host used Python `ctypes` and `libusb` to register a keyboard through USB
control transfers. It did not switch the frame into accessory mode, flash a
payload, or require an app on the frame.

The successful standard-keyboard sequence was:

| AOA operation | Request | Payload or parameters |
| --- | --- | --- |
| Get protocol | `51`, device-to-host `0xc0` | Read the two-byte protocol response |
| Register HID | `54`, host-to-device `0x40` | `wValue` = chosen HID ID; `wIndex` = report descriptor length |
| Set report descriptor | `56`, host-to-device `0x40` | Same HID ID, descriptor offset zero, standard boot-keyboard descriptor |
| Send HID event | `57`, host-to-device `0x40` | Same HID ID; send the eight-byte keyboard report |

The descriptor used for the keyboard was:

```text
05010906a101050719e029e71500250175019508810295017508810195067508150025650507190029658100c0
```

After allowing Android to register the keyboard, sending `08 00 05 00 00 00 00 00`
followed by eight zero bytes pressed and released **Meta+B**, Android 6's browser
shortcut. The browser opened. Subsequent reports could select the address bar and
type a URL. Sending characters too quickly initially dropped the first letter;
pauses after registration and focus changes fixed that input problem.

These are recorded protocol details, not a bundled, general-purpose USB tool.
The unit-specific host helpers are not bundled with this report. Another implementation
must select the owner's intended USB device, handle reconnects, and release held
keys. HID registrations are lost on USB re-enumeration. AOA unregisters a HID with
request `55`; changing the registered input devices can also recreate Android
activities, so keep a physical way back to PC transfer available.

### 2. Download and open Terminal Emulator

The host served a small HTTP page and the verified Terminal Emulator APK over the
local setup network. Only the frame's address was allowed through the host firewall
to that temporary server. The frame's browser downloaded `androidterm.apk` into
its default Download directory. No credentials were sent through this HTTP page.

The APK downloaded successfully, but this browser had no usable Downloads menu.
The path that opened Android's installer was the **exact file URL**:

```text
file:///storage/emulated/0/Download/androidterm.apk
```

Check the actual downloaded filename if the browser renamed a duplicate download.
Approve installation on the frame, then select **Open**, not Done. Do not clear or
disable Uhale to reach the terminal. If this firmware asks for an unknown-sources
permission, treat that as a separate owner-approved change; do not assume every
HSB unit has the same installer policy.

These attempted alternatives did not work:

- Opening `file:///storage/emulated/0/Download/` as a directory produced a blank page.
- The browser's download-location picker selected folders, not APKs to open.
- A link using `intent:` to open Android Settings failed with `ERR_UNKNOWN_URL_SCHEME`.
- Android browser download/menu shortcuts did not expose a usable download list.

Gboard's comma-key settings menu provided another native settings screen, but it
was not needed for the successful exact-file installer route.

### 3. Test the shipped root shell and enable USB ADB

In Terminal Emulator, this read-only check returned `uid=0(root)`:

```sh
su -c id
```

After the owner approved enabling debugging, a root terminal ran:

```sh
su
settings put global adb_enabled 1
```

A genuine computer RSA authorization prompt appeared. Its fingerprint was matched
against the setup host's public ADB key before accepting it. USB ADB then connected,
and its shell also returned UID 0. `ro.adb.secure` reported `1`.

Selecting MTP with the following command produced `mtp,adb` and USB ID `1782:4002`
while debugging was enabled:

```sh
adb -d shell svc usb setFunction mtp
adb -d shell getprop sys.usb.config
adb -d shell getprop persist.sys.usb.config
adb -d shell id
```

Use `adb -s YOUR_SERIAL` instead of `-d` if multiple USB Android devices are attached.
The authorized host key was present in `/data/misc/adb/adb_keys`.
`/system/etc/security/adb_keys` did not exist on this unit; no key was written to
`/system`. A key-file snapshot taken after accepting the prompt is not a backup of
the factory-original trust file. Post-reboot USB reconnection was not tested in the
final cable-free boot test, so this report does not establish USB authorization
persistence across reboot.

To undo debugging, turn it off in Android's Developer options once the physical
Settings/launcher escape route works. This unit's starting persistent USB property
was `none`; do not copy another unit's USB properties blindly.

## Seeing and controlling the screen before ADB

The PTP connection also provided a way to inspect the screen without installing a
screen-sharing app:

1. Send the keyboard Print Screen usage `0x46`, then release it.
2. Enumerate screenshot objects through PTP and find the new filename.
3. Fetch the file with `GetPartialObject`, operation `0x101b`, in 4096-byte pieces.
4. Check the returned size and validate the PNG on the host before viewing it.

The host helpers used `GetObjectPropList`, operation `0x9805`, with filename
property `0xdc07` to find screenshot objects. Fresh captures worked while ADB was
still off. This is screenshot-file retrieval, not live screen mirroring.

AOA mouse reports also moved a pointer and performed clicks and long presses.
An experimental absolute-touch HID did not produce reliable clicks. Mouse input
was the working choice. Physical touch remained available to the owner.

## USB and backup caveats

Uhale's PC transfer page affected USB availability. Leaving that page or recreating
its activity could drop the connection; reconnecting could bring PC transfer back
to the foreground. Avoid repeatedly toggling input-device registration while
depending on that page for access.

After ADB was enabled, long reads still suffered from repeated `adbd` restarts.
Temporary RSA-authenticated Wi-Fi ADB was restricted to the setup host with an
IPv4 firewall rule, and incoming IPv6 connections to its port were blocked. It
became stable after unplugging **only the USB data cable**, with separate power
still connected. Software USB deauthorization and temporarily stopping the
restarting factory `daemonsu` service had not resolved the interruptions. This
observation does not establish a single cause of the vendor USB behavior.

Network ADB was not made persistent. Its port was unreachable after the final
reboot while the frame responded on Wi-Fi. If using network ADB for setup, retain
authentication, restrict both IP families before enabling it, and verify it is
closed afterwards. Do not expose a root debugging port to the internet.

The private firmware acquisition covered the GPT-derived region before userdata,
both eMMC boot areas and the secondary GPT. Its boundaries differ from the SI006.
Checks included byte counts, gzip readback, host SHA-256, device MD5, filler checks
and independent boot/recovery reads. The large userdata partition was excluded;
NV, persist and cache can still contain private data.

An independent system sample initially disagreed with its earlier acquisition.
Work stopped to investigate rather than accepting the mismatch. Two subsequent
16 MiB reads matched each other; 18 changed bytes were filesystem metadata,
including timestamp fields for the shipped `su` and `daemonsu`. A separate backup
revision preserved the original acquisition. Its reconstructed full system
partition matched two device-computed full-partition digests.

Limits of this backup:

- It is a live acquisition, not an atomic whole-device snapshot or a photos backup.
- Read-only host `e2fsck -fn` reported inode-bitmap padding not set. No repair was run.
- The secondary GPT header pointed its partition array at LBA 2. That layout was
  recorded, not corrected on the frame.
- No offline flash restoration has been tested. A verified read is not proof of
  recovery from a failed firmware flash.

## Kiosk, recovery and boot results

Rootless Launcher was installed as an additional escape route. The existing
[Home HQ navigation controls](../dashboard/kiosk/README.md#frames-without-home-or-back-buttons)
were enabled, including the documented `WRITE_SECURE_SETTINGS` grant so the kiosk
can restore its navigation service. The owner physically verified the two-finger
menu, Android Settings and the floating Dashboard return button before selecting
Home HQ as the default Home app.

Android 6's Home chooser was used: enable the kiosk's Home alias as described in
the [startup instructions](../dashboard/kiosk/README.md#start-at-boot), then choose
**Home HQ → Always**. The preference was checked in Android's saved package state.
The owner confirmed that a subsequent reboot opened the dashboard without taps
and without a USB data cable. To undo the Home selection, use **Android Settings →
Home** and choose Uhale or the fallback launcher.

The installed kiosk was a local modification with private HTTP authentication and
retry changes. It loaded an existing hosted dashboard, not this repository's
mock-data web app. Its saved authentication survived an app restart. Temporarily
blocking only its dashboard connection showed the offline screen; removing that
block restored the dashboard automatically. Those authentication/retry changes and
the private hosting gateway are not included here, and an unmodified upstream APK
was not separately tested on this unit.

The existing WebView 107 rendered that dashboard over HTTPS. No WebView swap, CA
installation, TLS bypass or JavaScript compatibility patch was necessary. This
does not establish compatibility with every website or certificate chain.

An Android UI-automation helper temporarily suppressed other accessibility
services, hiding the floating buttons during testing. Stopping the helper restored
them. The helper was removed after testing; a missing overlay during automated
inspection was not evidence that the physical navigation service was broken.

The temporary setup server and firewall exception were removed. Bluetooth was
restored to off, and an experimental second Gboard layout was removed. Uhale and
vendor updaters remain installed and enabled. They were not audited or secured by
this work, and Android 6 / WebView 107 are not current security-supported versions.
No verified newer Android image or firmware flashing procedure was established for
this exact board.

## Downloads used

These APKs came from F-Droid. Verify the hash before installation; no binaries are
included in this report.

| App | Source | SHA-256 |
| --- | --- | --- |
| Terminal Emulator 1.0.70-rebuild | [F-Droid archive, version 72](https://f-droid.org/archive/jackpal.androidterm_72.apk) | `95095176ca3fa421102352ecaea0fffb6d13527db023967a7cfa280f7bc05cb5` |
| Rootless Launcher | [F-Droid, version 30911](https://f-droid.org/repo/amirz.rootless.nexuslauncher_30911.apk) | `7fa44d560dc4577374d45176220de2c0b00a71e09d6d148cdea4e0a52d38404a` |

Screenshots, raw device state, credentials, public ADB keys, firmware dumps and
unit-specific hashes remain private. No personal dashboard URL is needed to
reproduce the device-access findings.
