# Expose storage over USB as NORMAL, WRITABLE disks.
# LUN 0 is the SD card (mmc 0), LUN 1 the eMMC (mmc 1). Identify them by size on the host.
# Only write to these disks with a guarded, verified writer script. Never format or
# let the host "initialize" them.
ums 0 mmc 0,1 || ums 0 mmc 1 || ums 0 mmc 0
