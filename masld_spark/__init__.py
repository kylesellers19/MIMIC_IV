"""PySpark reimplementation of the MASLD / MIMIC-IV data preparation, checked for parity against the DuckDB pipeline.

The DuckDB pipeline under scripts/ stays the version of record. Nothing here writes into data/processed/, and the
frozen definitions are imported or copied from the repository, never re-decided. Output goes to data/spark/
(git-ignored); run logs go to runs/<name>/ (git-ignored). Scripts print aggregates only.
"""
