# E4 analysis (development topics; descriptive)

| Quantity | Value |
|---|---:|
| within-joint raw flip rate (mean of 6 pairs) | 0.182 |
| within-joint flip rate at grade>=1 | 0.128 |
| within-joint flip rate at grade>=2 | 0.082 |
| within-decide raw flip rate (mean of 6 pairs) | 0.182 |
| within-decide flip rate at grade>=1 | 0.088 |
| within-decide flip rate at grade>=2 | 0.085 |
| between-arm raw flip rate (mean of 16 pairs) | 0.306 |
| between-arm flip rate at grade>=1 (mean of 16 pairs) | 0.134 |
| between-arm flip rate at grade>=2 (mean of 16 pairs) | 0.185 |
| topic-level between minus within, mean [95% bootstrap] | 0.117 [0.067, 0.159] |

| Arm | Topic | Threshold | Positives retained per repeat | Mean |
|---|---|---:|---|---:|
| joint | CD010558 | 1 | [24, 34, 24, 18] | 25.0 |
| joint | CD010558 | 2 | [18, 20, 16, 13] | 16.8 |
| joint | CD010753 | 1 | [22, 20, 21, 21] | 21.0 |
| joint | CD010753 | 2 | [21, 16, 17, 20] | 18.5 |
| joint | CD012347 | 1 | [16, 16, 16, 16] | 16.0 |
| joint | CD012347 | 2 | [14, 14, 14, 14] | 14.0 |
| decide | CD010558 | 1 | [34, 26, 34, 34] | 32.0 |
| decide | CD010558 | 2 | [13, 17, 12, 12] | 13.5 |
| decide | CD010753 | 1 | [22, 21, 22, 21] | 21.5 |
| decide | CD010753 | 2 | [14, 13, 14, 19] | 15.0 |
| decide | CD012347 | 1 | [16, 16, 15, 16] | 15.8 |
| decide | CD012347 | 2 | [12, 12, 11, 12] | 11.8 |

| Topic | Positives | Joint, quote exact, per repeat | Joint, quote any tier, per repeat | Joint any-tier mean | Decide-only grade>=1 mean | Gain (points of recall) |
|---|---:|---|---|---:|---:|---:|
| CD010558 | 37 | [18, 29, 22, 11] | [19, 29, 22, 11] | 20.25 | 32.00 | 31.8 |
| CD010753 | 22 | [6, 5, 7, 5] | [11, 15, 14, 10] | 12.50 | 21.50 | 40.9 |
| CD012347 | 16 | [4, 4, 4, 4] | [9, 6, 9, 7] | 7.75 | 15.75 | 50.0 |

Hypotheses: {"H-A1": {"supported": false, "within_raw_mean": 0.18166666666666667, "within_thr1_mean": 0.10833333333333334}, "H-B1": {"supported": false, "between_raw_mean": 0.30625, "ratio": 1.6857798165137616}}
