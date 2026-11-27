"""PySpark pipeline tests: synthetic fixtures only, never a MIMIC file.

The suite runs in .venv-spark (make spark-test). Under the September .venv, which has no PySpark, the files here are
not collected, so `pytest tests/` there behaves as before.
"""
import os
import sys

import pytest

try:
    import pyspark  # noqa: F401
except ImportError:
    collect_ignore_glob = ["test_*.py"]

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.environ.setdefault("JAVA_HOME", "/opt/homebrew/opt/openjdk@21")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


@pytest.fixture(scope="session")
def spark(tmp_path_factory):
    from pyspark.sql import SparkSession
    local = tmp_path_factory.mktemp("spark-local")
    s = (SparkSession.builder.master("local[2]").appName("masld-spark-tests")
         .config("spark.ui.enabled", "false").config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.shuffle.partitions", "4").config("spark.sql.session.timeZone", "UTC")
         .config("spark.driver.bindAddress", "127.0.0.1").config("spark.driver.host", "localhost")
         .config("spark.local.dir", str(local)).getOrCreate())
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()
