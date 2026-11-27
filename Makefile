# MASLD / MIMIC-IV — PySpark pipeline, one target per step. See README, "PySpark pipeline".
# The DuckDB pipeline (run_pipeline.sh) is the version of record; these targets never write into data/processed/.
#
#   make spark-setup            create .venv-spark (Python 3.12, PySpark 4.1.4); needs uv and Homebrew openjdk@21
#   make spark-test             tests on synthetic fixtures only; touches no MIMIC file
#   make spark-ingest           Step 1: data/raw -> data/spark/ingest (hours: labevents is read by one task)
#   make spark-ingest-verify    Step 1 again after expected counts are filled in; re-hashes, reads no CSV
#   make spark-cohort           Step 2: data/spark/ingest -> data/spark/cohort (add ARGS=--force to rebuild)
#   make spark-splits           Step 4: verify and copy the frozen splits_v1 -> data/spark/splits (run before Step 3)
#   make spark-notes            Step 3: notes, rule flags, sections, rule labels, token counts, chunks -> data/spark/notes
#   make spark-gates            Step 5: validation gates; a failure quarantines the failing stage and every later one
#   make spark-gates-restore QRUN=<gates run name>   move quarantined stages back after review
#   make spark-parity           Step 6a: parity with the current pipeline's stored files (DuckDB, counts only)
#   make spark-scale            Step 6b: time per stage, peak memory, rows, notes and tokens per second
#
# Extra arguments: make spark-ingest ARGS="--tables admissions,patients"

CONF ?= conf/spark_local.yaml
ARGS ?=
QRUN ?=
RUN  := zsh scripts/spark_env.sh

.PHONY: spark-setup spark-test spark-ingest spark-ingest-verify spark-cohort spark-splits spark-notes \
        spark-gates spark-gates-restore spark-parity spark-scale

spark-setup:
	uv venv --allow-existing .venv-spark --python /opt/homebrew/opt/python@3.12/bin/python3.12
	VIRTUAL_ENV=.venv-spark uv pip install -r requirements-spark.txt

spark-test:
	$(RUN) -m pytest -q tests/spark

spark-ingest:
	$(RUN) -m masld_spark.ingest --config $(CONF) $(ARGS)

spark-ingest-verify:
	$(RUN) -m masld_spark.ingest --config $(CONF) --verify-only $(ARGS)

spark-cohort:
	$(RUN) -m masld_spark.cohort --config $(CONF) $(ARGS)

spark-splits:
	$(RUN) -m masld_spark.splits --config $(CONF) $(ARGS)

spark-notes:
	HF_HUB_OFFLINE=1 $(RUN) -m masld_spark.notes --config $(CONF) $(ARGS)

spark-gates:
	$(RUN) -m masld_spark.gates --config $(CONF) $(ARGS)

spark-gates-restore:
	@test -n "$(QRUN)" || { echo "usage: make spark-gates-restore QRUN=<gates run name>"; exit 2; }
	$(RUN) -m masld_spark.gates --config $(CONF) --restore $(QRUN)

spark-parity:
	$(RUN) -m masld_spark.parity --config $(CONF) $(ARGS)

spark-scale:
	$(RUN) -m masld_spark.scale --config $(CONF) $(ARGS)
