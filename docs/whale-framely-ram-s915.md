# Whale Framely 15.6" frame (`RAM_S915`, Rockchip RK3326-S)

One owner's unit, tested 2026-10-15 from an Apple silicon Mac running macOS. This is a record of one
unit, not a flashing guide. Observations are kept separate from guesses. Serials, MAC addresses,
the Terminal ID, network addresses and the contents of the device credential files are left out on
purpose.

## Identity

| Field | Observed value |
| --- | --- |
| Brand / platform | Whale Framely. Zeasn (now Whale TV) software, the same vendor platform as the Uhale frames |
| About screen "Model" | `RAM` |
| About screen "Build Number" | `RAM_S915_15.6_20260623` |
| About screen "System Version" | `8.10.0`. The Android version is not confirmed; this is probably the vendor app version |
| Panel | 15.6 inch |
| Mainboard silkscreen | `BND-S915-C A1.0` |
| Production label | `S915CABS-15.6`, flash 32G, DDR 1G |
| SoC | Rockchip RK3326-S (printed on the chip) |
| PMIC | RK817-6 |
| Memory | 1 GB DDR, Samsung eMMC (markings only partly legible) |
| Power | DC 12 V 2 A barrel supply. USB-C is data only: the frame does not start from USB power |
| Ports | USB-C, USB-A, 3.5 mm audio, SD card slot |
| Vendor kiosk app | `com.zeasn.frame` (full screen, no launcher exposed) |
| Vendor updater | `com.adups.fota` (Adups FOTA) |

The phone app for this product is `com.zeasn.android.photo.pro`.

## USB

- **Only one cable path enumerated.** Mac USB-C → USB-C-to-USB-A adapter → USB-A-to-USB-C data cable
  → frame USB-C. A direct USB-C-to-USB-C cable never enumerated, with or without the DC supply.
- With DC power, the frame presents **Rockchip VID `2207`, PID `0001`**, product string `RAM`,
  manufacturer `rockchip`. It has one vendor-specific interface (class `255/255/0`) whose string is
  `"MTP"`, and it answers as an MTP device.
- Manage photos → **PC transfer** switches the gadget to **PID `0002`**, a PTP interface
  (class `6/1/1`). Switching back returns to MTP.
- **No ADB interface in either mode.** `adb devices` stayed empty through three boot cycles with the
  cable attached.
- Tool note: the stock `rkdeveloptool` treats PID `0001` as MaskROM (`bcdDevice & 1 == 0`) and only
  accepts interface `255/6/5`. Here the device is running Android in MTP mode, not the boot ROM. Patching
  the tool to accept it got a response that was only the MTP stack, not RockUSB.

## ADB, network and browser routes

- Network ADB: `adb connect <ip>:5555` was refused. A TCP scan of ports 1–10000 on the frame's
  address found no open ports.
- WebADB (`app.webadb.com`, Chrome): the device did not appear in the USB chooser.
- Boot-from-USB debug trigger (documented for Uhale frames): not available. The frame needs its 12 V
  supply and does not run from 5 V USB power.

## What was tried on the frame

- Settings → About: tapping **System Version** 20 and 30 times, tapping **Build Number**, and
  tapping **Model** did not open native Android Settings.
- Long-presses on the home screen clock: nothing.
- Settings menu: My frame, Manage photos, Manage accounts, Display settings, Photo settings,
  Notifications, Backup and restore, Wi-Fi, Help, About. None offers a USB mode choice except the
  Manage photos submenu.
- Backup and restore: says "no photos found" and works only for photos.
- Manage photos submenu (Gallery, Import photos, Export photos, PC transfer, Play from external storage):
  the pickers are media-only with no folder navigation or "show all files".
- Factory reset from the vendor menu: the USB identity did not change, and a backup prompt appeared on
  the next boot. Files written to internal storage before the reset survived it.
- The one physical button on the board turns the display on and off. It is not a recovery key.

## MTP access

- Reads work across internal storage and the SD card. The SD card is listed as a removable storage
  object.
- Writes to internal storage worked once at the start of the session. After that, every write failed,
  including after `mtp-reset`. Folder creation also worked once.
- Writes to `Android/data/com.adups.fota/files/fota` and `.../adupsfota` failed.
- Writes to the SD card failed.
- The vendor app's data folders (`Android/data/com.zeasn.frame/`) are visible. The `files` folder was
  empty and `cache` held two empty subfolders.
- The `zeasn/` folder holds two device credential files. They are not recorded here.

## Hardware, case open

- Mainboard labelled `BND-S915-C A1.0`. Connectors seen: `MIC`, `eDP` (panel FPC), touch, `BAT+`,
  `SPKR`, `SPKL`, `PIR` (motion sensor), `KEY`.
- The `KEY` header is the button harness. The only button on the board toggles the display.
- A header labelled `SDA SCL INT RST 3.0V GND` is an I2C device header, probably the touch controller.
  It is not a serial console.
- Unlabelled round pad clusters are on the top edge, the right edge by the USB-A port, the right edge
  by the SD slot, and a 2×2 group near the middle. The owner reports TX and RX marks by the SD slot.
  These have not been confirmed with a meter or an adapter.
- The heat spreader is clipped on. The owner removed it without damage.

## Not yet tried

- UART at 115200 baud through the SD-slot TX/RX pads, with a 3.3 V USB-TTL adapter. No adapter was
  available when this was written. A TX pad should show activity on AC volts while the frame runs.
- Any boot image or loader write. Nothing was flashed or written to the eMMC.

## Guesses

- The RK3326 boot ROM may be reachable through a pad or key combination. This is untested.
- The Frameo "ADB Access" toggle used on other RK3326 frames does not apply: this unit does not run
  the Frameo app.
- Comparing with the Pastigio 15.6" FRAME156 page, the lack of a Frameo beta menu is the most likely
  reason no ADB appeared.
