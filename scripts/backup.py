"""
Uso:
    python scripts/backup.py              # sube los tres
    python scripts/backup.py postgres
    python scripts/backup.py mongo
    python scripts/backup.py data
    python scripts/backup.py pull-data    # descarga y extrae el zip más reciente de data/

Variables en .env.local:
    ETL_DATABASE_URL, ETL_MONGO_URL, S3_BUCKET
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent


def _check_cmd(name):
    if shutil.which(name) is None:
        print(f"ERROR: '{name}' no encontrado en PATH.")
        sys.exit(1)


def _dump_to_gz(cmd, dest):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with gzip.open(dest, "wb") as gz:
        shutil.copyfileobj(proc.stdout, gz)
    _, stderr = proc.communicate()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, stderr=stderr)


def backup_postgres(pg_url, tmp, ts, s3, bucket):
    dest = tmp / f"postgres_{ts}.sql.gz"
    key = f"backups/postgresql/postgres_{ts}.sql.gz"
    _dump_to_gz(["pg_dump", pg_url, "--no-owner", "--no-privileges"], dest)
    s3.upload_file(str(dest), bucket, key)
    print(f"postgres OK  s3://{bucket}/{key}")


def backup_mongo(mongo_url, tmp, ts, s3, bucket):
    dest = tmp / f"mongo_{ts}.archive.gz"
    key = f"backups/mongo/mongo_{ts}.archive.gz"
    _dump_to_gz(["mongodump", "--uri", mongo_url, "--archive"], dest)
    s3.upload_file(str(dest), bucket, key)
    print(f"mongo OK     s3://{bucket}/{key}")


def backup_data(tmp, ts, s3, bucket):
    dest = tmp / f"data_{ts}.zip"
    key = f"data/data_{ts}.zip"
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted((ROOT / "data").rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(ROOT))
    s3.upload_file(str(dest), bucket, key)
    print(f"data OK      s3://{bucket}/{key}")


def pull_data(tmp, s3, bucket):
    response = s3.list_objects_v2(Bucket=bucket, Prefix="data/data_")
    objects = response.get("Contents", [])
    if not objects:
        print("ERROR: no hay backups de data en S3.")
        sys.exit(1)

    latest = max(objects, key=lambda o: o["LastModified"])
    key = latest["Key"]
    dest = tmp / "data_pull.zip"

    print(f"descargando s3://{bucket}/{key} ...")
    s3.download_file(bucket, key, str(dest))

    with zipfile.ZipFile(dest, "r") as zf:
        zf.extractall(ROOT)

    print(f"pull-data OK  extraido en {ROOT / 'data'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", choices=["postgres", "mongo", "data", "pull-data"])
    args = parser.parse_args()

    load_dotenv(ROOT / ".env.local")

    pg_url = os.environ.get("ETL_DATABASE_URL")
    mongo_url = os.environ.get("ETL_MONGO_URL")
    bucket = os.environ.get("S3_BUCKET")

    if not bucket:
        print("ERROR: Falta S3_BUCKET")
        sys.exit(1)

    run_pull = args.target == "pull-data"
    run_postgres = not run_pull and args.target in (None, "postgres")
    run_mongo = not run_pull and args.target in (None, "mongo")
    run_data = not run_pull and args.target in (None, "data")

    if run_postgres:
        _check_cmd("pg_dump")
    if run_mongo:
        _check_cmd("mongodump")

    s3 = boto3.client("s3")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        if run_pull:
            pull_data(tmp, s3, bucket)
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            if run_postgres:
                backup_postgres(pg_url, tmp, ts, s3, bucket)
            if run_mongo:
                backup_mongo(mongo_url, tmp, ts, s3, bucket)
            if run_data:
                backup_data(tmp, ts, s3, bucket)


if __name__ == "__main__":
    main()
