# Running the PySpark pipeline on a Databricks cluster

The PySpark pipeline (`masld_spark/`, see the README) runs locally in Spark local mode. The same code runs on a Databricks cluster. Only the configuration changes: `conf/spark_cluster.yaml` lists the differences from `conf/spark_local.yaml`.

**Status: written, not yet run on a cluster.** Nothing here has been tested on Databricks. The first cluster run should start with Step 1 alone, and its output should be read before going further (see "What to check first").

## Ground rules

- **Your account only.** Use only a cloud account and Databricks workspace that you control and that meets the PhysioNet Credentialed Health Data Use Agreement. The agreement's terms are the authority; this guide does not interpret them.
- **Who has access.** Everyone with access to the data needs their own PhysioNet credentialing.
- **Storage.** Keep the data in a Unity Catalog volume that only you can read. Do not share it, publish it or link it.
- **Turn off AI features.** In the workspace settings, turn off Databricks Assistant and other AI-assisted features. They can send notebook and query context to a model service.
- **Logs on the cluster.** JVM logs go to the cluster's driver logs instead of `runs/<name>/private/`. Spark error messages can quote a record, so treat those logs as credentialed data.
- **Pasting output.** As locally, paste only the console output and `runs/<name>/run.json`. Never paste logs.
- **Cost.** A cluster costs money for as long as it runs. Set auto-termination (for example 15 minutes) and delete the volume's contents when the work is finished.

## What runs where

| Step | Cluster | Notes |
| --- | --- | --- |
| 1 ingest, 2 cohort, 4 splits, 3 notes, 5 gates, 6b scale | yes | `scripts/spark_job.py <step>` |
| 6a parity | local only | It reads the current pipeline's stored files, which stay on the local machine. |

The expected row counts, the population references and the tokenizer revisions are inherited from the local config. A cluster run is therefore checked against the same numbers as the local run.

## One-time setup

1. **Workspace and storage.** Create a catalog, a schema and a volume (Catalog Explorer, or `CREATE VOLUME <catalog>.<schema>.<volume>;`). Check that only you hold grants on it.
2. **Compute.**
   - **Mode:** classic compute in dedicated (single-user) access mode. The code reads JVM memory metrics and ships its Python files with `addPyFile`; Spark Connect / shared mode is not supported here.
   - **Runtime:** a Databricks Runtime whose release notes list Apache Spark 4.1 and Python 3.12, to match the local PySpark 4.1.4.
   - **Cluster libraries (PyPI, pinned):** `transformers==5.17.0`, `tokenizers==0.23.2`, `duckdb==1.5.4`, `huggingface-hub==1.32.0`, `regex==2026.9.10`.
   - **Size:** a modest memory-optimised cluster, for example a driver and 4 workers with 8 cores and 64 GB each. For comparison, locally the whole pipeline ran on 10 cores with a 16 GB heap in about 1 hour 10 minutes; the note step (45 minutes) was the longest. Price the node-hours with your provider before starting.
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

## Moving the data (commands you run)

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

## Running a step

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

## What to check first

- **File operations on the volume.** The pipeline writes each table to a hidden temporary folder, then renames it into place, using ordinary file operations on the driver. Volumes are reached through a mounted file system, and whether a folder rename behaves there as it does on local disk has not been tested. If Step 1 fails with a file-system error, stop and report it; do not work around it by hand.
- **Checksums.** Step 1's output should show every file matching its manifest and every row count passing, as locally.
- **Timings.** Compare the cluster's `scale` report with the local one.
