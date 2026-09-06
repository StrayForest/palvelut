#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    path: str
    elapsed_ms: float
    status: int


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires samples")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def request(base_url: str, path: str, timeout: float) -> Sample:
    started = time.perf_counter()
    status = 0
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"User-Agent": "Finrix-Palvelut-Load-Acceptance/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
    except (urllib.error.URLError, TimeoutError, OSError):
        status = 599
    elapsed_ms = (time.perf_counter() - started) * 1000
    return Sample(path=path, elapsed_ms=elapsed_ms, status=status)


def run_phase(
    *,
    base_url: str,
    paths: list[str],
    requests: int,
    concurrency: int,
    timeout: float,
) -> list[Sample]:
    samples: list[Sample] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(request, base_url, random.choice(paths), timeout)
            for _ in range(requests)
        ]
        for future in as_completed(futures):
            samples.append(future.result())
    return samples


def summarize(samples: list[Sample]) -> dict[str, float | int]:
    elapsed = [sample.elapsed_ms for sample in samples]
    server_errors = sum(1 for sample in samples if sample.status >= 500)
    failures = sum(1 for sample in samples if sample.status < 200 or sample.status >= 400)
    return {
        "requests": len(samples),
        "p50_ms": round(statistics.median(elapsed), 2),
        "p95_ms": round(percentile(elapsed, 0.95), 2),
        "p99_ms": round(percentile(elapsed, 0.99), 2),
        "failures": failures,
        "server_errors": server_errors,
        "server_error_rate": server_errors / len(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/palvelut")
    parser.add_argument("--normal-requests", type=int, default=400)
    parser.add_argument("--normal-concurrency", type=int, default=8)
    parser.add_argument("--overload-requests", type=int, default=600)
    parser.add_argument("--overload-concurrency", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    random.seed(0)
    base = args.base_url.rstrip("/")
    warm_path = "/en/"
    search_path = "/en/search/?q=Performance"

    for _ in range(10):
        warmup = request(base, warm_path, args.timeout)
        if warmup.status != 200:
            raise SystemExit(f"warmup failed with HTTP {warmup.status}")

    warm = run_phase(
        base_url=base,
        paths=[warm_path],
        requests=args.normal_requests,
        concurrency=args.normal_concurrency,
        timeout=args.timeout,
    )
    cold = run_phase(
        base_url=base,
        paths=[f"{search_path}&load={index}" for index in range(40)],
        requests=args.normal_requests,
        concurrency=args.normal_concurrency,
        timeout=args.timeout,
    )
    overload = run_phase(
        base_url=base,
        paths=[warm_path, search_path],
        requests=args.overload_requests,
        concurrency=args.overload_concurrency,
        timeout=args.timeout,
    )

    report = {
        "warm": summarize(warm),
        "cold": summarize(cold),
        "overload": summarize(overload),
        "limits": {
            "warm_p95_ms": 300,
            "cold_p95_ms": 800,
            "normal_server_error_rate": 0.001,
            "overload_concurrency": args.overload_concurrency,
        },
    }
    print(json.dumps(report, sort_keys=True))

    failures: list[str] = []
    if float(report["warm"]["p95_ms"]) > 300:
        failures.append("warm public p95 exceeds 300 ms")
    if float(report["cold"]["p95_ms"]) > 800:
        failures.append("cold public p95 exceeds 800 ms")
    for phase in ("warm", "cold"):
        if float(report[phase]["server_error_rate"]) >= 0.001:
            failures.append(f"{phase} 5xx rate is not below 0.1%")
        if int(report[phase]["failures"]) != 0:
            failures.append(f"{phase} contains non-success responses")

    if failures:
        raise SystemExit("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
