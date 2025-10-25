import os, csv, io, json, boto3

BUCKET      = os.environ["BUCKET"]
PR_PREFIX   = os.environ.get("PR_PREFIX", "bls/pr/")
POP_CSV_KEY = os.environ.get("POP_CSV_KEY", "bls/api/us_population_csv/us_population_2013_2018.csv")

s3 = boto3.client("s3")

def _read_s3_text(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")

def _load_population():
    text = _read_s3_text(BUCKET, POP_CSV_KEY)
    rdr = csv.DictReader(io.StringIO(text))
    data = [(int(r["year"]), int(r["population"])) for r in rdr]
    return dict(data)  # {year: population}

def _load_pr_current():
    # read pr.data.0.Current in-memory (TSV). We’ll pick just that file.
    key = PR_PREFIX + "pr.data.0.Current"
    text = _read_s3_text(BUCKET, key)
    rdr = csv.DictReader(io.StringIO(text), delimiter="\t")
    rows = []
    for r in rdr:
        try:
            rows.append({
                "series_id": (r["series_id"] or "").strip(),
                "year": int(r["year"]),
                "period": r["period"],
                "value": float(r["value"])
            })
        except Exception:
            pass
    return rows

def _mean_std(vals):
    import math
    n = len(vals)
    if n == 0: return (None, None)
    mean = sum(vals) / n
    var  = sum((x-mean)**2 for x in vals) / (n-1) if n > 1 else 0.0
    return (mean, math.sqrt(var))

def handler(event, context):
    pop = _load_population()
    pr  = _load_pr_current()

    # 3a: mean/stddev for 2013..2018
    years = [y for y in range(2013, 2019) if y in pop]
    pop_vals = [pop[y] for y in years]
    mean, stdev = _mean_std(pop_vals)
    print(f"[report 3a] years={years} mean={mean} stddev={stdev}")

    # 3b: best year per series (sum of Q01..Q04)
    from collections import defaultdict
    sums = defaultdict(lambda: defaultdict(float))  # series -> year -> sum
    for r in pr:
        if r["period"] in ("Q01","Q02","Q03","Q04"):
            sums[r["series_id"]][r["year"]] += r["value"]

    best = []
    for sid, per_year in sums.items():
        if not per_year: continue
        by = max(per_year.items(), key=lambda kv: kv[1])
        best.append((sid, by[0], by[1]))
    best.sort()
    print(f"[report 3b] sample={best[:10]} total_series={len(best)}")

    # 3c: PRS30006032 / Q01 join population
    target = [(r["year"], r["value"]) for r in pr
              if r["series_id"] == "PRS30006032" and r["period"] == "Q01"]
    out = [(y, v, pop.get(y)) for (y, v) in sorted(target)]
    print(f"[report 3c] PRS30006032 Q01 (year, value, population) -> {out}")

    # Done (logs are the “reports” per spec)
    return {"3a": {"years": years, "mean": mean, "stddev": stdev},
            "3b_count": len(best),
            "3c": out}
