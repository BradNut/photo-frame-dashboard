#!/usr/bin/env python3
"""Prepare a guarded userdata patch by diffing two copies of the /data partition.

This only reads the two local images and writes payloads + a plan to
diagnostics/a33-data-patch/. Nothing here touches a device.

Usage:
  python3 -I scripts/a33-uboot/data-patch-prepare.py \
      <orig-data-partition.img> <edited-data-partition.img> <data-partition-start-sector>

<data-partition-start-sector> is the /data partition's start sector within the full
eMMC (from the MBR/EBR you already parsed), so the plan's offsets are absolute eMMC
byte offsets the host writer can use directly against the live disk.
"""
import hashlib
import json
import sys
from pathlib import Path

SECTOR = 512
# Fine-grained scan granularity once a coarse (1 MiB) pass has found a hit.
COARSE = 1024 * 1024
FINE = SECTOR

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "diagnostics/a33-data-patch"


def fail(message):
    sys.exit(f"STOP: {message}")


def coarse_diff_regions(orig_path, edited_path, size):
    regions = []
    with open(orig_path, "rb") as fo, open(edited_path, "rb") as fe:
        off = 0
        while off < size:
            chunk = min(COARSE, size - off)
            bo = fo.read(chunk)
            be = fe.read(chunk)
            if bo != be:
                regions.append((off, chunk))
            off += chunk
    return regions


def fine_ranges(orig_path, edited_path, regions):
    ranges = []
    with open(orig_path, "rb") as fo, open(edited_path, "rb") as fe:
        for base, length in regions:
            fo.seek(base)
            fe.seek(base)
            off = base
            end = base + length
            cur_start = None
            while off < end:
                bo = fo.read(FINE)
                be = fe.read(FINE)
                if bo != be:
                    if cur_start is None:
                        cur_start = off
                    cur_end = off + FINE
                else:
                    if cur_start is not None:
                        ranges.append((cur_start, cur_end))
                        cur_start = None
                off += FINE
            if cur_start is not None:
                ranges.append((cur_start, cur_end))
    return ranges


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    orig_path = Path(sys.argv[1]).resolve(strict=True)
    edited_path = Path(sys.argv[2]).resolve(strict=True)
    partition_start_sector = int(sys.argv[3])
    partition_start_byte = partition_start_sector * SECTOR

    size = orig_path.stat().st_size
    if edited_path.stat().st_size != size:
        fail("orig and edited images are different sizes")

    print("Coarse (1 MiB) scan...")
    regions = coarse_diff_regions(orig_path, edited_path, size)
    print(f"  {len(regions)} coarse region(s) differ")

    print("Fine (sector) scan of those regions...")
    ranges = fine_ranges(orig_path, edited_path, regions)
    print(f"  {len(ranges)} byte range(s) differ, {sum(e - s for s, e in ranges)} bytes total")

    if OUT.exists():
        fail(f"{OUT} already exists; remove it first to re-prepare")
    OUT.mkdir(parents=True)

    writes = []
    with open(orig_path, "rb") as fo, open(edited_path, "rb") as fe:
        for i, (s, e) in enumerate(ranges):
            fo.seek(s)
            fe.seek(s)
            orig_bytes = fo.read(e - s)
            new_bytes = fe.read(e - s)
            assert orig_bytes != new_bytes
            orig_file = f"range-{i:02d}.orig"
            new_file = f"range-{i:02d}.new"
            (OUT / orig_file).write_bytes(orig_bytes)
            (OUT / new_file).write_bytes(new_bytes)
            abs_byte = partition_start_byte + s
            if abs_byte % SECTOR:
                fail(f"range {i} is not sector-aligned")
            writes.append({
                "range": i,
                "partition_relative_byte": s,
                "absolute_sector": abs_byte // SECTOR,
                "sectors": (e - s) // SECTOR,
                "length": e - s,
                "orig_file": orig_file,
                "new_file": new_file,
                "orig_sha256": hashlib.sha256(orig_bytes).hexdigest(),
                "new_sha256": hashlib.sha256(new_bytes).hexdigest(),
            })

    plan = {
        "partition_start_sector": partition_start_sector,
        "source_orig_image": str(orig_path),
        "source_edited_image": str(edited_path),
        "writes": writes,
    }
    (OUT / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(f"\nWrote plan for {len(writes)} range(s) to {OUT / 'plan.json'}")
    for w in writes:
        print(f"  range {w['range']}: absolute sector {w['absolute_sector']}, "
              f"{w['sectors']} sector(s), {w['length']} bytes")


if __name__ == "__main__":
    main()
