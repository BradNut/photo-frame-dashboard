#!/usr/bin/env python3
"""Validate and gzip a complete PF1007L eMMC user-area capture after card-macos.py backup."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DUMP = ROOT / 'backups' / 'pf1007-emmc'
OUT = ROOT / 'backups' / 'pf1007-emmc-full.img.gz'
MANIFEST = ROOT / 'backups' / 'pf1007-emmc-full.json'
SECTOR = 512
CHUNK_SECTORS = 131072
SIZES = {'30535680': (233, 126976), '30777344': (235, 106496)}


def require(ok, msg):
    if not ok:
        raise SystemExit(f'STOP: {msg}')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while data := f.read(1 << 20):
            h.update(data)
    return h.hexdigest()


def main():
    status = {}
    raw = (DUMP / 'a33-status.txt').read_bytes().split(b'\0', 1)[0].decode('ascii', 'strict')
    for line in raw.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            status[key] = value
    require(status.get('a33_stage') == 'finished' and status.get('emmc_dev') == 'ok'
            and status.get('full_dump') == 'yes', 'not a completed full SD dump')
    require(status.get('size_name') in SIZES, 'unsupported or missing capacity probe')
    count, final_sectors = SIZES[status['size_name']]
    require(int(status.get('total', '0'), 16) == int(status['size_name']),
            'capacity probe fields disagree')
    keys = {k for k in status if k.startswith('st_')}
    require(keys == {f'st_{i:02x}' for i in range(count)}, 'missing or unexpected chunks')
    require(not OUT.exists() and not MANIFEST.exists(), 'full backup output already exists')

    total_bytes = int(status['size_name']) * SECTOR
    whole = hashlib.sha256()
    out_tmp = OUT.with_suffix(OUT.suffix + '.partial')
    try:
        with out_tmp.open('xb') as raw_gz:
          with gzip.GzipFile(fileobj=raw_gz, mode='wb', compresslevel=6, mtime=0) as gz:
            for i in range(count):
                fields = status[f'st_{i:02x}'].split()
                sectors = final_sectors if i == count - 1 else CHUNK_SECTORS
                start = i * CHUNK_SECTORS
                require(len(fields) >= 4 and fields[0] == 'ok'
                        and int(fields[1], 16) == start and int(fields[3], 16) == sectors,
                        f'bad status for chunk {i:02x}')
                path = DUMP / f'emmc-{i:02x}.bin'
                require(path.stat().st_size == sectors * SECTOR, f'wrong size: {path.name}')
                chunk_hash = digest(path)
                require(chunk_hash == fields[2].lower(), f'frame hash mismatch: {path.name}')
                chunk_bytes = path.read_bytes()
                require(not any(chunk_bytes[j:j+65536] == b'\xcc' * 65536
                                for j in range(0, len(chunk_bytes) - 65535, 65536)),
                        f'0xCC filler block: {path.name}')
                whole.update(chunk_bytes)
                gz.write(chunk_bytes)
                print(f'{i+1}/{count} {path.name}: verified')
        raw_sha = whole.hexdigest()
        readback = hashlib.sha256()
        readback_bytes = 0
        with gzip.open(out_tmp, 'rb') as gz:
            while data := gz.read(1 << 20):
                readback.update(data)
                readback_bytes += len(data)
        require(readback_bytes == total_bytes and readback.hexdigest() == raw_sha,
                'gzip readback differs from the verified chunks')
        os.replace(out_tmp, OUT)
        manifest = {'format': 'raw eMMC user area, gzip', 'sectors': int(status['size_name']),
                    'bytes': total_bytes, 'chunks': count, 'sha256_raw': raw_sha,
                    'sha256_gzip': digest(OUT), 'gzip_readback_bytes': readback_bytes,
                    'gzip_readback_sha256': readback.hexdigest(),
                    'independent_overlap': 'first 2 GiB must match prior verified SD dump; enforced by check-dump.py'}
        MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'FULL BACKUP VERIFIED: {total_bytes} bytes; SHA-256 {raw_sha}')
        print(f'Compressed backup: {OUT}')
    except BaseException:
        if out_tmp.exists():
            out_tmp.unlink()
        raise


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit(__doc__)
    main()
