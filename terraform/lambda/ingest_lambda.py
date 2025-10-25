import os, io, csv, time, json, hashlib
import urllib.parse
import boto3, botocore
import requests

BUCKET        = os.environ["BUCKET"]
PR_PREFIX     = os.environ.get("PR_PREFIX", "bls/pr/")
JSON_CSV_KEY  = os.environ.get("JSON_CSV_KEY", "bls/api/us_population_csv/us_population_2013_2018.csv")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "you@example.com")

BLS_ROOT = "https://download.bls.gov/pub/time.series/pr/"
TIMEOUT  = 20

session = requests.Session()
session.headers.update({
    "User-Agent": f"Rearc Quest / Barry Petersen ({CONTACT_EMAIL})",
    "From": CONTACT_EMAIL,
    "Accept": "*/*",
})

s3 = boto3.client("s3")

def _list_bls():
    r = session.get(BLS_ROOT, timeout=TIMEOUT)
    r.raise_for_status()
    # crude href capture
    import re
    names = re.findall(r'href=[\'"]([^\'"]+)[\'"]', r.text, flags=re.I)
    files = [n for n in names if n and not n.endswith("/")]
    # return absolute URLs + names
    return [(BLS_ROOT + f, f) for f in files]

def _exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
            return False
        raise

def _download(url):
    r = session.get(url, timeout=TIMEOUT)
    if r.status_code == 403:
        raise RuntimeError("403 from BLS — check User-Agent/From headers.")
    r.raise_for_status()
    return r.content

def _ingest_bls_to_s3():
    """Part 1: sync pr/*, idempotent via HEAD/exists check."""
    added = 0
    for url, name in _list_bls():
        key = PR_PREFIX + name
        if _exists(BUCKET, key):
            continue
        blob = _download(url)
        s3.put_object(Bucket=BUCKET, Key=key, Body=blob)
        added += 1
        time.sleep(0.2)  # be polite
    return added

# For population: we’ll just ensure the CSV exists; if missing, write fallback 2013–2018.
FALLBACK = {
    2013: 316059947, 2014: 318386421, 2015: 320738994,
    2016: 323071342, 2017: 325122128, 2018: 327167434,
}

def _ensure_population_csv():
    if _exists(BUCKET, JSON_CSV_KEY):
        return "present"
    # write fallback CSV
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["year","population"])
    for y in range(2013, 2019):
        w.writerow([y, FALLBACK[y]])
    s3.put_object(Bucket=BUCKET, Key=JSON_CSV_KEY, Body=buf.getvalue().encode("utf-8"), ContentType="text/csv")
    return "created"

def handler(event, context):
    added = _ingest_bls_to_s3()
    pop_state = _ensure_population_csv()
    print(f"[ingest] added_files={added}, population_csv={pop_state}, bucket={BUCKET}")
    return {"added": added, "population_csv": pop_state}
