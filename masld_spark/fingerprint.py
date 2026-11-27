"""SHA-256 fingerprints of the raw files, checked against the PhysioNet SHA256SUMS*.txt manifests in the raw root.

The manifest parser is the repository's own (scripts/run0919_data_inventory.parse_manifests: hash and filename
lines only, never echoed). Files are opened in binary mode and streamed; nothing is parsed.
"""
import hashlib

from scripts.run0919_data_inventory import parse_manifests


def sha256_file(path, chunk=8 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def manifests(raw_root):
    """-> (manifest file names, {basename: {manifest name: hash}})"""
    return parse_manifests(raw_root)


def check(basename, digest, listed):
    """-> {"status": match | mismatch | missing, "manifests": [...]}"""
    entries = listed.get(basename, {})
    if not entries:
        return {"status": "missing", "manifests": []}
    status = "match" if all(h == digest for h in entries.values()) else "mismatch"
    return {"status": status, "manifests": sorted(entries)}
