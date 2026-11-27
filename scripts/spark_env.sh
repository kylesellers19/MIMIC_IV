#!/bin/zsh
# PySpark pipeline — run a Python command with the Spark environment:
#   JDK 21 from Homebrew (override with SPARK_JAVA_HOME), the .venv-spark interpreter for driver and workers,
#   the repository on PYTHONPATH, Hugging Face telemetry off.
# The September environment (.venv, scripts/run0919_env.sh) is separate and untouched.
cd "$(dirname "$0")/.."
export JAVA_HOME="${SPARK_JAVA_HOME:-/opt/homebrew/opt/openjdk@21}"
export PYSPARK_PYTHON="$PWD/.venv-spark/bin/python"
export PYSPARK_DRIVER_PYTHON="$PYSPARK_PYTHON"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_DISABLE_TELEMETRY=1
exec "$PYSPARK_PYTHON" "$@"
