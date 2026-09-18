# ActionProof — Performance Qualification

This page records the local performance qualification used for the hackathon demo.

## Run configuration

- Workload: **mixed**
- Measured iterations: **1000**
- Warmup: **10**
- Error rate: **0.00%**
- Wall time: **200.0 s**
- Source revision: [`d48cd1f65296b451a8bd76f963d271ace03c2c2e`](https://github.com/sagar-systems-lab/actionproof/commit/d48cd1f65296b451a8bd76f963d271ace03c2c2e)

## Observed latency

| Metric | p50 | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: |
| Moss retrieval | 19.3 ms | 23.9 ms | 26.4 ms | 34.1 ms |
| Policy evaluation | 9.0 µs | 29.9 µs | 42.7 µs | 74.7 µs |
| Proof build | 159.1 µs | 460.5 µs | 621.9 µs | 992.5 µs |
| **Total preflight** | **19.7 ms** | **24.6 ms** | **26.9 ms** | **34.5 ms** |

These are observed ActionProof measurements from the real preflight engine. No sponsor benchmark values are used as ActionProof results.

For methodology and reproducibility rules, see [Benchmark methodology](../../benchmark-methodology.md).

## Evidence

The image below is a crop of the local qualification screen showing the measured distribution, workload, iteration count, error rate, wall time, and source revision.

![ActionProof 1000 mixed-run performance qualification](./ACTIONPROOF_1000_MIXED_RUNS_EVIDENCE.jpg)
