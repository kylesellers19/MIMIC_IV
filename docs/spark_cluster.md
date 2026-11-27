# Running the PySpark pipeline on a cluster

The PySpark pipeline (`masld_spark/`, see the README) runs locally in Spark local mode. The same code runs on a cluster; only the configuration changes. There are two options:

| Option | Config | Status |
| --- | --- | --- |
| A. Spark standalone: one master and worker processes, on this machine or on machines you control. No Databricks needed. | `conf/spark_standalone.yaml` | tested on this Mac, end to end on invented data (`make spark-cluster-smoke`) |
| B. Databricks, classic compute | `conf/spark_cluster.yaml` | written; never run on Databricks |

Both run each step through `scripts/spark_job.py`. That script ships `masld_spark/` and `scripts/*.py` to the executors as one zip. The standalone smoke test runs the master and workers with no `PYTHONPATH` and their working folders outside the repository. Every step passed there, including the note step, whose Python workers load the frozen rule and the tokenizers on the executors. That test exercises the code path the two options share. What only Databricks can test (volumes, runtimes, cluster libraries) is listed under option B.

## Ground rules (any cluster)

- **Your machines only.** Use only machines and accounts that you control and that meet the PhysioNet Credentialed Health Data Use Agreement. The agreement's terms are the authority; this guide does not interpret them.
- **Who has access.** Everyone with access to the data needs their own PhysioNet credentialing.
- **Data at rest.** Keep the data on storage only you can read, encrypted at rest. Do not share it, publish it or link it.
- **Network.** A standalone cluster's ports (7077, and the 8091+ web pages) must be reachable only on a private network, never from the internet.
- **Logs.** JVM and executor logs can quote a record when an error occurs, so treat them as credentialed data. As locally, paste only the console output and `runs/<name>/run.json`.
- **Cost.** Cloud machines cost money while they run. Stop them when a step finishes, and delete the data when the work is done.

## What runs where

| Step | Cluster | Notes |
| --- | --- | --- |
| 1 ingest, 2 cohort, 4 splits, 3 notes, 5 gates, 6b scale | yes | `scripts/spark_job.py <step> --config <cluster config>` |
| 6a parity | the machine holding the current pipeline's stored files | It runs in DuckDB, not Spark. |

The expected row counts, the population references and the tokenizer revisions are inherited from the local config. A cluster run is therefore checked against the same numbers as the local run.

## Option A: Spark standalone (no Databricks)

### On this Mac

The commands below start a master and two workers bound to 127.0.0.1, run the smoke test on invented data, and stop the cluster. The smoke test reads no MIMIC file.

```bash
make spark-standalone-start
```

```bash
make spark-cluster-smoke
```

```bash
make spark-standalone-stop
```

To run the real pipeline on that cluster instead of in local mode, pass the standalone config to each step:

```bash
zsh scripts/spark_env.sh scripts/spark_job.py ingest --config conf/spark_standalone.yaml
```

Then run `cohort`, `splits`, `notes`, `gates` and `scale` the same way. On one machine this is slower than local mode: two worker processes share the same cores, and every exchange of data crosses process boundaries. Its purpose is to test the cluster path, not to speed up a run.

### On machines you control

1. **Every node gets the same software at the same path:** the same repository checkout, `.venv-spark` (`make spark-setup`), and JDK 21. Executors start their Python workers with the driver's interpreter path.
2. **Shared storage.** Put `raw_root`, `out_root` and `runs_root` on a file system mounted at the same path on every node: an NFS export, or a cloud file share such as Amazon EFS or Google Filestore. The pipeline checksums, moves and writes files with ordinary file operations, so object storage (`s3://`, `gs://`) will not work for these paths.
3. **Start the master** on one node, and a worker on each of the others:

   ```bash
   SPARK_LOCAL_IP=<master private ip> .venv-spark/lib/python3.12/site-packages/pyspark/bin/spark-class org.apache.spark.deploy.master.Master --host <master private ip> --port 7077
   ```

   ```bash
   SPARK_LOCAL_IP=<worker private ip> .venv-spark/lib/python3.12/site-packages/pyspark/bin/spark-class org.apache.spark.deploy.worker.Worker --cores <cores> --memory <memory> spark://<master private ip>:7077
   ```

4. **Write a config** (git-ignored: `conf/spark_standalone.local.yaml`) with `extends: conf/spark_standalone.yaml`, the master URL, the shared paths, and executor memory and cores to fit the workers.
5. **Run the steps** with `scripts/spark_job.py` from a node that can reach the master, starting with the smoke test.

**A simpler choice at this data size.** The raw files are under 5 GB, and the whole pipeline ran in about an hour on a 10-core laptop. A single cloud machine with more cores, running `conf/spark_local.yaml` with its paths and memory changed, avoids shared storage altogether.

## Option B: Databricks

**Not tested on Databricks.** The first Databricks run should start with Step 1 alone, and its output should be read before going further (see "What to check first").

Additional rules:
- Turn off Databricks Assistant and other AI-assisted features in the workspace settings. They can send notebook and query context to a model service.
- Keep the data in a Unity Catalog volume that only you can read.
- JVM logs go to the cluster's driver logs instead of `runs/<name>/private/`.
- Set auto-termination on the cluster, for example 15 minutes.

### One-time setup

1. **Workspace and storage.** Create a catalog, a schema and a volume (Catalog Explorer, or `CREATE VOLUME <catalog>.<schema>.<volume>;`). Check that only you hold grants on it.
2. **Compute.**
   - **Mode:** classic compute in dedicated (single-user) access mode. The code reads JVM memory metrics and ships its Python files with `addPyFile`; Spark Connect / shared mode is not supported here.
   - **Runtime:** a Databricks Runtime whose release notes list Apache Spark 4.1 and Python 3.12, to match the local PySpark 4.1.4.
   - **Cluster libraries (PyPI, pinned):** `transformers==5.17.0`, `tokenizers==0.23.2`, `duckdb==1.5.4`, `huggingface-hub==1.32.0`, `regex==2026.9.10`.
   - **Size:** a modest memory-optimised cluster, for example a driver and 4 workers with 8 cores and 64 GB each. Price the node-hours with your provider before starting.
3. **Code.** Add this repository to the workspace as a Git folder. It holds code only; no data is in it.
4. **Your config.** Create `conf/spark_cluster.local.yaml` (git-ignored) in the Git folder with your volume paths:

   ```yaml
   extends: conf/spark_cluster.yaml
   paths:
     raw_root: /Volumes/<catalog>/<schema>/<volume>/mimic/raw
     out_root: /Volumes/<catalog>/<schema>/<volume>/mimic/spark
     runs_root: /Volumes/<catalog>/<schema>/<volume>/mimic/runs
   splits:
     source: /Volumes/<catalog>/<schema>/<volume>/mimic/frozen/splits_v1.parquet
   notes:
     tokenizers:
       bio_clinicalbert: {name: /Volumes/<catalog>/<schema>/<volume>/mimic/tokenizers/Bio_ClinicalBERT-d5892b39}
       clinical_longformer: {name: /Volumes/<catalog>/<schema>/<volume>/mimic/tokenizers/Clinical-Longformer-5e2ebe8f}
   ```

### Moving the data (commands you run)

Use the Databricks CLI. It transfers over TLS to the volume.

1. Upload the raw files with their PhysioNet checksum manifests. The ingest checks every file against them on the cluster.

   ```bash
   databricks fs cp --recursive data/raw dbfs:/Volumes/<catalog>/<schema>/<volume>/mimic/raw
   ```

2. Upload the frozen split file. Step 4 checks its SHA-256 against the frozen record.

   ```bash
   databricks fs cp data/processed/splits_v1.parquet dbfs:/Volumes/<catalog>/<schema>/<volume>/mimic/frozen/splits_v1.parquet
   ```

3. Copy only the tokenizer files, not the model weights, out of the local Hugging Face cache:

   ```bash
   mkdir -p data/spark/_tokenizers/Bio_ClinicalBERT-d5892b39 data/spark/_tokenizers/Clinical-Longformer-5e2ebe8f
   ```

   ```bash
   cp -L ~/.cache/huggingface/hub/models--emilyalsentzer--Bio_ClinicalBERT/snapshots/d5892b39a4adaed74b92212a44081509db72f87b/{config.json,vocab.txt} data/spark/_tokenizers/Bio_ClinicalBERT-d5892b39/
   ```

   ```bash
   cp -L ~/.cache/huggingface/hub/models--yikuan8--Clinical-Longformer/snapshots/5e2ebe8f6e98d4751eaf71a8514e0edbe73989a2/{config.json,merges.txt,special_tokens_map.json,tokenizer_config.json,vocab.json} data/spark/_tokenizers/Clinical-Longformer-5e2ebe8f/
   ```

4. Upload the tokenizer folders:

   ```bash
   databricks fs cp --recursive data/spark/_tokenizers dbfs:/Volumes/<catalog>/<schema>/<volume>/mimic/tokenizers
   ```

### Running a step

Each step is one job run on the cluster. Save this as `job.json`, with your cluster id, your Git-folder path and the step:

```json
{
  "run_name": "masld-spark-ingest",
  "tasks": [{
    "task_key": "ingest",
    "existing_cluster_id": "<cluster id>",
    "spark_python_task": {
      "python_file": "/Workspace/Users/<you>/<git folder>/scripts/spark_job.py",
      "parameters": ["ingest", "--config", "conf/spark_cluster.local.yaml"]
    }
  }]
}
```

```bash
databricks jobs submit --json @job.json
```

Run the steps in this order, one job each: `ingest`, `cohort`, `splits`, `notes`, `gates`, `scale`. Each must exit 0 before the next starts.

### What to check first

- **File operations on the volume.** The pipeline writes each table to a hidden temporary folder, then renames it into place, using ordinary file operations on the driver. Volumes are reached through a mounted file system, and whether a folder rename behaves there as it does on local disk has not been tested. If Step 1 fails with a file-system error, stop and report it; do not work around it by hand.
- **Checksums.** Step 1's output should show every file matching its manifest and every row count passing, as locally.
- **Timings.** Compare the cluster's `scale` report with the local one.
