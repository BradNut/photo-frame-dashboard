# Device index

Every frame documented in this repo. Each row is a record of the units its owners tested.
Frames sold under the same name can have different boards, so match the About screen, not the
brand. Missing yours? See the README's
[contributing section](../README.md#check-for-updates-and-send-back-what-you-find).

| Device | SoC, Android | ADB out of the box | Root | Start with |
| --- | --- | --- | --- | --- |
| Skylight Calendar 15" (150-CAL) | Rockchip RK3566, Android 12 | No. Hidden 5-tap manufacturer menu | Boot ramdisk `/force_debuggable`, then `adb root` | [next-session.md](next-session.md) |
| BIUFRAME 10.1" (Synergy 10X1), the frame in the video | Rockchip RK3126, Android 6.0.1 | Yes, USB, accept the prompt | Shipped SuperSU `su` | [biuframe-setup-guide.md](biuframe-setup-guide.md) |
| PF1007L / AiMOR (sold as BIUFRAME and others) | Allwinner A33, Android 6.0.1 | Varies by firmware | Boot patch, or root ADB once `adbd` runs | [pf1007l-start-here.md](pf1007l-start-here.md) |
| Joyhong JT101F-I02 (Frameo) | Allwinner A33, Android 6.0.1 | **Yes, root over Wi-Fi, no key check** | Root ADB | [joyhong-jt101f-i02.md](joyhong-jt101f-i02.md) |
| Dragon Touch Modern10 Charm (VPhoto) | Allwinner A33 (inferred; same `astar_ococci` platform as the Joyhong), Android 6.0.1 | Yes, root over Wi-Fi | Root ADB | [dragontouch-modern10-charm.md](dragontouch-modern10-charm.md) |
| Pastigio FRAME156 15.6" (Frameo) | Rockchip RK3326, Android 8.1 | Frameo Settings → Beta → ADB Access | Shipped `su` | [pastigio-frame156.md](pastigio-frame156.md) |
| VESWWE DP100 10.1" (Frameo) | Rockchip RK3326 (S101 board), Android 8.1, NAND | Frameo beta menu, USB | Shipped `su` and `adb root` | [veswwe-10.1.md](veswwe-10.1.md) |
| Uhale SI006 | Spreadtrum `sp7731g_1h10`, Android 6.0 | No. Hidden Settings, then `unauthorized` | Terminal app `su`, then host key added to `adb_keys` | [si006-uhale.md](si006-uhale.md) |

## Patterns so far

- **Frameo frames** often have an ADB toggle under Settings → About → Beta Program.
- **Try ADB over the network** (`adb connect <ip>:5555`) as well as USB. Several Allwinner frames
  ship with root ADB open on Wi-Fi with no key check. That is convenient, but anything on the same
  network gets root, so keep these frames on an isolated network.
- **No SystemUI** (no status or navigation bar) is common. Then an ADB `unauthorized` prompt has
  nowhere to appear.
- **Cables:** several USB-C frames need a USB-A to USB-C data cable. The cable in the box is often
  power only.
