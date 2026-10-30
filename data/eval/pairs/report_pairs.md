# Pair correlation of double-double outcomes (v1 test seasons, regular season)

Rows: scored test players with calibrated p at least 0.1; pairs formed inside each game. ratio = mean joint hit rate / mean product of the two probabilities (1.00 = independence); interval is a 500-resample block bootstrap by game date. phi = correlation of the two outcomes; resid_corr = correlation of (outcome - p). Seasons [np.int32(2023), np.int32(2024), np.int32(2025), np.int32(2026)].

| group | pairs | games | joint | product | ratio | 95% interval | phi | resid corr | mean p1 | mean p2 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| all pairs | 49,309 | 4,904 | 0.0761 | 0.0811 | 0.939 | 0.896 to 0.981 | -0.0092 | +0.0022 | 0.295 | 0.281 |
| same team | 20,915 | 4,824 | 0.0681 | 0.0742 | 0.918 | 0.864 to 0.969 | -0.0220 | -0.0005 | 0.280 | 0.280 |
| opponents | 28,394 | 4,764 | 0.0821 | 0.0862 | 0.952 | 0.912 to 0.997 | -0.0002 | +0.0040 | 0.306 | 0.283 |
| same team, both legs p>=0.3 | 2,227 | 1,748 | 0.1971 | 0.2128 | 0.926 | 0.855 to 0.998 | +0.0303 | +0.0261 | 0.445 | 0.479 |
| opponents, both legs p>=0.3 | 4,295 | 2,582 | 0.2233 | 0.2388 | 0.935 | 0.876 to 0.985 | +0.0045 | -0.0030 | 0.514 | 0.465 |
| same team, both starters | 15,909 | 4,716 | 0.0804 | 0.0806 | 0.998 | 0.942 to 1.055 | -0.0184 | +0.0089 | 0.290 | 0.296 |
| same team, starter + bench | 4,829 | 1,950 | 0.0300 | 0.0548 | 0.548 | 0.450 to 0.646 | -0.0776 | -0.0453 | 0.250 | 0.230 |
| same team, both bench | 177 | 157 | 0.0000 | 0.0275 | 0.000 | 0.000 to 0.000 | -0.0709 | -0.0299 | 0.158 | 0.175 |
| same team, both centers | 1,045 | 970 | 0.0708 | 0.1021 | 0.694 | 0.547 to 0.861 | -0.0919 | -0.0721 | 0.366 | 0.288 |
| same team, center + non-center | 10,526 | 4,148 | 0.0798 | 0.0828 | 0.964 | 0.906 to 1.028 | -0.0230 | +0.0107 | 0.295 | 0.307 |
| same team, neither a center | 9,344 | 3,764 | 0.0546 | 0.0613 | 0.890 | 0.806 to 0.984 | -0.0195 | -0.0051 | 0.252 | 0.248 |
| opponents, both centers | 3,050 | 2,298 | 0.1266 | 0.1384 | 0.915 | 0.834 to 0.997 | -0.0237 | +0.0049 | 0.398 | 0.355 |
| opponents, both starters | 22,861 | 4,699 | 0.0928 | 0.0939 | 0.988 | 0.940 to 1.031 | -0.0020 | +0.0032 | 0.320 | 0.295 |
| same team, pace slow | 6,939 | 1,689 | 0.0612 | 0.0735 | 0.833 | 0.751 to 0.916 | -0.0384 | -0.0173 | 0.279 | 0.279 |
| opponents, pace slow | 9,501 | 1,664 | 0.0773 | 0.0854 | 0.904 | 0.831 to 0.980 | -0.0014 | +0.0011 | 0.310 | 0.278 |
| same team, pace mid | 6,981 | 1,649 | 0.0733 | 0.0738 | 0.993 | 0.911 to 1.074 | -0.0014 | +0.0228 | 0.278 | 0.280 |
| opponents, pace mid | 9,458 | 1,621 | 0.0837 | 0.0871 | 0.962 | 0.892 to 1.034 | -0.0031 | +0.0032 | 0.307 | 0.283 |
| same team, pace fast | 6,995 | 1,486 | 0.0696 | 0.0751 | 0.927 | 0.840 to 1.020 | -0.0270 | -0.0081 | 0.282 | 0.280 |
| opponents, pace fast | 9,435 | 1,479 | 0.0852 | 0.0862 | 0.989 | 0.910 to 1.068 | +0.0036 | +0.0074 | 0.302 | 0.286 |
| same team, final margin < 10 | 9,926 | 2,266 | 0.0781 | 0.0742 | 1.053 | 0.958 to 1.136 | -0.0344 | -0.0146 | 0.279 | 0.280 |
| opponents, final margin < 10 | 13,473 | 2,240 | 0.1003 | 0.0861 | 1.165 | 1.097 to 1.242 | +0.0024 | +0.0023 | 0.303 | 0.284 |
| same team, both starters, final margin < 10 | 7,510 | 2,213 | 0.0936 | 0.0806 | 1.162 | 1.071 to 1.249 | -0.0311 | -0.0070 | 0.288 | 0.296 |
| same team, final margin 10 to 19 | 7,018 | 1,616 | 0.0695 | 0.0741 | 0.939 | 0.861 to 1.029 | -0.0217 | -0.0017 | 0.281 | 0.279 |
| opponents, final margin 10 to 19 | 9,531 | 1,592 | 0.0785 | 0.0864 | 0.908 | 0.839 to 0.978 | -0.0080 | -0.0092 | 0.308 | 0.282 |
| same team, both starters, final margin 10 to 19 | 5,399 | 1,582 | 0.0811 | 0.0802 | 1.011 | 0.919 to 1.104 | -0.0171 | +0.0090 | 0.291 | 0.294 |
| same team, final margin 20+ | 3,971 | 942 | 0.0405 | 0.0744 | 0.545 | 0.443 to 0.635 | -0.0152 | +0.0091 | 0.281 | 0.280 |
| opponents, final margin 20+ | 5,390 | 932 | 0.0429 | 0.0862 | 0.497 | 0.428 to 0.580 | -0.0307 | -0.0103 | 0.311 | 0.279 |
| same team, both starters, final margin 20+ | 3,000 | 921 | 0.0460 | 0.0812 | 0.566 | 0.473 to 0.681 | -0.0185 | +0.0131 | 0.292 | 0.297 |

## Same-team position pairs (at least 2,000 pairs)

| pair | pairs | joint | product | ratio | interval | resid corr |
|---|---:|---:|---:|---:|---|---:|
| same team C+F | 2,686 | 0.0585 | 0.0666 | 0.877 | 0.749 to 1.008 | +0.0044 |
| same team C+G | 2,664 | 0.1055 | 0.1009 | 1.046 | 0.949 to 1.156 | +0.0206 |
| same team F+G | 2,328 | 0.0601 | 0.0616 | 0.977 | 0.839 to 1.123 | -0.0016 |
