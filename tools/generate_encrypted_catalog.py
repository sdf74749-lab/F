#!/usr/bin/env python3
"""Generate an encrypted game catalog suitable for mobile offline sync.

Default size: 12,000,000 records.
Uses only Python stdlib (stream cipher + HMAC authentication) to stay portable.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import hmac
import json
import os
import random
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CatalogConfig:
    count: int
    out_file: Path
    key_file: Path
    seed: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate encrypted game catalog")
    parser.add_argument("--count", type=int, default=12_000_000, help="Number of games")
    parser.add_argument("--out", type=Path, default=Path("build/game_catalog.enc.gz"))
    parser.add_argument("--key-out", type=Path, default=Path("build/game_catalog.key"))
    parser.add_argument("--seed", type=int, default=42)
    return parser


def make_record(idx: int, rng: random.Random) -> dict:
    return {
        "id": idx,
        "mode": rng.choice(["classic", "quick", "ranked"]),
        "minPlayers": 2,
        "maxPlayers": 4,
        "elo": rng.randint(300, 3200),
        "region": rng.choice(["MENA", "EU", "NA", "ASIA", "SA"]),
        "checksum": hashlib.sha1(f"{idx}:{rng.random()}".encode()).hexdigest()[:12],
    }


def keystream(master_key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    while sum(len(b) for b in blocks) < length:
        block = hmac.new(master_key, nonce + struct.pack("<I", counter), hashlib.sha256).digest()
        blocks.append(block)
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_record(master_key: bytes, payload: bytes) -> bytes:
    nonce = os.urandom(16)
    stream = keystream(master_key, nonce, len(payload))
    ciphertext = bytes([p ^ s for p, s in zip(payload, stream)])
    tag = hmac.new(master_key, nonce + ciphertext, hashlib.sha256).digest()[:16]
    return nonce + tag + ciphertext


def write_encrypted_catalog(config: CatalogConfig) -> None:
    config.out_file.parent.mkdir(parents=True, exist_ok=True)
    master_key = os.urandom(32)
    rng = random.Random(config.seed)

    with gzip.open(config.out_file, "wb", compresslevel=6) as out_f:
        out_f.write(struct.pack("<Q", config.count))
        for idx in range(config.count):
            payload = json.dumps(make_record(idx, rng), separators=(",", ":")).encode()
            encrypted = encrypt_record(master_key, payload)
            out_f.write(struct.pack("<H", len(encrypted)))
            out_f.write(encrypted)

    config.key_file.parent.mkdir(parents=True, exist_ok=True)
    config.key_file.write_bytes(master_key)


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be > 0")

    write_encrypted_catalog(CatalogConfig(args.count, args.out, args.key_out, args.seed))
    print(f"Encrypted catalog generated: {args.out} ({args.count:,} records)")
    print(f"Key written to: {args.key_out}")
