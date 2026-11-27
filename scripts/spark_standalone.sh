#!/bin/zsh
# PySpark pipeline — start, stop or check a Spark standalone cluster on this machine (master and workers bound to
# 127.0.0.1, each its own JVM), from the Spark that ships with .venv-spark.
#
#   zsh scripts/spark_standalone.sh start [workers=2] [cores per worker=4] [memory per worker=7g]
#   zsh scripts/spark_standalone.sh stop
#   zsh scripts/spark_standalone.sh status
#
# The master and workers run without PYTHONPATH and with their working directories outside the repository, so an
# executor can import the pipeline only from the zip scripts/spark_job.py ships: what a remote cluster would see.
# Logs and executor work directories go to runs/_standalone/private/ (they can quote records; never paste them).
# Spill files go to data/spark/_tmp_standalone/ (they hold patient data on a real run).
set -e
cd "$(dirname "$0")/.."
ROOT=$PWD
export JAVA_HOME="${SPARK_JAVA_HOME:-/opt/homebrew/opt/openjdk@21}"
SPARK_HOME="$ROOT/.venv-spark/lib/python3.12/site-packages/pyspark"
STATE="$ROOT/runs/_standalone"
MASTER="spark://127.0.0.1:7077"
cmd=${1:-status}

up() { nc -z 127.0.0.1 7077 >/dev/null 2>&1; }

case $cmd in
  start)
    n=${2:-2}; cores=${3:-4}; mem=${4:-7g}
    if up; then echo "[standalone] a master is already listening on 7077"; exit 1; fi
    mkdir -p "$STATE/private" "$ROOT/data/spark/_tmp_standalone"
    cd "$STATE"
    env -u PYTHONPATH -u PYSPARK_PYTHON -u PYSPARK_DRIVER_PYTHON SPARK_LOCAL_IP=127.0.0.1 \
      SPARK_LOCAL_DIRS="$ROOT/data/spark/_tmp_standalone" \
      nohup "$SPARK_HOME/bin/spark-class" org.apache.spark.deploy.master.Master \
        --host 127.0.0.1 --port 7077 --webui-port 8091 > "$STATE/private/master.log" 2>&1 &
    echo $! > "$STATE/master.pid"
    for _ in {1..60}; do up && break; sleep 0.5; done
    up || { echo "[standalone] master did not start (see runs/_standalone/private/master.log)"; exit 1; }
    for i in $(seq 1 $n); do
      mkdir -p "$STATE/private/work-$i"
      env -u PYTHONPATH -u PYSPARK_PYTHON -u PYSPARK_DRIVER_PYTHON SPARK_LOCAL_IP=127.0.0.1 \
        SPARK_LOCAL_DIRS="$ROOT/data/spark/_tmp_standalone" \
        nohup "$SPARK_HOME/bin/spark-class" org.apache.spark.deploy.worker.Worker \
          --host 127.0.0.1 --cores "$cores" --memory "$mem" --work-dir "$STATE/private/work-$i" \
          --webui-port $((8091 + i)) "$MASTER" > "$STATE/private/worker-$i.log" 2>&1 &
      echo $! > "$STATE/worker-$i.pid"
    done
    sleep 3
    echo "[standalone] master $MASTER, $n worker(s) x $cores cores x $mem"
    ;;
  stop)
    for f in "$STATE"/worker-*.pid(N) "$STATE"/master.pid(N); do
      kill "$(cat "$f")" 2>/dev/null || true
      rm -f "$f"
    done
    echo "[standalone] stopped"
    ;;
  status)
    if up; then echo "[standalone] master listening on 7077; worker pid files: $(ls "$STATE"/worker-*.pid(N) 2>/dev/null | wc -l | tr -d ' ')"
    else echo "[standalone] not running"; fi
    ;;
  *) echo "usage: $0 start [workers] [cores] [memory] | stop | status"; exit 2 ;;
esac
