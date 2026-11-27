"""The DuckDB cross-check lists exactly the tables the Spark ingest reads, from the same module folders."""
from masld_spark.schemas import TABLES
from scripts import spark_duckdb_counts as X


def test_cross_check_covers_the_ingest_tables():
    assert X.FILES == {t: module for t, (module, _) in TABLES.items()}


def test_cross_check_formats_small_counts():
    assert X.fmt(None) == "—" and X.fmt(7) == "<11" and X.fmt(0) == "0" and X.fmt(158_374_764) == "158,374,764"
