#!/usr/bin/env python3
"""Download immutable inputs and record SHA-256 provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

PDBS = {
    "6XG5": "https://files.rcsb.org/download/6XG5.pdb",
    "6XG4": "https://files.rcsb.org/download/6XG4.pdb",
}


def download(url: str, destination: Path) -> str:
    request = Request(url, headers={"User-Agent": "dhfr-inquanto-resistance/1.0"})
    digest = hashlib.sha256()
    with urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("data/raw/pdbs"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for pdb_id, url in PDBS.items():
        destination = args.outdir / f"{pdb_id}.pdb"
        if destination.exists() and not args.force:
            sha256 = hashlib.sha256(destination.read_bytes()).hexdigest()
            status = "cached"
        else:
            sha256 = download(url, destination)
            status = "downloaded"
        print(f"{pdb_id}: {status} ({sha256[:16]}...)")
        rows.append((pdb_id, url, datetime.now(timezone.utc).isoformat(), sha256))
    with (args.outdir / "manifest.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("pdb_id", "source_url", "access_date_utc", "sha256"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
