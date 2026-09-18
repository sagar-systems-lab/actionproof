# Benchmark methodology

ActionProof measures its own preflight path. Sponsor marketing numbers are not used as product results.

## What is timed

Each benchmarked restart evaluation records monotonic nanosecond timings for:

- action normalization
- context requirement resolution
- Moss retrieval
- freshness and evidence validation
- deterministic policy evaluation
- proof construction
- total preflight

The benchmark uses the same retrieval and decision engine used by Mission Control.

## Workloads

Three workload selections are available:

- safe — reconciled state, expected ALLOW
- unsafe — unreconciled state, expected BLOCK
- mixed — alternating safe and unsafe evaluations

The safe and unsafe live-state documents are prepared before the timed samples. Setup writes are therefore not counted as preflight latency.

## Run sizes

The product exposes 100, 500, and 1000 measured iterations.

A warmup is executed before recorded samples and is stored with the result.

## Percentiles

ActionProof uses the nearest-rank method for p50, p95, and p99.

Only successful samples contribute latency values. Every failed or semantically incorrect sample increments the error count and error rate.

## Reproducibility record

Every result stores:

- source revision
- environment
- UTC timestamp
- workload
- warmup count
- iteration count
- errors and error rate
- raw samples
- aggregate p50 / p95 / p99 / max

Raw JSON results are written under benchmarks/results and are ignored by Git by default so local runs do not pollute source history.

## Integrity rules

- no fabricated values
- no copied Moss marketing benchmark
- no comparison against an unrelated external database
- optimization follows measurement
- the UI labels measurements as observed ActionProof results
