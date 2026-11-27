"""Load and check the pipeline YAML. Relative paths resolve against the repository root.

Paths must be POSIX paths that both the driver's Python and Spark can open: local disk here, and on a cluster a
mounted volume (for example a Databricks Unity Catalog volume under /Volumes/...). Hashing and file moves are done
by the driver with ordinary file operations.
"""
import os
from pathlib import Path

import yaml

from masld_spark.schemas import TABLES

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "paths": ["raw_root", "out_root", "runs_root", "local_dir"],
    "spark": ["master", "app_name", "conf"],
    "ingest": ["tolerance_pct", "require_manifest_match", "partitions", "expected_rows"],
}


class ConfigError(ValueError):
    pass


def resolve(p):
    p = Path(os.path.expanduser(str(p)))
    return p if p.is_absolute() else ROOT / p


def _merge(base, over, replace=(), prefix=""):
    """Deep merge: dictionaries merge key by key; anything else, or a dotted path listed in `replace`, is overridden."""
    out = dict(base)
    for k, v in over.items():
        path = f"{prefix}{k}"
        if isinstance(v, dict) and isinstance(out.get(k), dict) and path not in replace:
            out[k] = _merge(out[k], v, replace, path + ".")
        else:
            out[k] = v
    return out


def load(path):
    """A config may name `extends: <base config>`; it then lists only what differs. `extends_replace` names dotted
    sections taken whole from this file instead of merged (for example spark.conf on a cluster)."""
    with open(resolve(path)) as fh:
        cfg = yaml.safe_load(fh)
    if "extends" in cfg:
        base_path = cfg.pop("extends")
        replace = tuple(cfg.pop("extends_replace", ()) or ())
        base = {k: v for k, v in load(base_path).items() if not k.startswith("_")}
        cfg = _merge(base, cfg, replace)
        cfg["_extends"] = str(resolve(base_path))
    cfg["_source"] = str(resolve(path))
    return check(cfg)


def check(cfg):
    for section, keys in REQUIRED.items():
        if section not in cfg:
            raise ConfigError(f"missing section '{section}'")
        for k in keys:
            if k not in cfg[section]:
                raise ConfigError(f"missing key '{section}.{k}'")
    ing = cfg["ingest"]
    for key in ("partitions", "expected_rows"):
        given = set(ing[key] or {})
        if given != set(TABLES):
            raise ConfigError(f"ingest.{key} must list exactly the 12 tables; missing {sorted(set(TABLES) - given)}, "
                              f"unknown {sorted(given - set(TABLES))}")
    for t, n in ing["partitions"].items():
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ConfigError(f"ingest.partitions.{t} must be an integer >= 1")
    for t, n in ing["expected_rows"].items():
        if n is not None and (not isinstance(n, int) or isinstance(n, bool) or n < 0):
            raise ConfigError(f"ingest.expected_rows.{t} must be null or an integer >= 0")
    tol = ing["tolerance_pct"]
    if not isinstance(tol, (int, float)) or isinstance(tol, bool) or tol < 0:
        raise ConfigError("ingest.tolerance_pct must be a number >= 0")
    if not isinstance(ing["require_manifest_match"], bool):
        raise ConfigError("ingest.require_manifest_match must be true or false")
    return cfg


def paths(cfg):
    return {k: resolve(v) for k, v in cfg["paths"].items()}
