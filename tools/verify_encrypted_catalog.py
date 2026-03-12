#!/usr/bin/env python3
"""Verify encrypted catalog integrity and decrypt a sample of records."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import hmac
import json
import struct
from pathlib import Path


def keystream(master_key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    while sum(len(b) for b in blocks) < length:
        blocks.append(hmac.new(master_key, nonce + struct.pack("<I", counter), hashlib.sha256).digest())
        counter += 1
    return b"".join(blocks)[:length]


def decrypt_record(master_key: bytes, blob: bytes) -> dict:
    nonce = blob[:16]
    tag = blob[16:32]
    ciphertext = blob[32:]

    expected = hmac.new(master_key, nonce + ciphertext, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected):
        raise ValueError("HMAC verification failed")

    stream = keystream(master_key, nonce, len(ciphertext))
    payload = bytes([c ^ s for c, s in zip(ciphertext, stream)])
    return json.loads(payload.decode())


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify encrypted catalog")
    parser.add_argument("--in", dest="in_file", type=Path, required=True)
    parser.add_argument("--key", dest="key_file", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=50)
    args = parser.parse_args()

    key = args.key_file.read_bytes()

    with gzip.open(args.in_file, "rb") as f:
        count = struct.unpack("<Q", f.read(8))[0]
        sample = min(args.sample, count)
        last_id = -1

        for _ in range(sample):
            size = struct.unpack("<H", f.read(2))[0]
            blob = f.read(size)
            record = decrypt_record(key, blob)
            if not (2 <= record["minPlayers"] <= record["maxPlayers"] <= 4):
                raise ValueError("Invalid player bounds")
            if record["id"] <= last_id:
                raise ValueError("Non-monotonic id sequence")
            last_id = record["id"]

    print(f"Verified {sample} records out of {count} total records")


if __name__ == "__main__":
    main()
