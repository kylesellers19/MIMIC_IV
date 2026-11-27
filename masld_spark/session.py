"""Build the SparkSession from the YAML config.

The JVM's log goes to a file under runs/<name>/private/ and never to the console: Spark error messages can quote the
CSV record or value that failed, and only aggregates may be printed. On a cluster where a session already exists
(spark.master: null), getOrCreate() returns it and only runtime-settable options apply.
"""
import logging

from masld_spark.config import paths

LOG4J2 = """status = error
appender.file.type = File
appender.file.name = file
appender.file.fileName = {log}
appender.file.layout.type = PatternLayout
appender.file.layout.pattern = %d{{ISO8601}} %p %c{{1}}: %m%n
rootLogger.level = info
rootLogger.appenderRef.file.ref = file
"""


def build(cfg, private_dir=None):
    from pyspark.sql import SparkSession

    logging.getLogger("py4j").setLevel(logging.WARNING)
    p = paths(cfg)
    p["local_dir"].mkdir(parents=True, exist_ok=True)
    conf = {k: (str(v).lower() if isinstance(v, bool) else str(v)) for k, v in (cfg["spark"]["conf"] or {}).items()}
    conf.setdefault("spark.local.dir", str(p["local_dir"]))   # shuffle/spill files hold patient data: keep them under data/
    if private_dir is not None:
        private_dir.mkdir(parents=True, exist_ok=True)
        props = private_dir / "log4j2.properties"
        props.write_text(LOG4J2.format(log=private_dir / "spark-jvm.log"))
        extra = conf.get("spark.driver.extraJavaOptions", "")
        conf["spark.driver.extraJavaOptions"] = f"{extra} -Dlog4j2.configurationFile=file:{props}".strip()
    b = SparkSession.builder.appName(cfg["spark"]["app_name"])
    if cfg["spark"]["master"]:
        b = b.master(cfg["spark"]["master"])
    for k, v in conf.items():
        b = b.config(k, v)
    return b.getOrCreate()
