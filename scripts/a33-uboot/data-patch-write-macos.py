#!/usr/bin/env python3
"""Guarded writer for the userdata patch in diagnostics/a33-data-patch/plan.json (macOS).

Run with the frame in FEL, loaded with the WRITABLE U-Boot
(build-uboot-write.sh), its `ums` exposing the eMMC as a normal writable
USB disk.

Usage (run from the repo root, with sudo):
  sudo python3 -I scripts/a33-uboot/data-patch-write-macos.py check   diskN <exact-bytes>
  sudo python3 -I scripts/a33-uboot/data-patch-write-macos.py write   diskN <exact-bytes>
  sudo python3 -I scripts/a33-uboot/data-patch-write-macos.py restore diskN <exact-bytes>

<exact-bytes> is the eMMC's exact size from `diskutil info diskN` (Disk Size, in
bytes). It guards against a disk number that changed after a replug.

check    reads every planned range and confirms the live disk still holds exactly
         the recorded original bytes. Writes nothing. Safe to run any time.
write    runs the same check as above first and aborts entirely (writes nothing)
         if any range has already changed. Only then does it write each range's
         new bytes, reading back and verifying immediately after each one.
restore  the mirror image: confirms each live range is either the new bytes or
         already the original, then writes the original bytes back and verifies.
"""
import hashlib
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN_DIR = REPO / "diagnostics/a33-data-patch"
PLAN_PATH = PLAN_DIR / "plan.json"
SECTOR = 512


def fail(message):
    sys.exit(f"STOP: {message}")


def load_plan():
    if not PLAN_PATH.exists():
        fail(f"{PLAN_PATH} not found; run data-patch-prepare.py first")
    plan = json.loads(PLAN_PATH.read_text())
    for w in plan["writes"]:
        orig = (PLAN_DIR / w["orig_file"]).read_bytes()
        new = (PLAN_DIR / w["new_file"]).read_bytes()
        if len(orig) != w["length"] or len(new) != w["length"]:
            fail(f"range {w['range']}: payload file size does not match plan")
        if hashlib.sha256(orig).hexdigest() != w["orig_sha256"]:
            fail(f"range {w['range']}: orig payload SHA-256 mismatch")
        if hashlib.sha256(new).hexdigest() != w["new_sha256"]:
            fail(f"range {w['range']}: new payload SHA-256 mismatch")
        w["_orig"] = orig
        w["_new"] = new
    return plan


def disk_info(identifier):
    output = subprocess.check_output(["diskutil", "info", "-plist", identifier])
    return plistlib.loads(output)


def open_disk(identifier, expected_size):
    if not re.fullmatch(r"disk\d+", identifier):
        fail("pass a whole disk like disk6, not a partition")
    info = disk_info(identifier)
    if not re.fullmatch(r"UMS disk \d+", info.get("MediaName", "")):
        fail(f"unexpected media name {info.get('MediaName')!r}; expected U-Boot's 'UMS disk N'")
    if info.get("TotalSize") != expected_size:
        fail(f"size {info.get('TotalSize')} != expected {expected_size}")
    if info.get("Internal", True) or info.get("BusProtocol") != "USB":
        fail("not an external USB disk")
    if not info.get("WritableMedia", False):
        fail("disk is read-only; load the WRITABLE U-Boot build (build-uboot-write.sh), not the backup one")
    subprocess.check_call(["diskutil", "unmountDisk", identifier])
    return f"/dev/r{identifier}"


def read_range(fd, offset, length):
    first = os.pread(fd, length, offset)
    second = os.pread(fd, length, offset)
    if len(first) != length:
        fail(f"short read at byte {offset}: got {len(first)} of {length}")
    if first != second:
        fail(f"independent re-read differs at byte {offset}")
    return first


def write_range(fd, offset, data):
    written = os.pwrite(fd, data, offset)
    os.fsync(fd)
    if written != len(data):
        fail(f"short write at byte {offset}: wrote {written} of {len(data)}")


def check(raw_path, plan, against="_orig", label="original"):
    fd = os.open(raw_path, os.O_RDONLY)
    try:
        for w in plan["writes"]:
            offset = w["absolute_sector"] * SECTOR
            live = read_range(fd, offset, w["length"])
            if live != w[against]:
                fail(f"range {w['range']} (sector {w['absolute_sector']}) does not match "
                     f"the recorded {label} bytes; stopping, nothing changed")
        print(f"All {len(plan['writes'])} range(s) match the recorded {label} bytes.")
    finally:
        os.close(fd)


def write(raw_path, plan):
    # Abort entirely, untouched, if any range has already moved off the original.
    check(raw_path, plan, against="_orig", label="original")

    fd = os.open(raw_path, os.O_RDWR)
    try:
        for w in plan["writes"]:
            offset = w["absolute_sector"] * SECTOR
            write_range(fd, offset, w["_new"])
            live = read_range(fd, offset, w["length"])
            if live != w["_new"]:
                fail(f"range {w['range']} (sector {w['absolute_sector']}) readback does not "
                     f"match the new bytes after writing; stop and investigate before continuing")
            print(f"  range {w['range']}: wrote and verified {w['length']} bytes at sector {w['absolute_sector']}")
    finally:
        os.close(fd)
    print(f"Wrote and verified all {len(plan['writes'])} range(s).")


def restore(raw_path, plan):
    fd = os.open(raw_path, os.O_RDONLY)
    try:
        for w in plan["writes"]:
            offset = w["absolute_sector"] * SECTOR
            live = read_range(fd, offset, w["length"])
            if live not in (w["_new"], w["_orig"]):
                fail(f"range {w['range']} (sector {w['absolute_sector']}) matches neither the "
                     f"new nor the original bytes; stopping, nothing changed")
    finally:
        os.close(fd)

    fd = os.open(raw_path, os.O_RDWR)
    try:
        for w in plan["writes"]:
            offset = w["absolute_sector"] * SECTOR
            write_range(fd, offset, w["_orig"])
            live = read_range(fd, offset, w["length"])
            if live != w["_orig"]:
                fail(f"range {w['range']} (sector {w['absolute_sector']}) readback does not "
                     f"match the original bytes after restoring")
            print(f"  range {w['range']}: restored and verified original bytes at sector {w['absolute_sector']}")
    finally:
        os.close(fd)
    print(f"Restored and verified all {len(plan['writes'])} range(s).")


ACTIONS = {"check": lambda rp, p: check(rp, p), "write": write, "restore": restore}


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ACTIONS:
        sys.exit(__doc__)
    if os.geteuid() != 0:
        fail("run with sudo")
    action, identifier, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
    plan = load_plan()
    raw_path = open_disk(identifier, size)
    ACTIONS[action](raw_path, plan)


if __name__ == "__main__":
    main()
