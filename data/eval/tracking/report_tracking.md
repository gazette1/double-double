# Tracking, opponent and matchup feature lift test

Regular-season rows, season keys 2024 to 2026 (2023-24 to 2025-26). Test 2025 is trained on 2024; test 2026 on 2024 and 2025. All variants use identical rows, hyperparameters, seed, holdout split and Platt calibration. REF is the saved v1 C_full prediction, trained on 2018 onward with all season types, so it has more history than the era-only variants; the STACK rows measure the new features as increments over REF. The RESID rows boost from logit(REF) as the initial score and see only the new features (plus min_ewm and position), so zero trees equals REF exactly and every departure from REF is chosen by the holdout; RESID_NONE is the control with no new features, and the raw rows skip the Platt step. BLEND_REF_ALL is a 0.5/0.5 logit blend of REF and BASE+ALL. The proxy price q = min(0.97, 1.08 x Baseline A) is an assumption, not a book price.

## Coverage
| season | rows | trk_5plus_prior | oppt_present | mu_present |
|---|---|---|---|---|
| 2024 | 25820 | 0.9104 | 1.0000 | 1.0000 |
| 2025 | 25723 | 0.9958 | 1.0000 | 1.0000 |
| 2026 | 26055 | 0.9983 | 1.0000 | 1.0000 |

## Metric 1: calibrated log loss, Brier, AUC
| season | model | n | base_rate | logloss | brier | auc |
|---|---|---|---|---|---|---|
| 2025 | A | 25723 | 0.0872 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | REF | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.1975 | 0.0569 | 0.8933 |
| 2025 | BASE+TRK | 25723 | 0.0872 | 0.1976 | 0.0571 | 0.8936 |
| 2025 | BASE+OPP | 25723 | 0.0872 | 0.1983 | 0.0571 | 0.8921 |
| 2025 | BASE+MU | 25723 | 0.0872 | 0.1971 | 0.0571 | 0.8935 |
| 2025 | BASE+ALL | 25723 | 0.0872 | 0.1971 | 0.0571 | 0.8946 |
| 2025 | STACK_BASE | 25723 | 0.0872 | 0.1994 | 0.0579 | 0.8897 |
| 2025 | STACK_ALL | 25723 | 0.0872 | 0.1954 | 0.0568 | 0.8961 |
| 2025 | RESID_NONE | 25723 | 0.0872 | 0.1940 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK | 25723 | 0.0872 | 0.1938 | 0.0564 | 0.8980 |
| 2025 | RESID_OPP | 25723 | 0.0872 | 0.1941 | 0.0565 | 0.8984 |
| 2025 | RESID_MU | 25723 | 0.0872 | 0.1947 | 0.0568 | 0.8973 |
| 2025 | RESID_ALL | 25723 | 0.0872 | 0.1942 | 0.0565 | 0.8983 |
| 2025 | RESID_NONE raw | 25723 | 0.0872 | 0.1935 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK raw | 25723 | 0.0872 | 0.1935 | 0.0565 | 0.8980 |
| 2025 | RESID_OPP raw | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | RESID_MU raw | 25723 | 0.0872 | 0.1943 | 0.0568 | 0.8973 |
| 2025 | RESID_ALL raw | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8983 |
| 2025 | BLEND_REF_ALL | 25723 | 0.0872 | 0.1928 | 0.0563 | 0.8990 |
| 2026 | A | 26055 | 0.0733 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | REF | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.1838 | 0.0524 | 0.8810 |
| 2026 | BASE+TRK | 26055 | 0.0733 | 0.1839 | 0.0523 | 0.8797 |
| 2026 | BASE+OPP | 26055 | 0.0733 | 0.1840 | 0.0525 | 0.8806 |
| 2026 | BASE+MU | 26055 | 0.0733 | 0.1840 | 0.0524 | 0.8806 |
| 2026 | BASE+ALL | 26055 | 0.0733 | 0.1844 | 0.0523 | 0.8796 |
| 2026 | STACK_BASE | 26055 | 0.0733 | 0.1841 | 0.0525 | 0.8800 |
| 2026 | STACK_ALL | 26055 | 0.0733 | 0.1820 | 0.0519 | 0.8848 |
| 2026 | RESID_NONE | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK | 26055 | 0.0733 | 0.1807 | 0.0517 | 0.8863 |
| 2026 | RESID_OPP | 26055 | 0.0733 | 0.1808 | 0.0517 | 0.8862 |
| 2026 | RESID_MU | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL | 26055 | 0.0733 | 0.1805 | 0.0517 | 0.8865 |
| 2026 | RESID_NONE raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK raw | 26055 | 0.0733 | 0.1806 | 0.0517 | 0.8863 |
| 2026 | RESID_OPP raw | 26055 | 0.0733 | 0.1807 | 0.0518 | 0.8862 |
| 2026 | RESID_MU raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL raw | 26055 | 0.0733 | 0.1805 | 0.0517 | 0.8865 |
| 2026 | BLEND_REF_ALL | 26055 | 0.0733 | 0.1811 | 0.0518 | 0.8853 |
| all | A | 51778 | 0.0802 | 0.1989 | 0.0557 | 0.8643 |
| all | REF | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | BASE | 51778 | 0.0802 | 0.1906 | 0.0546 | 0.8871 |
| all | BASE+TRK | 51778 | 0.0802 | 0.1907 | 0.0547 | 0.8863 |
| all | BASE+OPP | 51778 | 0.0802 | 0.1911 | 0.0548 | 0.8862 |
| all | BASE+MU | 51778 | 0.0802 | 0.1905 | 0.0547 | 0.8874 |
| all | BASE+ALL | 51778 | 0.0802 | 0.1907 | 0.0547 | 0.8872 |
| all | STACK_BASE | 51778 | 0.0802 | 0.1917 | 0.0552 | 0.8850 |
| all | STACK_ALL | 51778 | 0.0802 | 0.1887 | 0.0543 | 0.8907 |
| all | RESID_NONE | 51778 | 0.0802 | 0.1874 | 0.0541 | 0.8927 |
| all | RESID_TRK | 51778 | 0.0802 | 0.1872 | 0.0540 | 0.8926 |
| all | RESID_OPP | 51778 | 0.0802 | 0.1875 | 0.0541 | 0.8927 |
| all | RESID_MU | 51778 | 0.0802 | 0.1878 | 0.0542 | 0.8920 |
| all | RESID_ALL | 51778 | 0.0802 | 0.1873 | 0.0541 | 0.8927 |
| all | RESID_NONE raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | RESID_TRK raw | 51778 | 0.0802 | 0.1870 | 0.0541 | 0.8926 |
| all | RESID_OPP raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8927 |
| all | RESID_MU raw | 51778 | 0.0802 | 0.1875 | 0.0543 | 0.8920 |
| all | RESID_ALL raw | 51778 | 0.0802 | 0.1870 | 0.0541 | 0.8928 |
| all | BLEND_REF_ALL | 51778 | 0.0802 | 0.1869 | 0.0540 | 0.8928 |

## Bootstrap of log-loss differences (block bootstrap by game date, 1000 resamples; negative favors the model)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2025 | p_BASE+TRK_cal | p_BASE_cal | 0.00012 | -0.00052 | 0.00078 | 0.35600 |
| 2025 | p_BASE+OPP_cal | p_BASE_cal | 0.00078 | 0.00014 | 0.00152 | 0.00600 |
| 2025 | p_BASE+MU_cal | p_BASE_cal | -0.00039 | -0.00103 | 0.00025 | 0.89200 |
| 2025 | p_BASE+ALL_cal | p_BASE_cal | -0.00035 | -0.00128 | 0.00054 | 0.76100 |
| 2025 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00394 | -0.00551 | -0.00244 | 1.00000 |
| 2025 | p_STACK_ALL_cal | p_REF_cal | 0.00183 | 0.00040 | 0.00314 | 0.00700 |
| 2025 | p_STACK_BASE_cal | p_REF_cal | 0.00578 | 0.00416 | 0.00751 | 0.00000 |
| 2025 | p_BASE+ALL_cal | p_REF_cal | 0.00355 | 0.00154 | 0.00552 | 0.00000 |
| 2025 | p_RESID_NONE_cal | p_REF_cal | 0.00043 | -0.00012 | 0.00096 | 0.06300 |
| 2025 | p_RESID_TRK_cal | p_REF_cal | 0.00024 | -0.00054 | 0.00092 | 0.26000 |
| 2025 | p_RESID_OPP_cal | p_REF_cal | 0.00054 | -0.00004 | 0.00112 | 0.03600 |
| 2025 | p_RESID_MU_cal | p_REF_cal | 0.00108 | 0.00034 | 0.00182 | 0.00200 |
| 2025 | p_RESID_ALL_cal | p_REF_cal | 0.00059 | -0.00012 | 0.00123 | 0.04800 |
| 2025 | p_RESID_NONE_raw | p_REF_cal | -0.00008 | -0.00017 | 0.00002 | 0.93700 |
| 2025 | p_RESID_TRK_raw | p_REF_cal | -0.00012 | -0.00067 | 0.00043 | 0.66900 |
| 2025 | p_RESID_OPP_raw | p_REF_cal | -0.00000 | -0.00018 | 0.00018 | 0.49800 |
| 2025 | p_RESID_MU_raw | p_REF_cal | 0.00071 | 0.00025 | 0.00116 | 0.00000 |
| 2025 | p_RESID_ALL_raw | p_REF_cal | -0.00001 | -0.00037 | 0.00035 | 0.52100 |
| 2025 | p_BLEND_cal | p_REF_cal | -0.00080 | -0.00180 | 0.00017 | 0.94800 |
| 2025 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00004 | -0.00061 | 0.00050 | 0.57300 |
| 2025 | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00008 | -0.00013 | 0.00029 | 0.25900 |
| 2025 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00079 | 0.00035 | 0.00125 | 0.00000 |
| 2025 | p_RESID_ALL_raw | p_RESID_NONE_raw | 0.00006 | -0.00030 | 0.00044 | 0.35000 |
| 2026 | p_BASE+TRK_cal | p_BASE_cal | 0.00010 | -0.00063 | 0.00088 | 0.40600 |
| 2026 | p_BASE+OPP_cal | p_BASE_cal | 0.00013 | -0.00050 | 0.00078 | 0.39000 |
| 2026 | p_BASE+MU_cal | p_BASE_cal | 0.00016 | -0.00034 | 0.00062 | 0.28900 |
| 2026 | p_BASE+ALL_cal | p_BASE_cal | 0.00053 | -0.00032 | 0.00137 | 0.11400 |
| 2026 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00208 | -0.00325 | -0.00092 | 0.99900 |
| 2026 | p_STACK_ALL_cal | p_REF_cal | 0.00126 | 0.00010 | 0.00251 | 0.01300 |
| 2026 | p_STACK_BASE_cal | p_REF_cal | 0.00334 | 0.00223 | 0.00440 | 0.00000 |
| 2026 | p_BASE+ALL_cal | p_REF_cal | 0.00361 | 0.00212 | 0.00528 | 0.00000 |
| 2026 | p_RESID_NONE_cal | p_REF_cal | 0.00016 | -0.00011 | 0.00039 | 0.11400 |
| 2026 | p_RESID_TRK_cal | p_REF_cal | -0.00002 | -0.00029 | 0.00022 | 0.57800 |
| 2026 | p_RESID_OPP_cal | p_REF_cal | 0.00009 | -0.00018 | 0.00033 | 0.24000 |
| 2026 | p_RESID_MU_cal | p_REF_cal | 0.00017 | -0.00011 | 0.00040 | 0.11600 |
| 2026 | p_RESID_ALL_cal | p_REF_cal | -0.00021 | -0.00055 | 0.00012 | 0.87800 |
| 2026 | p_RESID_NONE_raw | p_REF_cal | 0.00000 | -0.00002 | 0.00003 | 0.47200 |
| 2026 | p_RESID_TRK_raw | p_REF_cal | -0.00013 | -0.00022 | -0.00003 | 0.99600 |
| 2026 | p_RESID_OPP_raw | p_REF_cal | -0.00006 | -0.00012 | 0.00001 | 0.96000 |
| 2026 | p_RESID_MU_raw | p_REF_cal | 0.00001 | -0.00002 | 0.00004 | 0.21200 |
| 2026 | p_RESID_ALL_raw | p_REF_cal | -0.00027 | -0.00050 | -0.00004 | 0.98600 |
| 2026 | p_BLEND_cal | p_REF_cal | 0.00037 | -0.00034 | 0.00114 | 0.14500 |
| 2026 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00013 | -0.00023 | -0.00003 | 0.99800 |
| 2026 | p_RESID_OPP_raw | p_RESID_NONE_raw | -0.00006 | -0.00013 | 0.00001 | 0.95400 |
| 2026 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00001 | -0.00003 | 0.00005 | 0.25800 |
| 2026 | p_RESID_ALL_raw | p_RESID_NONE_raw | -0.00027 | -0.00050 | -0.00004 | 0.98800 |
| all | p_BASE+TRK_cal | p_BASE_cal | 0.00011 | -0.00039 | 0.00062 | 0.31900 |
| all | p_BASE+OPP_cal | p_BASE_cal | 0.00045 | -0.00003 | 0.00095 | 0.03300 |
| all | p_BASE+MU_cal | p_BASE_cal | -0.00011 | -0.00050 | 0.00026 | 0.68800 |
| all | p_BASE+ALL_cal | p_BASE_cal | 0.00009 | -0.00048 | 0.00069 | 0.38500 |
| all | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00301 | -0.00403 | -0.00206 | 1.00000 |
| all | p_STACK_ALL_cal | p_REF_cal | 0.00154 | 0.00063 | 0.00240 | 0.00200 |
| all | p_STACK_BASE_cal | p_REF_cal | 0.00455 | 0.00349 | 0.00551 | 0.00000 |
| all | p_BASE+ALL_cal | p_REF_cal | 0.00358 | 0.00235 | 0.00474 | 0.00000 |
| all | p_RESID_NONE_cal | p_REF_cal | 0.00029 | -0.00001 | 0.00061 | 0.03000 |
| all | p_RESID_TRK_cal | p_REF_cal | 0.00011 | -0.00027 | 0.00049 | 0.30000 |
| all | p_RESID_OPP_cal | p_REF_cal | 0.00032 | -0.00001 | 0.00068 | 0.02800 |
| all | p_RESID_MU_cal | p_REF_cal | 0.00062 | 0.00024 | 0.00102 | 0.00000 |
| all | p_RESID_ALL_cal | p_REF_cal | 0.00019 | -0.00018 | 0.00058 | 0.18500 |
| all | p_RESID_NONE_raw | p_REF_cal | -0.00004 | -0.00008 | 0.00001 | 0.95400 |
| all | p_RESID_TRK_raw | p_REF_cal | -0.00012 | -0.00038 | 0.00014 | 0.81100 |
| all | p_RESID_OPP_raw | p_REF_cal | -0.00003 | -0.00013 | 0.00007 | 0.68200 |
| all | p_RESID_MU_raw | p_REF_cal | 0.00036 | 0.00015 | 0.00060 | 0.00000 |
| all | p_RESID_ALL_raw | p_REF_cal | -0.00014 | -0.00033 | 0.00007 | 0.89100 |
| all | p_BLEND_cal | p_REF_cal | -0.00021 | -0.00083 | 0.00038 | 0.77400 |
| all | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00009 | -0.00035 | 0.00018 | 0.72800 |
| all | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00001 | -0.00010 | 0.00013 | 0.40000 |
| all | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00040 | 0.00019 | 0.00063 | 0.00000 |
| all | p_RESID_ALL_raw | p_RESID_NONE_raw | -0.00011 | -0.00031 | 0.00012 | 0.80700 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | logloss | brier | auc |
|---|---|---|---|---|---|---|
| 2025 | A | 2129 | 0.4298 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | REF | 2129 | 0.4298 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.6604 | 0.2339 | 0.6328 |
| 2025 | BASE+TRK | 2129 | 0.4298 | 0.6611 | 0.2344 | 0.6290 |
| 2025 | BASE+OPP | 2129 | 0.4298 | 0.6622 | 0.2349 | 0.6266 |
| 2025 | BASE+MU | 2129 | 0.4298 | 0.6642 | 0.2354 | 0.6266 |
| 2025 | BASE+ALL | 2129 | 0.4298 | 0.6599 | 0.2337 | 0.6310 |
| 2025 | STACK_BASE | 2129 | 0.4298 | 0.6815 | 0.2424 | 0.6151 |
| 2025 | STACK_ALL | 2129 | 0.4298 | 0.6651 | 0.2360 | 0.6269 |
| 2025 | RESID_NONE | 2129 | 0.4298 | 0.6615 | 0.2346 | 0.6276 |
| 2025 | RESID_TRK | 2129 | 0.4298 | 0.6595 | 0.2335 | 0.6325 |
| 2025 | RESID_OPP | 2129 | 0.4298 | 0.6621 | 0.2349 | 0.6249 |
| 2025 | RESID_MU | 2129 | 0.4298 | 0.6652 | 0.2362 | 0.6181 |
| 2025 | RESID_ALL | 2129 | 0.4298 | 0.6613 | 0.2346 | 0.6263 |
| 2025 | RESID_NONE raw | 2129 | 0.4298 | 0.6633 | 0.2353 | 0.6276 |
| 2025 | RESID_TRK raw | 2129 | 0.4298 | 0.6625 | 0.2347 | 0.6325 |
| 2025 | RESID_OPP raw | 2129 | 0.4298 | 0.6642 | 0.2358 | 0.6249 |
| 2025 | RESID_MU raw | 2129 | 0.4298 | 0.6672 | 0.2370 | 0.6181 |
| 2025 | RESID_ALL raw | 2129 | 0.4298 | 0.6639 | 0.2356 | 0.6263 |
| 2025 | BLEND_REF_ALL | 2129 | 0.4298 | 0.6565 | 0.2323 | 0.6362 |
| 2026 | A | 1976 | 0.3806 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | REF | 1976 | 0.3806 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.6311 | 0.2204 | 0.6558 |
| 2026 | BASE+TRK | 1976 | 0.3806 | 0.6291 | 0.2194 | 0.6583 |
| 2026 | BASE+OPP | 1976 | 0.3806 | 0.6316 | 0.2207 | 0.6540 |
| 2026 | BASE+MU | 1976 | 0.3806 | 0.6309 | 0.2203 | 0.6548 |
| 2026 | BASE+ALL | 1976 | 0.3806 | 0.6280 | 0.2189 | 0.6593 |
| 2026 | STACK_BASE | 1976 | 0.3806 | 0.6326 | 0.2210 | 0.6497 |
| 2026 | STACK_ALL | 1976 | 0.3806 | 0.6271 | 0.2184 | 0.6615 |
| 2026 | RESID_NONE | 1976 | 0.3806 | 0.6264 | 0.2181 | 0.6620 |
| 2026 | RESID_TRK | 1976 | 0.3806 | 0.6257 | 0.2178 | 0.6638 |
| 2026 | RESID_OPP | 1976 | 0.3806 | 0.6262 | 0.2180 | 0.6633 |
| 2026 | RESID_MU | 1976 | 0.3806 | 0.6263 | 0.2181 | 0.6623 |
| 2026 | RESID_ALL | 1976 | 0.3806 | 0.6256 | 0.2178 | 0.6629 |
| 2026 | RESID_NONE raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6620 |
| 2026 | RESID_TRK raw | 1976 | 0.3806 | 0.6268 | 0.2183 | 0.6638 |
| 2026 | RESID_OPP raw | 1976 | 0.3806 | 0.6273 | 0.2185 | 0.6633 |
| 2026 | RESID_MU raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6623 |
| 2026 | RESID_ALL raw | 1976 | 0.3806 | 0.6262 | 0.2180 | 0.6629 |
| 2026 | BLEND_REF_ALL | 1976 | 0.3806 | 0.6247 | 0.2175 | 0.6648 |
| all | A | 4105 | 0.4061 | 0.6557 | 0.2318 | 0.6196 |
| all | REF | 4105 | 0.4061 | 0.6463 | 0.2274 | 0.6442 |
| all | BASE | 4105 | 0.4061 | 0.6462 | 0.2274 | 0.6456 |
| all | BASE+TRK | 4105 | 0.4061 | 0.6457 | 0.2272 | 0.6457 |
| all | BASE+OPP | 4105 | 0.4061 | 0.6475 | 0.2281 | 0.6420 |
| all | BASE+MU | 4105 | 0.4061 | 0.6482 | 0.2281 | 0.6415 |
| all | BASE+ALL | 4105 | 0.4061 | 0.6445 | 0.2266 | 0.6474 |
| all | STACK_BASE | 4105 | 0.4061 | 0.6580 | 0.2321 | 0.6279 |
| all | STACK_ALL | 4105 | 0.4061 | 0.6468 | 0.2275 | 0.6459 |
| all | RESID_NONE | 4105 | 0.4061 | 0.6446 | 0.2267 | 0.6451 |
| all | RESID_TRK | 4105 | 0.4061 | 0.6433 | 0.2259 | 0.6493 |
| all | RESID_OPP | 4105 | 0.4061 | 0.6448 | 0.2268 | 0.6445 |
| all | RESID_MU | 4105 | 0.4061 | 0.6465 | 0.2275 | 0.6402 |
| all | RESID_ALL | 4105 | 0.4061 | 0.6442 | 0.2265 | 0.6462 |
| all | RESID_NONE raw | 4105 | 0.4061 | 0.6461 | 0.2273 | 0.6451 |
| all | RESID_TRK raw | 4105 | 0.4061 | 0.6453 | 0.2268 | 0.6495 |
| all | RESID_OPP raw | 4105 | 0.4061 | 0.6464 | 0.2274 | 0.6446 |
| all | RESID_MU raw | 4105 | 0.4061 | 0.6481 | 0.2282 | 0.6405 |
| all | RESID_ALL raw | 4105 | 0.4061 | 0.6458 | 0.2272 | 0.6460 |
| all | BLEND_REF_ALL | 4105 | 0.4061 | 0.6412 | 0.2252 | 0.6529 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 | distinct_players |
|---|---|---|---|---|---|---|---|
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 | 31 |
| 2025 | REF | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 | 33 |
| 2025 | BASE | 164 | 0.7805 | 0.6829 | 0.3841 | 0.7065 | 35 |
| 2025 | BASE+TRK | 164 | 0.8110 | 0.6972 | 0.3476 | 0.7053 | 32 |
| 2025 | BASE+OPP | 164 | 0.7927 | 0.6829 | 0.3598 | 0.7000 | 34 |
| 2025 | BASE+MU | 164 | 0.8049 | 0.6911 | 0.3780 | 0.6922 | 32 |
| 2025 | BASE+ALL | 164 | 0.7927 | 0.6728 | 0.3171 | 0.6993 | 32 |
| 2025 | STACK_BASE | 164 | 0.7622 | 0.6626 | 0.3110 | 0.6552 | 35 |
| 2025 | STACK_ALL | 164 | 0.8110 | 0.7012 | 0.3720 | 0.7114 | 36 |
| 2025 | RESID_NONE | 164 | 0.8171 | 0.7012 | 0.3537 | 0.6950 | 35 |
| 2025 | RESID_TRK | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7110 | 33 |
| 2025 | RESID_OPP | 164 | 0.8415 | 0.6992 | 0.3720 | 0.6984 | 35 |
| 2025 | RESID_MU | 164 | 0.7988 | 0.6931 | 0.3354 | 0.6875 | 32 |
| 2025 | RESID_ALL | 164 | 0.8293 | 0.6870 | 0.3476 | 0.7037 | 35 |
| 2025 | RESID_NONE raw | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7390 | 35 |
| 2025 | RESID_TRK raw | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7566 | 33 |
| 2025 | RESID_OPP raw | 164 | 0.8415 | 0.6992 | 0.3720 | 0.7441 | 35 |
| 2025 | RESID_MU raw | 164 | 0.7988 | 0.6931 | 0.3354 | 0.7410 | 32 |
| 2025 | RESID_ALL raw | 164 | 0.8293 | 0.6870 | 0.3476 | 0.7490 | 35 |
| 2025 | BLEND_REF_ALL | 164 | 0.8354 | 0.6951 | 0.3659 | 0.7178 | 32 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 | 31 |
| 2026 | REF | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 | 35 |
| 2026 | BASE | 165 | 0.6848 | 0.6081 | 0.2182 | 0.6598 | 36 |
| 2026 | BASE+TRK | 165 | 0.6727 | 0.6061 | 0.2182 | 0.6273 | 35 |
| 2026 | BASE+OPP | 165 | 0.6909 | 0.6000 | 0.2121 | 0.6207 | 37 |
| 2026 | BASE+MU | 165 | 0.6727 | 0.6061 | 0.2121 | 0.6449 | 36 |
| 2026 | BASE+ALL | 165 | 0.6788 | 0.6121 | 0.2121 | 0.6201 | 34 |
| 2026 | STACK_BASE | 165 | 0.6909 | 0.5939 | 0.1697 | 0.6487 | 37 |
| 2026 | STACK_ALL | 165 | 0.6848 | 0.6242 | 0.2121 | 0.6071 | 40 |
| 2026 | RESID_NONE | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6397 | 35 |
| 2026 | RESID_TRK | 165 | 0.6909 | 0.6162 | 0.2424 | 0.6335 | 36 |
| 2026 | RESID_OPP | 165 | 0.6848 | 0.6121 | 0.2121 | 0.6380 | 35 |
| 2026 | RESID_MU | 165 | 0.6788 | 0.6121 | 0.2242 | 0.6394 | 37 |
| 2026 | RESID_ALL | 165 | 0.6848 | 0.6202 | 0.2303 | 0.6238 | 36 |
| 2026 | RESID_NONE raw | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6642 | 35 |
| 2026 | RESID_TRK raw | 165 | 0.6909 | 0.6162 | 0.2424 | 0.6612 | 36 |
| 2026 | RESID_OPP raw | 165 | 0.6848 | 0.6121 | 0.2121 | 0.6625 | 35 |
| 2026 | RESID_MU raw | 165 | 0.6788 | 0.6121 | 0.2242 | 0.6644 | 37 |
| 2026 | RESID_ALL raw | 165 | 0.6848 | 0.6202 | 0.2303 | 0.6556 | 36 |
| 2026 | BLEND_REF_ALL | 165 | 0.6970 | 0.6141 | 0.2182 | 0.6413 | 36 |
| all | A | 329 | 0.7356 | 0.6606 | 0.3040 | 0.6895 | 41 |
| all | REF | 329 | 0.7477 | 0.6484 | 0.2766 | 0.7013 | 46 |
| all | BASE | 329 | 0.7325 | 0.6454 | 0.3009 | 0.6831 | 47 |
| all | BASE+TRK | 329 | 0.7416 | 0.6515 | 0.2827 | 0.6662 | 44 |
| all | BASE+OPP | 329 | 0.7416 | 0.6413 | 0.2857 | 0.6602 | 45 |
| all | BASE+MU | 329 | 0.7386 | 0.6484 | 0.2948 | 0.6685 | 44 |
| all | BASE+ALL | 329 | 0.7356 | 0.6424 | 0.2644 | 0.6596 | 44 |
| all | STACK_BASE | 329 | 0.7264 | 0.6282 | 0.2401 | 0.6519 | 48 |
| all | STACK_ALL | 329 | 0.7477 | 0.6626 | 0.2918 | 0.6591 | 50 |
| all | RESID_NONE | 329 | 0.7508 | 0.6535 | 0.2796 | 0.6673 | 47 |
| all | RESID_TRK | 329 | 0.7538 | 0.6586 | 0.2979 | 0.6721 | 48 |
| all | RESID_OPP | 329 | 0.7629 | 0.6555 | 0.2918 | 0.6681 | 47 |
| all | RESID_MU | 329 | 0.7386 | 0.6525 | 0.2796 | 0.6634 | 46 |
| all | RESID_ALL | 329 | 0.7568 | 0.6535 | 0.2888 | 0.6636 | 48 |
| all | RESID_NONE raw | 329 | 0.7508 | 0.6535 | 0.2796 | 0.7015 | 47 |
| all | RESID_TRK raw | 329 | 0.7538 | 0.6586 | 0.2979 | 0.7087 | 48 |
| all | RESID_OPP raw | 329 | 0.7629 | 0.6555 | 0.2918 | 0.7032 | 47 |
| all | RESID_MU raw | 329 | 0.7386 | 0.6525 | 0.2796 | 0.7026 | 46 |
| all | RESID_ALL raw | 329 | 0.7568 | 0.6535 | 0.2888 | 0.7022 | 48 |
| all | BLEND_REF_ALL | 329 | 0.7660 | 0.6545 | 0.2918 | 0.6794 | 46 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | REF | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4216 | 0.3686 | 0.4614 | 0.0928 | 0.1783 |
| 2025 | BASE+TRK | 491 | 0.3890 | 0.3525 | 0.4559 | 0.1035 | 0.1183 |
| 2025 | BASE+OPP | 491 | 0.3931 | 0.3494 | 0.4510 | 0.1016 | 0.1396 |
| 2025 | BASE+MU | 491 | 0.3992 | 0.3551 | 0.4388 | 0.0837 | 0.1362 |
| 2025 | BASE+ALL | 491 | 0.3971 | 0.3347 | 0.4501 | 0.1154 | 0.2105 |
| 2025 | STACK_BASE | 491 | 0.4277 | 0.4044 | 0.4500 | 0.0457 | 0.0804 |
| 2025 | STACK_ALL | 491 | 0.4175 | 0.3645 | 0.4869 | 0.1224 | 0.2108 |
| 2025 | RESID_NONE | 491 | 0.4094 | 0.3715 | 0.4415 | 0.0700 | 0.1835 |
| 2025 | RESID_TRK | 491 | 0.3870 | 0.3591 | 0.4448 | 0.0857 | 0.1246 |
| 2025 | RESID_OPP | 491 | 0.4175 | 0.3654 | 0.4404 | 0.0750 | 0.2066 |
| 2025 | RESID_MU | 491 | 0.4053 | 0.3713 | 0.4398 | 0.0684 | 0.1627 |
| 2025 | RESID_ALL | 491 | 0.4114 | 0.3613 | 0.4422 | 0.0808 | 0.1980 |
| 2025 | RESID_NONE raw | 491 | 0.4297 | 0.4055 | 0.5004 | 0.0950 | 0.1191 |
| 2025 | RESID_TRK raw | 491 | 0.4094 | 0.3974 | 0.5126 | 0.1152 | 0.0765 |
| 2025 | RESID_OPP raw | 491 | 0.4358 | 0.3994 | 0.5027 | 0.1033 | 0.1543 |
| 2025 | RESID_MU raw | 491 | 0.4379 | 0.4027 | 0.5041 | 0.1015 | 0.1531 |
| 2025 | RESID_ALL raw | 491 | 0.4440 | 0.3956 | 0.5045 | 0.1089 | 0.1914 |
| 2025 | BLEND_REF_ALL | 491 | 0.4196 | 0.3556 | 0.4442 | 0.0885 | 0.2275 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | REF | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4263 | 0.3732 | 0.4518 | 0.0786 | 0.1891 |
| 2026 | BASE+TRK | 495 | 0.3939 | 0.3616 | 0.4098 | 0.0483 | 0.1347 |
| 2026 | BASE+OPP | 495 | 0.3980 | 0.3622 | 0.4155 | 0.0533 | 0.1286 |
| 2026 | BASE+MU | 495 | 0.3919 | 0.3580 | 0.4338 | 0.0758 | 0.1320 |
| 2026 | BASE+ALL | 495 | 0.3939 | 0.3387 | 0.3943 | 0.0556 | 0.1942 |
| 2026 | STACK_BASE | 495 | 0.4000 | 0.3710 | 0.4801 | 0.1090 | 0.1484 |
| 2026 | STACK_ALL | 495 | 0.4101 | 0.3451 | 0.4074 | 0.0622 | 0.2201 |
| 2026 | RESID_NONE | 495 | 0.4263 | 0.3638 | 0.4389 | 0.0752 | 0.2441 |
| 2026 | RESID_TRK | 495 | 0.4202 | 0.3582 | 0.4287 | 0.0706 | 0.2468 |
| 2026 | RESID_OPP | 495 | 0.4283 | 0.3609 | 0.4348 | 0.0739 | 0.2583 |
| 2026 | RESID_MU | 495 | 0.4263 | 0.3613 | 0.4370 | 0.0757 | 0.2488 |
| 2026 | RESID_ALL | 495 | 0.4162 | 0.3548 | 0.4170 | 0.0622 | 0.2319 |
| 2026 | RESID_NONE raw | 495 | 0.4424 | 0.3878 | 0.4777 | 0.0899 | 0.1996 |
| 2026 | RESID_TRK raw | 495 | 0.4444 | 0.3875 | 0.4757 | 0.0882 | 0.2188 |
| 2026 | RESID_OPP raw | 495 | 0.4424 | 0.3855 | 0.4742 | 0.0887 | 0.2259 |
| 2026 | RESID_MU raw | 495 | 0.4384 | 0.3858 | 0.4767 | 0.0909 | 0.1953 |
| 2026 | RESID_ALL raw | 495 | 0.4303 | 0.3852 | 0.4686 | 0.0834 | 0.1783 |
| 2026 | BLEND_REF_ALL | 495 | 0.4404 | 0.3614 | 0.4254 | 0.0640 | 0.2774 |
| all | A | 986 | 0.2049 | 0.2248 | 0.2081 | -0.0167 | -0.0864 |
| all | REF | 986 | 0.4371 | 0.3958 | 0.4888 | 0.0930 | 0.1662 |
| all | BASE | 986 | 0.4239 | 0.3709 | 0.4566 | 0.0856 | 0.1837 |
| all | BASE+TRK | 986 | 0.3915 | 0.3570 | 0.4328 | 0.0758 | 0.1265 |
| all | BASE+OPP | 986 | 0.3955 | 0.3558 | 0.4332 | 0.0774 | 0.1341 |
| all | BASE+MU | 986 | 0.3955 | 0.3566 | 0.4363 | 0.0797 | 0.1341 |
| all | BASE+ALL | 986 | 0.3955 | 0.3367 | 0.4221 | 0.0854 | 0.2023 |
| all | STACK_BASE | 986 | 0.4138 | 0.3876 | 0.4651 | 0.0775 | 0.1146 |
| all | STACK_ALL | 986 | 0.4138 | 0.3548 | 0.4470 | 0.0922 | 0.2154 |
| all | RESID_NONE | 986 | 0.4178 | 0.3676 | 0.4402 | 0.0726 | 0.2139 |
| all | RESID_TRK | 986 | 0.4037 | 0.3586 | 0.4367 | 0.0781 | 0.1860 |
| all | RESID_OPP | 986 | 0.4229 | 0.3631 | 0.4376 | 0.0745 | 0.2326 |
| all | RESID_MU | 986 | 0.4158 | 0.3663 | 0.4384 | 0.0721 | 0.2059 |
| all | RESID_ALL | 986 | 0.4138 | 0.3580 | 0.4295 | 0.0715 | 0.2150 |
| all | RESID_NONE raw | 986 | 0.4361 | 0.3966 | 0.4890 | 0.0924 | 0.1595 |
| all | RESID_TRK raw | 986 | 0.4270 | 0.3924 | 0.4940 | 0.1016 | 0.1479 |
| all | RESID_OPP raw | 986 | 0.4391 | 0.3925 | 0.4884 | 0.0960 | 0.1902 |
| all | RESID_MU raw | 986 | 0.4381 | 0.3942 | 0.4904 | 0.0962 | 0.1743 |
| all | RESID_ALL raw | 986 | 0.4371 | 0.3904 | 0.4865 | 0.0961 | 0.1848 |
| all | BLEND_REF_ALL | 986 | 0.4300 | 0.3585 | 0.4348 | 0.0762 | 0.2526 |

## Disagreement buckets (model minus comparison, calibrated)
| model | vs | bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|---|---|
| p_BASE+ALL_cal | p_BASE_cal | < -0.05 | 1820 | 0.3864 | 0.3096 | 0.3412 |
| p_BASE+ALL_cal | p_BASE_cal | [-0.05, 0.05] | 47900 | 0.0694 | 0.0696 | 0.0625 |
| p_BASE+ALL_cal | p_BASE_cal | > 0.05 | 2058 | 0.2253 | 0.3047 | 0.2614 |
| p_RESID_ALL_raw | p_REF_cal | < -0.05 | 1 | 0.5374 | 0.4808 | 1.0000 |
| p_RESID_ALL_raw | p_REF_cal | [-0.05, 0.05] | 51612 | 0.0817 | 0.0818 | 0.0790 |
| p_RESID_ALL_raw | p_REF_cal | > 0.05 | 165 | 0.4308 | 0.4909 | 0.4667 |
| p_STACK_ALL_cal | p_REF_cal | < -0.05 | 2663 | 0.3830 | 0.2989 | 0.3496 |
| p_STACK_ALL_cal | p_REF_cal | [-0.05, 0.05] | 47039 | 0.0582 | 0.0614 | 0.0553 |
| p_STACK_ALL_cal | p_REF_cal | > 0.05 | 2076 | 0.2570 | 0.3358 | 0.2991 |
| p_BASE+TRK_cal | p_BASE_cal | < -0.05 | 1812 | 0.3589 | 0.2842 | 0.3168 |
| p_BASE+TRK_cal | p_BASE_cal | [-0.05, 0.05] | 48750 | 0.0729 | 0.0720 | 0.0670 |
| p_BASE+TRK_cal | p_BASE_cal | > 0.05 | 1216 | 0.2376 | 0.3090 | 0.2574 |
| p_BASE+OPP_cal | p_BASE_cal | < -0.05 | 1387 | 0.4137 | 0.3374 | 0.3807 |
| p_BASE+OPP_cal | p_BASE_cal | [-0.05, 0.05] | 49373 | 0.0740 | 0.0738 | 0.0678 |
| p_BASE+OPP_cal | p_BASE_cal | > 0.05 | 1018 | 0.2613 | 0.3321 | 0.2750 |
| p_BASE+MU_cal | p_BASE_cal | < -0.05 | 1055 | 0.4187 | 0.3472 | 0.4019 |
| p_BASE+MU_cal | p_BASE_cal | [-0.05, 0.05] | 50004 | 0.0771 | 0.0763 | 0.0704 |
| p_BASE+MU_cal | p_BASE_cal | > 0.05 | 719 | 0.2749 | 0.3431 | 0.2893 |

## Gain share by feature group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+TRK | 2025 | BASE | 0.8765 | 155 |
| BASE+TRK | 2025 | TRK | 0.1235 | 59 |
| BASE+OPP | 2025 | BASE | 0.9196 | 155 |
| BASE+OPP | 2025 | OPP | 0.0804 | 35 |
| BASE+MU | 2025 | BASE | 0.9355 | 155 |
| BASE+MU | 2025 | MU | 0.0645 | 21 |
| BASE+ALL | 2025 | BASE | 0.7668 | 155 |
| BASE+ALL | 2025 | MU | 0.0404 | 21 |
| BASE+ALL | 2025 | OPP | 0.0768 | 35 |
| BASE+ALL | 2025 | TRK | 0.1161 | 59 |
| STACK_BASE | 2025 | BASE | 0.6699 | 2 |
| STACK_BASE | 2025 | REF | 0.3301 | 1 |
| STACK_ALL | 2025 | BASE | 0.0330 | 2 |
| STACK_ALL | 2025 | MU | 0.0441 | 21 |
| STACK_ALL | 2025 | OPP | 0.0628 | 35 |
| STACK_ALL | 2025 | REF | 0.5681 | 1 |
| STACK_ALL | 2025 | TRK | 0.2921 | 59 |
| RESID_NONE | 2025 | BASE | 1.0000 | 2 |
| RESID_TRK | 2025 | BASE | 0.0216 | 2 |
| RESID_TRK | 2025 | TRK | 0.9784 | 59 |
| RESID_OPP | 2025 | BASE | 0.0282 | 2 |
| RESID_OPP | 2025 | OPP | 0.9718 | 35 |
| RESID_MU | 2025 | BASE | 0.0533 | 2 |
| RESID_MU | 2025 | MU | 0.9467 | 21 |
| RESID_ALL | 2025 | BASE | 0.0062 | 2 |
| RESID_ALL | 2025 | MU | 0.1830 | 21 |
| RESID_ALL | 2025 | OPP | 0.3708 | 35 |
| RESID_ALL | 2025 | TRK | 0.4400 | 59 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+TRK | 2026 | BASE | 0.8804 | 155 |
| BASE+TRK | 2026 | TRK | 0.1196 | 59 |
| BASE+OPP | 2026 | BASE | 0.9055 | 155 |
| BASE+OPP | 2026 | OPP | 0.0945 | 35 |
| BASE+MU | 2026 | BASE | 0.9529 | 155 |
| BASE+MU | 2026 | MU | 0.0471 | 21 |
| BASE+ALL | 2026 | BASE | 0.8493 | 155 |
| BASE+ALL | 2026 | MU | 0.0222 | 21 |
| BASE+ALL | 2026 | OPP | 0.0414 | 35 |
| BASE+ALL | 2026 | TRK | 0.0871 | 59 |
| STACK_BASE | 2026 | BASE | 0.6429 | 2 |
| STACK_BASE | 2026 | REF | 0.3571 | 1 |
| STACK_ALL | 2026 | BASE | 0.0194 | 2 |
| STACK_ALL | 2026 | MU | 0.0229 | 21 |
| STACK_ALL | 2026 | OPP | 0.0294 | 35 |
| STACK_ALL | 2026 | REF | 0.6398 | 1 |
| STACK_ALL | 2026 | TRK | 0.2885 | 59 |
| RESID_NONE | 2026 | BASE | 1.0000 | 2 |
| RESID_TRK | 2026 | BASE | 0.0158 | 2 |
| RESID_TRK | 2026 | TRK | 0.9842 | 59 |
| RESID_OPP | 2026 | BASE | 0.0307 | 2 |
| RESID_OPP | 2026 | OPP | 0.9693 | 35 |
| RESID_MU | 2026 | BASE | 0.0960 | 2 |
| RESID_MU | 2026 | MU | 0.9040 | 21 |
| RESID_ALL | 2026 | BASE | 0.0109 | 2 |
| RESID_ALL | 2026 | MU | 0.1919 | 21 |
| RESID_ALL | 2026 | OPP | 0.3478 | 35 |
| RESID_ALL | 2026 | TRK | 0.4494 | 59 |

## Top 30 features by gain share (BASE+ALL, STACK_ALL and RESID_ALL)
| model | season | rank | feature | group | gain_share |
|---|---|---|---|---|---|
| BASE+ALL | 2025 | 1 | dd_rate_ewm | BASE | 0.34813 |
| BASE+ALL | 2025 | 2 | dd_rate_l20 | BASE | 0.08350 |
| BASE+ALL | 2025 | 3 | dd_rate_szn | BASE | 0.04647 |
| BASE+ALL | 2025 | 4 | prev_dd_rate | BASE | 0.03430 |
| BASE+ALL | 2025 | 5 | reb_ewm | BASE | 0.01671 |
| BASE+ALL | 2025 | 6 | reb_l20 | BASE | 0.01579 |
| BASE+ALL | 2025 | 7 | trk_potast_pg_ewm | TRK | 0.01150 |
| BASE+ALL | 2025 | 8 | dd_rate_l10 | BASE | 0.01033 |
| BASE+ALL | 2025 | 9 | trk_rebch_pg_ewm | TRK | 0.00816 |
| BASE+ALL | 2025 | 10 | reb_l10 | BASE | 0.00655 |
| BASE+ALL | 2025 | 11 | abs_absent_rebounds_pg | BASE | 0.00609 |
| BASE+ALL | 2025 | 12 | oppt_al_rebcon_share_l20 | OPP | 0.00502 |
| BASE+ALL | 2025 | 13 | reb8_rate_ewm | BASE | 0.00470 |
| BASE+ALL | 2025 | 14 | trk_rebdist_l10 | TRK | 0.00453 |
| BASE+ALL | 2025 | 15 | trk_loose_pm_l10 | TRK | 0.00444 |
| BASE+ALL | 2025 | 16 | mu_h2h_pts100 | MU | 0.00443 |
| BASE+ALL | 2025 | 17 | mu_off_fit | MU | 0.00443 |
| BASE+ALL | 2025 | 18 | reb8_rate_szn | BASE | 0.00437 |
| BASE+ALL | 2025 | 19 | min_trend | BASE | 0.00405 |
| BASE+ALL | 2025 | 20 | last_starter | BASE | 0.00405 |
| BASE+ALL | 2025 | 21 | team_reb_share_l20 | BASE | 0.00389 |
| BASE+ALL | 2025 | 22 | fta_szn | BASE | 0.00385 |
| BASE+ALL | 2025 | 23 | reb_szn | BASE | 0.00381 |
| BASE+ALL | 2025 | 24 | oppt_al_rebch_conv_l10 | OPP | 0.00378 |
| BASE+ALL | 2025 | 25 | oppt_contested_l10 | OPP | 0.00365 |
| BASE+ALL | 2025 | 26 | opp_allow_pts_szn | BASE | 0.00358 |
| BASE+ALL | 2025 | 27 | trk_passes_pm_l10 | TRK | 0.00356 |
| BASE+ALL | 2025 | 28 | oppt_al_ast_conv_l10 | OPP | 0.00339 |
| BASE+ALL | 2025 | 29 | oppx_pts36_allowed_pos_l20 | OPP | 0.00336 |
| BASE+ALL | 2025 | 30 | opp_allow_ast_szn | BASE | 0.00334 |
| STACK_ALL | 2025 | 1 | z_ref | REF | 0.56805 |
| STACK_ALL | 2025 | 2 | trk_rebch_pg_ewm | TRK | 0.12501 |
| STACK_ALL | 2025 | 3 | min_ewm | BASE | 0.03286 |
| STACK_ALL | 2025 | 4 | exp_rebch | TRK | 0.02275 |
| STACK_ALL | 2025 | 5 | trk_potast_pg_ewm | TRK | 0.01830 |
| STACK_ALL | 2025 | 6 | trk_rebch_last | TRK | 0.01130 |
| STACK_ALL | 2025 | 7 | exp_potast | TRK | 0.00919 |
| STACK_ALL | 2025 | 8 | trk_drebch_pm_ewm | TRK | 0.00747 |
| STACK_ALL | 2025 | 9 | trk_min_ewm | TRK | 0.00660 |
| STACK_ALL | 2025 | 10 | mu_off_pts100 | MU | 0.00604 |
| STACK_ALL | 2025 | 11 | trk_rebdist_l10 | TRK | 0.00597 |
| STACK_ALL | 2025 | 12 | trk_rebch_conv_ewm | TRK | 0.00498 |
| STACK_ALL | 2025 | 13 | oppt_al_rebcon_share_l20 | OPP | 0.00480 |
| STACK_ALL | 2025 | 14 | mu_def_pos_F | MU | 0.00418 |
| STACK_ALL | 2025 | 15 | oppt_al_rebch_conv_l10 | OPP | 0.00378 |
| STACK_ALL | 2025 | 16 | mu_off_fit | MU | 0.00366 |
| STACK_ALL | 2025 | 17 | oppx_ast36_allowed_pos_l20 | OPP | 0.00362 |
| STACK_ALL | 2025 | 18 | oppt_contested_l10 | OPP | 0.00334 |
| STACK_ALL | 2025 | 19 | trk_screenast_pm_ewm | TRK | 0.00321 |
| STACK_ALL | 2025 | 20 | trk_rebch_conv_l20 | TRK | 0.00311 |
| STACK_ALL | 2025 | 21 | trk_loose_pm_ewm | TRK | 0.00309 |
| STACK_ALL | 2025 | 22 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.00303 |
| STACK_ALL | 2025 | 23 | trk_potast_last | TRK | 0.00294 |
| STACK_ALL | 2025 | 24 | trk_passes_pm_l10 | TRK | 0.00276 |
| STACK_ALL | 2025 | 25 | trk_loose_pm_l10 | TRK | 0.00274 |
| STACK_ALL | 2025 | 26 | mu_def_ast_vs_exp | MU | 0.00267 |
| STACK_ALL | 2025 | 27 | oppt_al_ast_conv_l20 | OPP | 0.00263 |
| STACK_ALL | 2025 | 28 | mu_off_ast100 | MU | 0.00257 |
| STACK_ALL | 2025 | 29 | trk_astpts_pm_l10 | TRK | 0.00257 |
| STACK_ALL | 2025 | 30 | mu_off_defby_C | MU | 0.00255 |
| RESID_ALL | 2025 | 1 | oppt_al_rebcon_share_l20 | OPP | 0.04996 |
| RESID_ALL | 2025 | 2 | oppx_ast36_allowed_pos_l20 | OPP | 0.04775 |
| RESID_ALL | 2025 | 3 | trk_rebdefer_pm_ewm | TRK | 0.04070 |
| RESID_ALL | 2025 | 4 | trk_screenast_pm_l10 | TRK | 0.02748 |
| RESID_ALL | 2025 | 5 | trk_rebdist_l10 | TRK | 0.02606 |
| RESID_ALL | 2025 | 6 | mu_def_pos_C | MU | 0.02181 |
| RESID_ALL | 2025 | 7 | trk_screenast_pm_ewm | TRK | 0.02168 |
| RESID_ALL | 2025 | 8 | oppx_pts36_allowed_pos_l20 | OPP | 0.02124 |
| RESID_ALL | 2025 | 9 | oppt_al_potast_l20 | OPP | 0.02061 |
| RESID_ALL | 2025 | 10 | oppt_al_ast_conv_l10 | OPP | 0.02049 |
| RESID_ALL | 2025 | 11 | trk_loose_pm_ewm | TRK | 0.01982 |
| RESID_ALL | 2025 | 12 | mu_h2h_ast100 | MU | 0.01927 |
| RESID_ALL | 2025 | 13 | trk_loose_pm_l10 | TRK | 0.01899 |
| RESID_ALL | 2025 | 14 | trk_potast_pm_ewm | TRK | 0.01866 |
| RESID_ALL | 2025 | 15 | mu_off_defby_F | MU | 0.01794 |
| RESID_ALL | 2025 | 16 | exp_potast | TRK | 0.01751 |
| RESID_ALL | 2025 | 17 | trk_rebch_last | TRK | 0.01730 |
| RESID_ALL | 2025 | 18 | oppt_al_rebch_conv_l10 | OPP | 0.01694 |
| RESID_ALL | 2025 | 19 | oppt_contested_l20 | OPP | 0.01690 |
| RESID_ALL | 2025 | 20 | oppt_al_rebch_l10 | OPP | 0.01526 |
| RESID_ALL | 2025 | 21 | trk_ast_conv_l20 | TRK | 0.01517 |
| RESID_ALL | 2025 | 22 | trk_min_ewm | TRK | 0.01482 |
| RESID_ALL | 2025 | 23 | oppt_boxouts_l10 | OPP | 0.01399 |
| RESID_ALL | 2025 | 24 | mu_def_pos_G | MU | 0.01373 |
| RESID_ALL | 2025 | 25 | mu_best_def_vs_pos | MU | 0.01361 |
| RESID_ALL | 2025 | 26 | mu_off_ast100 | MU | 0.01345 |
| RESID_ALL | 2025 | 27 | mu_def_defbox_pm | MU | 0.01339 |
| RESID_ALL | 2025 | 28 | trk_rebch_conv_ewm | TRK | 0.01327 |
| RESID_ALL | 2025 | 29 | mu_def_ast_vs_exp | MU | 0.01320 |
| RESID_ALL | 2025 | 30 | trk_reb_contest_share_l10 | TRK | 0.01320 |
| BASE+ALL | 2026 | 1 | dd_rate_ewm | BASE | 0.41828 |
| BASE+ALL | 2026 | 2 | dd_rate_l20 | BASE | 0.11347 |
| BASE+ALL | 2026 | 3 | dd_rate_szn | BASE | 0.04791 |
| BASE+ALL | 2026 | 4 | prev_dd_rate | BASE | 0.04450 |
| BASE+ALL | 2026 | 5 | reb_ewm | BASE | 0.01985 |
| BASE+ALL | 2026 | 6 | dd_rate_l10 | BASE | 0.01836 |
| BASE+ALL | 2026 | 7 | reb_l10 | BASE | 0.01729 |
| BASE+ALL | 2026 | 8 | trk_rebch_pg_ewm | TRK | 0.01628 |
| BASE+ALL | 2026 | 9 | last_starter | BASE | 0.00722 |
| BASE+ALL | 2026 | 10 | trk_potast_pg_ewm | TRK | 0.00714 |
| BASE+ALL | 2026 | 11 | abs_absent_rebounds_pg | BASE | 0.00661 |
| BASE+ALL | 2026 | 12 | reb_szn | BASE | 0.00608 |
| BASE+ALL | 2026 | 13 | last_min | BASE | 0.00498 |
| BASE+ALL | 2026 | 14 | abs_absent_assists_pg | BASE | 0.00432 |
| BASE+ALL | 2026 | 15 | ast_ewm | BASE | 0.00428 |
| BASE+ALL | 2026 | 16 | abs_absent_points_pg | BASE | 0.00369 |
| BASE+ALL | 2026 | 17 | reb8_rate_szn | BASE | 0.00354 |
| BASE+ALL | 2026 | 18 | oppt_al_rebcon_share_l20 | OPP | 0.00347 |
| BASE+ALL | 2026 | 19 | min_trend | BASE | 0.00338 |
| BASE+ALL | 2026 | 20 | opp_allow_pts_szn | BASE | 0.00334 |
| BASE+ALL | 2026 | 21 | trk_rebch_last | TRK | 0.00324 |
| BASE+ALL | 2026 | 22 | opp_allow_reb_l20 | BASE | 0.00307 |
| BASE+ALL | 2026 | 23 | exp_potast | TRK | 0.00283 |
| BASE+ALL | 2026 | 24 | ast_szn | BASE | 0.00279 |
| BASE+ALL | 2026 | 25 | ast_l10 | BASE | 0.00268 |
| BASE+ALL | 2026 | 26 | trk_passes_pm_l10 | TRK | 0.00262 |
| BASE+ALL | 2026 | 27 | min_l5 | BASE | 0.00260 |
| BASE+ALL | 2026 | 28 | abs_absent_minutes_share | BASE | 0.00259 |
| BASE+ALL | 2026 | 29 | pts_pm_szn | BASE | 0.00258 |
| BASE+ALL | 2026 | 30 | opp_allow_ast_szn | BASE | 0.00249 |
| STACK_ALL | 2026 | 1 | z_ref | REF | 0.63977 |
| STACK_ALL | 2026 | 2 | trk_rebch_pg_ewm | TRK | 0.12912 |
| STACK_ALL | 2026 | 3 | exp_rebch | TRK | 0.04694 |
| STACK_ALL | 2026 | 4 | exp_potast | TRK | 0.02188 |
| STACK_ALL | 2026 | 5 | trk_potast_pg_ewm | TRK | 0.01973 |
| STACK_ALL | 2026 | 6 | min_ewm | BASE | 0.01931 |
| STACK_ALL | 2026 | 7 | trk_rebch_last | TRK | 0.01277 |
| STACK_ALL | 2026 | 8 | trk_min_ewm | TRK | 0.00538 |
| STACK_ALL | 2026 | 9 | mu_off_ast100 | MU | 0.00447 |
| STACK_ALL | 2026 | 10 | trk_rebch_conv_ewm | TRK | 0.00411 |
| STACK_ALL | 2026 | 11 | trk_potast_last | TRK | 0.00388 |
| STACK_ALL | 2026 | 12 | trk_drebch_pm_ewm | TRK | 0.00356 |
| STACK_ALL | 2026 | 13 | mu_off_pts100 | MU | 0.00352 |
| STACK_ALL | 2026 | 14 | trk_drebch_pm_l10 | TRK | 0.00325 |
| STACK_ALL | 2026 | 15 | trk_rebdist_l10 | TRK | 0.00238 |
| STACK_ALL | 2026 | 16 | trk_passes_pm_l10 | TRK | 0.00236 |
| STACK_ALL | 2026 | 17 | oppt_al_rebcon_share_l20 | OPP | 0.00211 |
| STACK_ALL | 2026 | 18 | mu_h2h_pts100 | MU | 0.00202 |
| STACK_ALL | 2026 | 19 | trk_rebch_conv_l20 | TRK | 0.00194 |
| STACK_ALL | 2026 | 20 | oppt_al_potast_l20 | OPP | 0.00190 |
| STACK_ALL | 2026 | 21 | oppx_pts36_allowed_pos_l20 | OPP | 0.00184 |
| STACK_ALL | 2026 | 22 | oppt_deflect_l20 | OPP | 0.00183 |
| STACK_ALL | 2026 | 23 | mu_off_fit | MU | 0.00173 |
| STACK_ALL | 2026 | 24 | trk_ast_conv_l20 | TRK | 0.00170 |
| STACK_ALL | 2026 | 25 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.00167 |
| STACK_ALL | 2026 | 26 | trk_rebch_pm_l10 | TRK | 0.00165 |
| STACK_ALL | 2026 | 27 | oppt_al_ast_conv_l10 | OPP | 0.00163 |
| STACK_ALL | 2026 | 28 | trk_rebch_pm_l20 | TRK | 0.00156 |
| STACK_ALL | 2026 | 29 | mu_off_defby_G | MU | 0.00153 |
| STACK_ALL | 2026 | 30 | oppt_al_passes_l20 | OPP | 0.00141 |
| RESID_ALL | 2026 | 1 | trk_rebch_conv_l20 | TRK | 0.08428 |
| RESID_ALL | 2026 | 2 | oppt_al_rebcon_share_l20 | OPP | 0.04081 |
| RESID_ALL | 2026 | 3 | oppt_al_passes_l20 | OPP | 0.03695 |
| RESID_ALL | 2026 | 4 | trk_rebch_conv_l5 | TRK | 0.03444 |
| RESID_ALL | 2026 | 5 | oppx_pts36_allowed_pos_l20 | OPP | 0.03079 |
| RESID_ALL | 2026 | 6 | trk_astpts_pm_l10 | TRK | 0.02935 |
| RESID_ALL | 2026 | 7 | mu_h2h_pts100 | MU | 0.02452 |
| RESID_ALL | 2026 | 8 | mu_def_pos_C | MU | 0.02370 |
| RESID_ALL | 2026 | 9 | oppt_al_ast_conv_l10 | OPP | 0.02208 |
| RESID_ALL | 2026 | 10 | trk_screenast_pm_ewm | TRK | 0.02130 |
| RESID_ALL | 2026 | 11 | mu_def_ast_vs_exp | MU | 0.02125 |
| RESID_ALL | 2026 | 12 | oppt_al_potast_l20 | OPP | 0.02100 |
| RESID_ALL | 2026 | 13 | trk_ast_conv_l20 | TRK | 0.02038 |
| RESID_ALL | 2026 | 14 | oppt_deflect_l20 | OPP | 0.02025 |
| RESID_ALL | 2026 | 15 | mu_h2h_ast100 | MU | 0.01930 |
| RESID_ALL | 2026 | 16 | mu_off_ast100 | MU | 0.01785 |
| RESID_ALL | 2026 | 17 | oppx_ast_allowed_pos_l10 | OPP | 0.01599 |
| RESID_ALL | 2026 | 18 | oppt_screenast_l20 | OPP | 0.01521 |
| RESID_ALL | 2026 | 19 | oppt_al_rebch_conv_l20 | OPP | 0.01510 |
| RESID_ALL | 2026 | 20 | mu_def_defbox_pm | MU | 0.01501 |
| RESID_ALL | 2026 | 21 | oppx_pts_allowed_pos_l10 | OPP | 0.01476 |
| RESID_ALL | 2026 | 22 | oppt_al_potast_l10 | OPP | 0.01359 |
| RESID_ALL | 2026 | 23 | trk_rebdist_l10 | TRK | 0.01334 |
| RESID_ALL | 2026 | 24 | trk_astpts_pm_ewm | TRK | 0.01261 |
| RESID_ALL | 2026 | 25 | trk_passes_pm_l10 | TRK | 0.01214 |
| RESID_ALL | 2026 | 26 | trk_games_prior | TRK | 0.01172 |
| RESID_ALL | 2026 | 27 | oppt_deflect_l10 | OPP | 0.01152 |
| RESID_ALL | 2026 | 28 | trk_passes_pm_l5 | TRK | 0.01150 |
| RESID_ALL | 2026 | 29 | mu_off_fit | MU | 0.01129 |
| RESID_ALL | 2026 | 30 | mu_off_defby_C | MU | 0.01121 |

## Folds
```
{
  "2025": {
    "n_fit": 21931,
    "n_hold": 3889,
    "n_test": 25723,
    "cut_date": "2024-03-23",
    "BASE_best_iteration": 105,
    "BASE_holdout_logloss": 0.21167410120509128,
    "BASE+TRK_best_iteration": 126,
    "BASE+TRK_holdout_logloss": 0.21002014935833974,
    "BASE+OPP_best_iteration": 117,
    "BASE+OPP_holdout_logloss": 0.211087413230205,
    "BASE+MU_best_iteration": 158,
    "BASE+MU_holdout_logloss": 0.21018077509445174,
    "BASE+ALL_best_iteration": 176,
    "BASE+ALL_holdout_logloss": 0.20939959282014114,
    "STACK_BASE_best_iteration": 544,
    "STACK_BASE_holdout_logloss": 0.2108647093254539,
    "STACK_ALL_best_iteration": 147,
    "STACK_ALL_holdout_logloss": 0.20385348747265952,
    "RESID_NONE_best_iteration": 7,
    "RESID_NONE_holdout_logloss": 0.20318533302391203,
    "RESID_TRK_best_iteration": 90,
    "RESID_TRK_holdout_logloss": 0.20241765555955307,
    "RESID_OPP_best_iteration": 11,
    "RESID_OPP_holdout_logloss": 0.20300775894496234,
    "RESID_MU_best_iteration": 67,
    "RESID_MU_holdout_logloss": 0.2026074345172758,
    "RESID_ALL_best_iteration": 22,
    "RESID_ALL_holdout_logloss": 0.2026338467425516
  },
  "2026": {
    "n_fit": 43767,
    "n_hold": 7776,
    "n_test": 26055,
    "cut_date": "2025-02-25",
    "BASE_best_iteration": 207,
    "BASE_holdout_logloss": 0.2071726278704816,
    "BASE+TRK_best_iteration": 206,
    "BASE+TRK_holdout_logloss": 0.20799047552526945,
    "BASE+OPP_best_iteration": 274,
    "BASE+OPP_holdout_logloss": 0.2071186953523475,
    "BASE+MU_best_iteration": 192,
    "BASE+MU_holdout_logloss": 0.20734695640208486,
    "BASE+ALL_best_iteration": 148,
    "BASE+ALL_holdout_logloss": 0.20921954966545542,
    "STACK_BASE_best_iteration": 768,
    "STACK_BASE_holdout_logloss": 0.20751908512946754,
    "STACK_ALL_best_iteration": 112,
    "STACK_ALL_holdout_logloss": 0.2062058230849884,
    "RESID_NONE_best_iteration": 2,
    "RESID_NONE_holdout_logloss": 0.20659804174081567,
    "RESID_TRK_best_iteration": 5,
    "RESID_TRK_holdout_logloss": 0.20652986212248534,
    "RESID_OPP_best_iteration": 4,
    "RESID_OPP_holdout_logloss": 0.2065552213497972,
    "RESID_MU_best_iteration": 2,
    "RESID_MU_holdout_logloss": 0.20664834615958338,
    "RESID_ALL_best_iteration": 17,
    "RESID_ALL_holdout_logloss": 0.20646006581082105
  }
}
```
