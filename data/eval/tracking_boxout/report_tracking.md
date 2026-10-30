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
| 2025 | BASE+TRK | 25723 | 0.0872 | 0.1973 | 0.0572 | 0.8940 |
| 2025 | BASE+OPP | 25723 | 0.0872 | 0.1983 | 0.0571 | 0.8921 |
| 2025 | BASE+MU | 25723 | 0.0872 | 0.1971 | 0.0571 | 0.8935 |
| 2025 | BASE+ALL | 25723 | 0.0872 | 0.1979 | 0.0571 | 0.8930 |
| 2025 | STACK_BASE | 25723 | 0.0872 | 0.1994 | 0.0579 | 0.8897 |
| 2025 | STACK_ALL | 25723 | 0.0872 | 0.1951 | 0.0568 | 0.8963 |
| 2025 | RESID_NONE | 25723 | 0.0872 | 0.1940 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK | 25723 | 0.0872 | 0.1938 | 0.0564 | 0.8983 |
| 2025 | RESID_OPP | 25723 | 0.0872 | 0.1941 | 0.0565 | 0.8984 |
| 2025 | RESID_MU | 25723 | 0.0872 | 0.1947 | 0.0568 | 0.8973 |
| 2025 | RESID_ALL | 25723 | 0.0872 | 0.1941 | 0.0565 | 0.8987 |
| 2025 | RESID_NONE raw | 25723 | 0.0872 | 0.1935 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK raw | 25723 | 0.0872 | 0.1934 | 0.0564 | 0.8983 |
| 2025 | RESID_OPP raw | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | RESID_MU raw | 25723 | 0.0872 | 0.1943 | 0.0568 | 0.8973 |
| 2025 | RESID_ALL raw | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8987 |
| 2025 | BLEND_REF_ALL | 25723 | 0.0872 | 0.1933 | 0.0564 | 0.8981 |
| 2026 | A | 26055 | 0.0733 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | REF | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.1838 | 0.0524 | 0.8810 |
| 2026 | BASE+TRK | 26055 | 0.0733 | 0.1840 | 0.0523 | 0.8805 |
| 2026 | BASE+OPP | 26055 | 0.0733 | 0.1840 | 0.0525 | 0.8806 |
| 2026 | BASE+MU | 26055 | 0.0733 | 0.1840 | 0.0524 | 0.8806 |
| 2026 | BASE+ALL | 26055 | 0.0733 | 0.1843 | 0.0524 | 0.8793 |
| 2026 | STACK_BASE | 26055 | 0.0733 | 0.1841 | 0.0525 | 0.8800 |
| 2026 | STACK_ALL | 26055 | 0.0733 | 0.1815 | 0.0518 | 0.8850 |
| 2026 | RESID_NONE | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK | 26055 | 0.0733 | 0.1805 | 0.0517 | 0.8865 |
| 2026 | RESID_OPP | 26055 | 0.0733 | 0.1808 | 0.0517 | 0.8862 |
| 2026 | RESID_MU | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL | 26055 | 0.0733 | 0.1808 | 0.0517 | 0.8864 |
| 2026 | RESID_NONE raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK raw | 26055 | 0.0733 | 0.1805 | 0.0517 | 0.8865 |
| 2026 | RESID_OPP raw | 26055 | 0.0733 | 0.1807 | 0.0518 | 0.8862 |
| 2026 | RESID_MU raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL raw | 26055 | 0.0733 | 0.1806 | 0.0517 | 0.8864 |
| 2026 | BLEND_REF_ALL | 26055 | 0.0733 | 0.1811 | 0.0518 | 0.8852 |
| all | A | 51778 | 0.0802 | 0.1989 | 0.0557 | 0.8643 |
| all | REF | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | BASE | 51778 | 0.0802 | 0.1906 | 0.0546 | 0.8871 |
| all | BASE+TRK | 51778 | 0.0802 | 0.1906 | 0.0547 | 0.8874 |
| all | BASE+OPP | 51778 | 0.0802 | 0.1911 | 0.0548 | 0.8862 |
| all | BASE+MU | 51778 | 0.0802 | 0.1905 | 0.0547 | 0.8874 |
| all | BASE+ALL | 51778 | 0.0802 | 0.1910 | 0.0548 | 0.8859 |
| all | STACK_BASE | 51778 | 0.0802 | 0.1917 | 0.0552 | 0.8850 |
| all | STACK_ALL | 51778 | 0.0802 | 0.1883 | 0.0543 | 0.8912 |
| all | RESID_NONE | 51778 | 0.0802 | 0.1874 | 0.0541 | 0.8927 |
| all | RESID_TRK | 51778 | 0.0802 | 0.1872 | 0.0540 | 0.8928 |
| all | RESID_OPP | 51778 | 0.0802 | 0.1875 | 0.0541 | 0.8927 |
| all | RESID_MU | 51778 | 0.0802 | 0.1878 | 0.0542 | 0.8920 |
| all | RESID_ALL | 51778 | 0.0802 | 0.1874 | 0.0541 | 0.8928 |
| all | RESID_NONE raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | RESID_TRK raw | 51778 | 0.0802 | 0.1869 | 0.0541 | 0.8929 |
| all | RESID_OPP raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8927 |
| all | RESID_MU raw | 51778 | 0.0802 | 0.1875 | 0.0543 | 0.8920 |
| all | RESID_ALL raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8927 |
| all | BLEND_REF_ALL | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8922 |

## Bootstrap of log-loss differences (block bootstrap by game date, 1000 resamples; negative favors the model)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2025 | p_BASE+TRK_cal | p_BASE_cal | -0.00023 | -0.00091 | 0.00049 | 0.72400 |
| 2025 | p_BASE+OPP_cal | p_BASE_cal | 0.00078 | 0.00014 | 0.00152 | 0.00600 |
| 2025 | p_BASE+MU_cal | p_BASE_cal | -0.00039 | -0.00103 | 0.00025 | 0.89200 |
| 2025 | p_BASE+ALL_cal | p_BASE_cal | 0.00037 | -0.00039 | 0.00119 | 0.14500 |
| 2025 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00425 | -0.00575 | -0.00271 | 1.00000 |
| 2025 | p_STACK_ALL_cal | p_REF_cal | 0.00153 | 0.00004 | 0.00285 | 0.02000 |
| 2025 | p_STACK_BASE_cal | p_REF_cal | 0.00578 | 0.00416 | 0.00751 | 0.00000 |
| 2025 | p_BASE+ALL_cal | p_REF_cal | 0.00427 | 0.00238 | 0.00616 | 0.00000 |
| 2025 | p_RESID_NONE_cal | p_REF_cal | 0.00043 | -0.00012 | 0.00096 | 0.06300 |
| 2025 | p_RESID_TRK_cal | p_REF_cal | 0.00024 | -0.00044 | 0.00088 | 0.24100 |
| 2025 | p_RESID_OPP_cal | p_REF_cal | 0.00054 | -0.00004 | 0.00112 | 0.03600 |
| 2025 | p_RESID_MU_cal | p_REF_cal | 0.00108 | 0.00034 | 0.00182 | 0.00200 |
| 2025 | p_RESID_ALL_cal | p_REF_cal | 0.00053 | -0.00001 | 0.00106 | 0.03200 |
| 2025 | p_RESID_NONE_raw | p_REF_cal | -0.00008 | -0.00017 | 0.00002 | 0.93700 |
| 2025 | p_RESID_TRK_raw | p_REF_cal | -0.00023 | -0.00062 | 0.00013 | 0.87800 |
| 2025 | p_RESID_OPP_raw | p_REF_cal | -0.00000 | -0.00018 | 0.00018 | 0.49800 |
| 2025 | p_RESID_MU_raw | p_REF_cal | 0.00071 | 0.00025 | 0.00116 | 0.00000 |
| 2025 | p_RESID_ALL_raw | p_REF_cal | -0.00003 | -0.00006 | 0.00001 | 0.92000 |
| 2025 | p_BLEND_cal | p_REF_cal | -0.00032 | -0.00124 | 0.00062 | 0.72100 |
| 2025 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00015 | -0.00054 | 0.00022 | 0.77500 |
| 2025 | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00008 | -0.00013 | 0.00029 | 0.25900 |
| 2025 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00079 | 0.00035 | 0.00125 | 0.00000 |
| 2025 | p_RESID_ALL_raw | p_RESID_NONE_raw | 0.00005 | -0.00005 | 0.00015 | 0.15100 |
| 2026 | p_BASE+TRK_cal | p_BASE_cal | 0.00011 | -0.00067 | 0.00089 | 0.39900 |
| 2026 | p_BASE+OPP_cal | p_BASE_cal | 0.00013 | -0.00050 | 0.00078 | 0.39000 |
| 2026 | p_BASE+MU_cal | p_BASE_cal | 0.00016 | -0.00034 | 0.00062 | 0.28900 |
| 2026 | p_BASE+ALL_cal | p_BASE_cal | 0.00045 | -0.00036 | 0.00127 | 0.14700 |
| 2026 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00258 | -0.00365 | -0.00151 | 1.00000 |
| 2026 | p_STACK_ALL_cal | p_REF_cal | 0.00076 | -0.00021 | 0.00186 | 0.07300 |
| 2026 | p_STACK_BASE_cal | p_REF_cal | 0.00334 | 0.00223 | 0.00440 | 0.00000 |
| 2026 | p_BASE+ALL_cal | p_REF_cal | 0.00353 | 0.00212 | 0.00508 | 0.00000 |
| 2026 | p_RESID_NONE_cal | p_REF_cal | 0.00016 | -0.00011 | 0.00039 | 0.11400 |
| 2026 | p_RESID_TRK_cal | p_REF_cal | -0.00020 | -0.00052 | 0.00009 | 0.90400 |
| 2026 | p_RESID_OPP_cal | p_REF_cal | 0.00009 | -0.00018 | 0.00033 | 0.24000 |
| 2026 | p_RESID_MU_cal | p_REF_cal | 0.00017 | -0.00011 | 0.00040 | 0.11600 |
| 2026 | p_RESID_ALL_cal | p_REF_cal | 0.00001 | -0.00026 | 0.00023 | 0.49300 |
| 2026 | p_RESID_NONE_raw | p_REF_cal | 0.00000 | -0.00002 | 0.00003 | 0.47200 |
| 2026 | p_RESID_TRK_raw | p_REF_cal | -0.00027 | -0.00047 | -0.00006 | 0.99300 |
| 2026 | p_RESID_OPP_raw | p_REF_cal | -0.00006 | -0.00012 | 0.00001 | 0.96000 |
| 2026 | p_RESID_MU_raw | p_REF_cal | 0.00001 | -0.00002 | 0.00004 | 0.21200 |
| 2026 | p_RESID_ALL_raw | p_REF_cal | -0.00012 | -0.00019 | -0.00005 | 1.00000 |
| 2026 | p_BLEND_cal | p_REF_cal | 0.00033 | -0.00037 | 0.00104 | 0.16500 |
| 2026 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00027 | -0.00047 | -0.00006 | 0.99600 |
| 2026 | p_RESID_OPP_raw | p_RESID_NONE_raw | -0.00006 | -0.00013 | 0.00001 | 0.95400 |
| 2026 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00001 | -0.00003 | 0.00005 | 0.25800 |
| 2026 | p_RESID_ALL_raw | p_RESID_NONE_raw | -0.00012 | -0.00019 | -0.00005 | 1.00000 |
| all | p_BASE+TRK_cal | p_BASE_cal | -0.00006 | -0.00059 | 0.00049 | 0.55800 |
| all | p_BASE+OPP_cal | p_BASE_cal | 0.00045 | -0.00003 | 0.00095 | 0.03300 |
| all | p_BASE+MU_cal | p_BASE_cal | -0.00011 | -0.00050 | 0.00026 | 0.68800 |
| all | p_BASE+ALL_cal | p_BASE_cal | 0.00041 | -0.00012 | 0.00101 | 0.06600 |
| all | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00341 | -0.00438 | -0.00245 | 1.00000 |
| all | p_STACK_ALL_cal | p_REF_cal | 0.00114 | 0.00026 | 0.00198 | 0.00900 |
| all | p_STACK_BASE_cal | p_REF_cal | 0.00455 | 0.00349 | 0.00551 | 0.00000 |
| all | p_BASE+ALL_cal | p_REF_cal | 0.00390 | 0.00274 | 0.00505 | 0.00000 |
| all | p_RESID_NONE_cal | p_REF_cal | 0.00029 | -0.00001 | 0.00061 | 0.03000 |
| all | p_RESID_TRK_cal | p_REF_cal | 0.00002 | -0.00034 | 0.00037 | 0.47000 |
| all | p_RESID_OPP_cal | p_REF_cal | 0.00032 | -0.00001 | 0.00068 | 0.02800 |
| all | p_RESID_MU_cal | p_REF_cal | 0.00062 | 0.00024 | 0.00102 | 0.00000 |
| all | p_RESID_ALL_cal | p_REF_cal | 0.00027 | -0.00004 | 0.00059 | 0.04900 |
| all | p_RESID_NONE_raw | p_REF_cal | -0.00004 | -0.00008 | 0.00001 | 0.95400 |
| all | p_RESID_TRK_raw | p_REF_cal | -0.00025 | -0.00045 | -0.00004 | 0.99200 |
| all | p_RESID_OPP_raw | p_REF_cal | -0.00003 | -0.00013 | 0.00007 | 0.68200 |
| all | p_RESID_MU_raw | p_REF_cal | 0.00036 | 0.00015 | 0.00060 | 0.00000 |
| all | p_RESID_ALL_raw | p_REF_cal | -0.00007 | -0.00011 | -0.00003 | 1.00000 |
| all | p_BLEND_cal | p_REF_cal | 0.00001 | -0.00055 | 0.00057 | 0.50100 |
| all | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00021 | -0.00041 | 0.00001 | 0.96400 |
| all | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00001 | -0.00010 | 0.00013 | 0.40000 |
| all | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00040 | 0.00019 | 0.00063 | 0.00000 |
| all | p_RESID_ALL_raw | p_RESID_NONE_raw | -0.00003 | -0.00009 | 0.00003 | 0.85500 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | logloss | brier | auc |
|---|---|---|---|---|---|---|
| 2025 | A | 2129 | 0.4298 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | REF | 2129 | 0.4298 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.6604 | 0.2339 | 0.6328 |
| 2025 | BASE+TRK | 2129 | 0.4298 | 0.6633 | 0.2353 | 0.6252 |
| 2025 | BASE+OPP | 2129 | 0.4298 | 0.6622 | 0.2349 | 0.6266 |
| 2025 | BASE+MU | 2129 | 0.4298 | 0.6642 | 0.2354 | 0.6266 |
| 2025 | BASE+ALL | 2129 | 0.4298 | 0.6617 | 0.2346 | 0.6282 |
| 2025 | STACK_BASE | 2129 | 0.4298 | 0.6815 | 0.2424 | 0.6151 |
| 2025 | STACK_ALL | 2129 | 0.4298 | 0.6658 | 0.2364 | 0.6251 |
| 2025 | RESID_NONE | 2129 | 0.4298 | 0.6615 | 0.2346 | 0.6276 |
| 2025 | RESID_TRK | 2129 | 0.4298 | 0.6596 | 0.2337 | 0.6311 |
| 2025 | RESID_OPP | 2129 | 0.4298 | 0.6621 | 0.2349 | 0.6249 |
| 2025 | RESID_MU | 2129 | 0.4298 | 0.6652 | 0.2362 | 0.6181 |
| 2025 | RESID_ALL | 2129 | 0.4298 | 0.6619 | 0.2348 | 0.6258 |
| 2025 | RESID_NONE raw | 2129 | 0.4298 | 0.6633 | 0.2353 | 0.6276 |
| 2025 | RESID_TRK raw | 2129 | 0.4298 | 0.6623 | 0.2348 | 0.6311 |
| 2025 | RESID_OPP raw | 2129 | 0.4298 | 0.6642 | 0.2358 | 0.6249 |
| 2025 | RESID_MU raw | 2129 | 0.4298 | 0.6672 | 0.2370 | 0.6181 |
| 2025 | RESID_ALL raw | 2129 | 0.4298 | 0.6638 | 0.2356 | 0.6258 |
| 2025 | BLEND_REF_ALL | 2129 | 0.4298 | 0.6576 | 0.2328 | 0.6345 |
| 2026 | A | 1976 | 0.3806 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | REF | 1976 | 0.3806 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.6311 | 0.2204 | 0.6558 |
| 2026 | BASE+TRK | 1976 | 0.3806 | 0.6285 | 0.2192 | 0.6587 |
| 2026 | BASE+OPP | 1976 | 0.3806 | 0.6316 | 0.2207 | 0.6540 |
| 2026 | BASE+MU | 1976 | 0.3806 | 0.6309 | 0.2203 | 0.6548 |
| 2026 | BASE+ALL | 1976 | 0.3806 | 0.6304 | 0.2200 | 0.6573 |
| 2026 | STACK_BASE | 1976 | 0.3806 | 0.6326 | 0.2210 | 0.6497 |
| 2026 | STACK_ALL | 1976 | 0.3806 | 0.6254 | 0.2176 | 0.6644 |
| 2026 | RESID_NONE | 1976 | 0.3806 | 0.6264 | 0.2181 | 0.6620 |
| 2026 | RESID_TRK | 1976 | 0.3806 | 0.6253 | 0.2176 | 0.6634 |
| 2026 | RESID_OPP | 1976 | 0.3806 | 0.6262 | 0.2180 | 0.6633 |
| 2026 | RESID_MU | 1976 | 0.3806 | 0.6263 | 0.2181 | 0.6623 |
| 2026 | RESID_ALL | 1976 | 0.3806 | 0.6260 | 0.2179 | 0.6628 |
| 2026 | RESID_NONE raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6620 |
| 2026 | RESID_TRK raw | 1976 | 0.3806 | 0.6262 | 0.2180 | 0.6634 |
| 2026 | RESID_OPP raw | 1976 | 0.3806 | 0.6273 | 0.2185 | 0.6633 |
| 2026 | RESID_MU raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6623 |
| 2026 | RESID_ALL raw | 1976 | 0.3806 | 0.6270 | 0.2184 | 0.6628 |
| 2026 | BLEND_REF_ALL | 1976 | 0.3806 | 0.6246 | 0.2175 | 0.6652 |
| all | A | 4105 | 0.4061 | 0.6557 | 0.2318 | 0.6196 |
| all | REF | 4105 | 0.4061 | 0.6463 | 0.2274 | 0.6442 |
| all | BASE | 4105 | 0.4061 | 0.6462 | 0.2274 | 0.6456 |
| all | BASE+TRK | 4105 | 0.4061 | 0.6466 | 0.2276 | 0.6438 |
| all | BASE+OPP | 4105 | 0.4061 | 0.6475 | 0.2281 | 0.6420 |
| all | BASE+MU | 4105 | 0.4061 | 0.6482 | 0.2281 | 0.6415 |
| all | BASE+ALL | 4105 | 0.4061 | 0.6467 | 0.2276 | 0.6444 |
| all | STACK_BASE | 4105 | 0.4061 | 0.6580 | 0.2321 | 0.6279 |
| all | STACK_ALL | 4105 | 0.4061 | 0.6464 | 0.2274 | 0.6460 |
| all | RESID_NONE | 4105 | 0.4061 | 0.6446 | 0.2267 | 0.6451 |
| all | RESID_TRK | 4105 | 0.4061 | 0.6431 | 0.2260 | 0.6487 |
| all | RESID_OPP | 4105 | 0.4061 | 0.6448 | 0.2268 | 0.6445 |
| all | RESID_MU | 4105 | 0.4061 | 0.6465 | 0.2275 | 0.6402 |
| all | RESID_ALL | 4105 | 0.4061 | 0.6446 | 0.2267 | 0.6447 |
| all | RESID_NONE raw | 4105 | 0.4061 | 0.6461 | 0.2273 | 0.6451 |
| all | RESID_TRK raw | 4105 | 0.4061 | 0.6449 | 0.2267 | 0.6486 |
| all | RESID_OPP raw | 4105 | 0.4061 | 0.6464 | 0.2274 | 0.6446 |
| all | RESID_MU raw | 4105 | 0.4061 | 0.6481 | 0.2282 | 0.6405 |
| all | RESID_ALL raw | 4105 | 0.4061 | 0.6461 | 0.2273 | 0.6449 |
| all | BLEND_REF_ALL | 4105 | 0.4061 | 0.6417 | 0.2254 | 0.6520 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 | distinct_players |
|---|---|---|---|---|---|---|---|
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 | 31 |
| 2025 | REF | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 | 33 |
| 2025 | BASE | 164 | 0.7805 | 0.6829 | 0.3841 | 0.7065 | 35 |
| 2025 | BASE+TRK | 164 | 0.7988 | 0.6890 | 0.3476 | 0.7081 | 32 |
| 2025 | BASE+OPP | 164 | 0.7927 | 0.6829 | 0.3598 | 0.7000 | 34 |
| 2025 | BASE+MU | 164 | 0.8049 | 0.6911 | 0.3780 | 0.6922 | 32 |
| 2025 | BASE+ALL | 164 | 0.7988 | 0.6829 | 0.3293 | 0.6990 | 35 |
| 2025 | STACK_BASE | 164 | 0.7622 | 0.6626 | 0.3110 | 0.6552 | 35 |
| 2025 | STACK_ALL | 164 | 0.7927 | 0.6931 | 0.3537 | 0.7103 | 36 |
| 2025 | RESID_NONE | 164 | 0.8171 | 0.7012 | 0.3537 | 0.6950 | 35 |
| 2025 | RESID_TRK | 164 | 0.7927 | 0.7093 | 0.3598 | 0.7058 | 34 |
| 2025 | RESID_OPP | 164 | 0.8415 | 0.6992 | 0.3720 | 0.6984 | 35 |
| 2025 | RESID_MU | 164 | 0.7988 | 0.6931 | 0.3354 | 0.6875 | 32 |
| 2025 | RESID_ALL | 164 | 0.8110 | 0.7093 | 0.3720 | 0.6971 | 33 |
| 2025 | RESID_NONE raw | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7390 | 35 |
| 2025 | RESID_TRK raw | 164 | 0.7927 | 0.7093 | 0.3598 | 0.7533 | 34 |
| 2025 | RESID_OPP raw | 164 | 0.8415 | 0.6992 | 0.3720 | 0.7441 | 35 |
| 2025 | RESID_MU raw | 164 | 0.7988 | 0.6931 | 0.3354 | 0.7410 | 32 |
| 2025 | RESID_ALL raw | 164 | 0.8110 | 0.7093 | 0.3720 | 0.7398 | 33 |
| 2025 | BLEND_REF_ALL | 164 | 0.8293 | 0.7012 | 0.3659 | 0.7183 | 32 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 | 31 |
| 2026 | REF | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 | 35 |
| 2026 | BASE | 165 | 0.6848 | 0.6081 | 0.2182 | 0.6598 | 36 |
| 2026 | BASE+TRK | 165 | 0.6606 | 0.6101 | 0.2182 | 0.6270 | 35 |
| 2026 | BASE+OPP | 165 | 0.6909 | 0.6000 | 0.2121 | 0.6207 | 37 |
| 2026 | BASE+MU | 165 | 0.6727 | 0.6061 | 0.2121 | 0.6449 | 36 |
| 2026 | BASE+ALL | 165 | 0.6788 | 0.6040 | 0.2364 | 0.6067 | 33 |
| 2026 | STACK_BASE | 165 | 0.6909 | 0.5939 | 0.1697 | 0.6487 | 37 |
| 2026 | STACK_ALL | 165 | 0.6848 | 0.6162 | 0.2121 | 0.6138 | 40 |
| 2026 | RESID_NONE | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6397 | 35 |
| 2026 | RESID_TRK | 165 | 0.6848 | 0.6081 | 0.2182 | 0.6267 | 34 |
| 2026 | RESID_OPP | 165 | 0.6848 | 0.6121 | 0.2121 | 0.6380 | 35 |
| 2026 | RESID_MU | 165 | 0.6788 | 0.6121 | 0.2242 | 0.6394 | 37 |
| 2026 | RESID_ALL | 165 | 0.6788 | 0.6141 | 0.2242 | 0.6366 | 35 |
| 2026 | RESID_NONE raw | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6642 | 35 |
| 2026 | RESID_TRK raw | 165 | 0.6848 | 0.6081 | 0.2182 | 0.6585 | 34 |
| 2026 | RESID_OPP raw | 165 | 0.6848 | 0.6121 | 0.2121 | 0.6625 | 35 |
| 2026 | RESID_MU raw | 165 | 0.6788 | 0.6121 | 0.2242 | 0.6644 | 37 |
| 2026 | RESID_ALL raw | 165 | 0.6788 | 0.6141 | 0.2242 | 0.6614 | 35 |
| 2026 | BLEND_REF_ALL | 165 | 0.6848 | 0.6081 | 0.2242 | 0.6347 | 34 |
| all | A | 329 | 0.7356 | 0.6606 | 0.3040 | 0.6895 | 41 |
| all | REF | 329 | 0.7477 | 0.6484 | 0.2766 | 0.7013 | 46 |
| all | BASE | 329 | 0.7325 | 0.6454 | 0.3009 | 0.6831 | 47 |
| all | BASE+TRK | 329 | 0.7295 | 0.6494 | 0.2827 | 0.6675 | 44 |
| all | BASE+OPP | 329 | 0.7416 | 0.6413 | 0.2857 | 0.6602 | 45 |
| all | BASE+MU | 329 | 0.7386 | 0.6484 | 0.2948 | 0.6685 | 44 |
| all | BASE+ALL | 329 | 0.7386 | 0.6434 | 0.2827 | 0.6527 | 46 |
| all | STACK_BASE | 329 | 0.7264 | 0.6282 | 0.2401 | 0.6519 | 48 |
| all | STACK_ALL | 329 | 0.7386 | 0.6545 | 0.2827 | 0.6619 | 51 |
| all | RESID_NONE | 329 | 0.7508 | 0.6535 | 0.2796 | 0.6673 | 47 |
| all | RESID_TRK | 329 | 0.7386 | 0.6586 | 0.2888 | 0.6661 | 46 |
| all | RESID_OPP | 329 | 0.7629 | 0.6555 | 0.2918 | 0.6681 | 47 |
| all | RESID_MU | 329 | 0.7386 | 0.6525 | 0.2796 | 0.6634 | 46 |
| all | RESID_ALL | 329 | 0.7447 | 0.6616 | 0.2979 | 0.6667 | 46 |
| all | RESID_NONE raw | 329 | 0.7508 | 0.6535 | 0.2796 | 0.7015 | 47 |
| all | RESID_TRK raw | 329 | 0.7386 | 0.6586 | 0.2888 | 0.7058 | 46 |
| all | RESID_OPP raw | 329 | 0.7629 | 0.6555 | 0.2918 | 0.7032 | 47 |
| all | RESID_MU raw | 329 | 0.7386 | 0.6525 | 0.2796 | 0.7026 | 46 |
| all | RESID_ALL raw | 329 | 0.7447 | 0.6616 | 0.2979 | 0.7005 | 46 |
| all | BLEND_REF_ALL | 329 | 0.7568 | 0.6545 | 0.2948 | 0.6763 | 45 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | REF | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4216 | 0.3686 | 0.4614 | 0.0928 | 0.1783 |
| 2025 | BASE+TRK | 491 | 0.4134 | 0.3501 | 0.4541 | 0.1040 | 0.2089 |
| 2025 | BASE+OPP | 491 | 0.3931 | 0.3494 | 0.4510 | 0.1016 | 0.1396 |
| 2025 | BASE+MU | 491 | 0.3992 | 0.3551 | 0.4388 | 0.0837 | 0.1362 |
| 2025 | BASE+ALL | 491 | 0.4134 | 0.3492 | 0.4549 | 0.1057 | 0.2038 |
| 2025 | STACK_BASE | 491 | 0.4277 | 0.4044 | 0.4500 | 0.0457 | 0.0804 |
| 2025 | STACK_ALL | 491 | 0.4175 | 0.3667 | 0.4870 | 0.1203 | 0.2172 |
| 2025 | RESID_NONE | 491 | 0.4094 | 0.3715 | 0.4415 | 0.0700 | 0.1835 |
| 2025 | RESID_TRK | 491 | 0.3971 | 0.3654 | 0.4459 | 0.0805 | 0.1333 |
| 2025 | RESID_OPP | 491 | 0.4175 | 0.3654 | 0.4404 | 0.0750 | 0.2066 |
| 2025 | RESID_MU | 491 | 0.4053 | 0.3713 | 0.4398 | 0.0684 | 0.1627 |
| 2025 | RESID_ALL | 491 | 0.4134 | 0.3701 | 0.4437 | 0.0736 | 0.1901 |
| 2025 | RESID_NONE raw | 491 | 0.4297 | 0.4055 | 0.5004 | 0.0950 | 0.1191 |
| 2025 | RESID_TRK raw | 491 | 0.4338 | 0.4011 | 0.5117 | 0.1106 | 0.1342 |
| 2025 | RESID_OPP raw | 491 | 0.4358 | 0.3994 | 0.5027 | 0.1033 | 0.1543 |
| 2025 | RESID_MU raw | 491 | 0.4379 | 0.4027 | 0.5041 | 0.1015 | 0.1531 |
| 2025 | RESID_ALL raw | 491 | 0.4297 | 0.4013 | 0.4989 | 0.0977 | 0.1420 |
| 2025 | BLEND_REF_ALL | 491 | 0.4114 | 0.3637 | 0.4470 | 0.0833 | 0.1695 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | REF | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4263 | 0.3732 | 0.4518 | 0.0786 | 0.1891 |
| 2026 | BASE+TRK | 495 | 0.3798 | 0.3499 | 0.4080 | 0.0581 | 0.1283 |
| 2026 | BASE+OPP | 495 | 0.3980 | 0.3622 | 0.4155 | 0.0533 | 0.1286 |
| 2026 | BASE+MU | 495 | 0.3919 | 0.3580 | 0.4338 | 0.0758 | 0.1320 |
| 2026 | BASE+ALL | 495 | 0.3576 | 0.3331 | 0.3829 | 0.0498 | 0.0935 |
| 2026 | STACK_BASE | 495 | 0.4000 | 0.3710 | 0.4801 | 0.1090 | 0.1484 |
| 2026 | STACK_ALL | 495 | 0.4141 | 0.3437 | 0.4150 | 0.0713 | 0.2481 |
| 2026 | RESID_NONE | 495 | 0.4263 | 0.3638 | 0.4389 | 0.0752 | 0.2441 |
| 2026 | RESID_TRK | 495 | 0.4323 | 0.3590 | 0.4232 | 0.0642 | 0.2876 |
| 2026 | RESID_OPP | 495 | 0.4283 | 0.3609 | 0.4348 | 0.0739 | 0.2583 |
| 2026 | RESID_MU | 495 | 0.4263 | 0.3613 | 0.4370 | 0.0757 | 0.2488 |
| 2026 | RESID_ALL | 495 | 0.4242 | 0.3605 | 0.4330 | 0.0725 | 0.2442 |
| 2026 | RESID_NONE raw | 495 | 0.4424 | 0.3878 | 0.4777 | 0.0899 | 0.1996 |
| 2026 | RESID_TRK raw | 495 | 0.4505 | 0.3874 | 0.4730 | 0.0856 | 0.2374 |
| 2026 | RESID_OPP raw | 495 | 0.4424 | 0.3855 | 0.4742 | 0.0887 | 0.2259 |
| 2026 | RESID_MU raw | 495 | 0.4384 | 0.3858 | 0.4767 | 0.0909 | 0.1953 |
| 2026 | RESID_ALL raw | 495 | 0.4444 | 0.3883 | 0.4760 | 0.0878 | 0.2067 |
| 2026 | BLEND_REF_ALL | 495 | 0.4202 | 0.3590 | 0.4191 | 0.0601 | 0.2058 |
| all | A | 986 | 0.2049 | 0.2248 | 0.2081 | -0.0167 | -0.0864 |
| all | REF | 986 | 0.4371 | 0.3958 | 0.4888 | 0.0930 | 0.1662 |
| all | BASE | 986 | 0.4239 | 0.3709 | 0.4566 | 0.0856 | 0.1837 |
| all | BASE+TRK | 986 | 0.3966 | 0.3500 | 0.4309 | 0.0809 | 0.1685 |
| all | BASE+OPP | 986 | 0.3955 | 0.3558 | 0.4332 | 0.0774 | 0.1341 |
| all | BASE+MU | 986 | 0.3955 | 0.3566 | 0.4363 | 0.0797 | 0.1341 |
| all | BASE+ALL | 986 | 0.3854 | 0.3411 | 0.4188 | 0.0776 | 0.1484 |
| all | STACK_BASE | 986 | 0.4138 | 0.3876 | 0.4651 | 0.0775 | 0.1146 |
| all | STACK_ALL | 986 | 0.4158 | 0.3552 | 0.4509 | 0.0957 | 0.2327 |
| all | RESID_NONE | 986 | 0.4178 | 0.3676 | 0.4402 | 0.0726 | 0.2139 |
| all | RESID_TRK | 986 | 0.4148 | 0.3622 | 0.4345 | 0.0723 | 0.2108 |
| all | RESID_OPP | 986 | 0.4229 | 0.3631 | 0.4376 | 0.0745 | 0.2326 |
| all | RESID_MU | 986 | 0.4158 | 0.3663 | 0.4384 | 0.0721 | 0.2059 |
| all | RESID_ALL | 986 | 0.4189 | 0.3653 | 0.4383 | 0.0731 | 0.2173 |
| all | RESID_NONE raw | 986 | 0.4361 | 0.3966 | 0.4890 | 0.0924 | 0.1595 |
| all | RESID_TRK raw | 986 | 0.4422 | 0.3942 | 0.4923 | 0.0980 | 0.1860 |
| all | RESID_OPP raw | 986 | 0.4391 | 0.3925 | 0.4884 | 0.0960 | 0.1902 |
| all | RESID_MU raw | 986 | 0.4381 | 0.3942 | 0.4904 | 0.0962 | 0.1743 |
| all | RESID_ALL raw | 986 | 0.4371 | 0.3948 | 0.4874 | 0.0927 | 0.1745 |
| all | BLEND_REF_ALL | 986 | 0.4158 | 0.3613 | 0.4330 | 0.0717 | 0.1877 |

## Disagreement buckets (model minus comparison, calibrated)
| model | vs | bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|---|---|
| p_BASE+ALL_cal | p_BASE_cal | < -0.05 | 2136 | 0.3901 | 0.3099 | 0.3497 |
| p_BASE+ALL_cal | p_BASE_cal | [-0.05, 0.05] | 48243 | 0.0691 | 0.0684 | 0.0631 |
| p_BASE+ALL_cal | p_BASE_cal | > 0.05 | 1399 | 0.2324 | 0.3064 | 0.2580 |
| p_RESID_ALL_raw | p_REF_cal | < -0.05 | 0 |  |  |  |
| p_RESID_ALL_raw | p_REF_cal | [-0.05, 0.05] | 51778 | 0.0829 | 0.0826 | 0.0802 |
| p_RESID_ALL_raw | p_REF_cal | > 0.05 | 0 |  |  |  |
| p_STACK_ALL_cal | p_REF_cal | < -0.05 | 2171 | 0.4091 | 0.3280 | 0.3676 |
| p_STACK_ALL_cal | p_REF_cal | [-0.05, 0.05] | 47719 | 0.0606 | 0.0633 | 0.0580 |
| p_STACK_ALL_cal | p_REF_cal | > 0.05 | 1888 | 0.2713 | 0.3496 | 0.3125 |
| p_BASE+TRK_cal | p_BASE_cal | < -0.05 | 1811 | 0.3772 | 0.3026 | 0.3374 |
| p_BASE+TRK_cal | p_BASE_cal | [-0.05, 0.05] | 48552 | 0.0712 | 0.0706 | 0.0651 |
| p_BASE+TRK_cal | p_BASE_cal | > 0.05 | 1415 | 0.2487 | 0.3237 | 0.2686 |
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
| BASE+TRK | 2025 | BASE | 0.8494 | 155 |
| BASE+TRK | 2025 | TRK | 0.1506 | 67 |
| BASE+OPP | 2025 | BASE | 0.9196 | 155 |
| BASE+OPP | 2025 | OPP | 0.0804 | 35 |
| BASE+MU | 2025 | BASE | 0.9355 | 155 |
| BASE+MU | 2025 | MU | 0.0645 | 21 |
| BASE+ALL | 2025 | BASE | 0.7911 | 155 |
| BASE+ALL | 2025 | MU | 0.0330 | 21 |
| BASE+ALL | 2025 | OPP | 0.0637 | 35 |
| BASE+ALL | 2025 | TRK | 0.1122 | 67 |
| STACK_BASE | 2025 | BASE | 0.6699 | 2 |
| STACK_BASE | 2025 | REF | 0.3301 | 1 |
| STACK_ALL | 2025 | BASE | 0.0097 | 2 |
| STACK_ALL | 2025 | MU | 0.0408 | 21 |
| STACK_ALL | 2025 | OPP | 0.0634 | 35 |
| STACK_ALL | 2025 | REF | 0.6752 | 1 |
| STACK_ALL | 2025 | TRK | 0.2109 | 67 |
| RESID_NONE | 2025 | BASE | 1.0000 | 2 |
| RESID_TRK | 2025 | BASE | 0.0217 | 2 |
| RESID_TRK | 2025 | TRK | 0.9783 | 67 |
| RESID_OPP | 2025 | BASE | 0.0282 | 2 |
| RESID_OPP | 2025 | OPP | 0.9718 | 35 |
| RESID_MU | 2025 | BASE | 0.0533 | 2 |
| RESID_MU | 2025 | MU | 0.9467 | 21 |
| RESID_ALL | 2025 | BASE | 0.0000 | 2 |
| RESID_ALL | 2025 | MU | 0.0578 | 21 |
| RESID_ALL | 2025 | OPP | 0.4350 | 35 |
| RESID_ALL | 2025 | TRK | 0.5072 | 67 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+TRK | 2026 | BASE | 0.8944 | 155 |
| BASE+TRK | 2026 | TRK | 0.1056 | 67 |
| BASE+OPP | 2026 | BASE | 0.9055 | 155 |
| BASE+OPP | 2026 | OPP | 0.0945 | 35 |
| BASE+MU | 2026 | BASE | 0.9529 | 155 |
| BASE+MU | 2026 | MU | 0.0471 | 21 |
| BASE+ALL | 2026 | BASE | 0.7899 | 155 |
| BASE+ALL | 2026 | MU | 0.0343 | 21 |
| BASE+ALL | 2026 | OPP | 0.0612 | 35 |
| BASE+ALL | 2026 | TRK | 0.1147 | 67 |
| STACK_BASE | 2026 | BASE | 0.6429 | 2 |
| STACK_BASE | 2026 | REF | 0.3571 | 1 |
| STACK_ALL | 2026 | BASE | 0.0042 | 2 |
| STACK_ALL | 2026 | MU | 0.0217 | 21 |
| STACK_ALL | 2026 | OPP | 0.0291 | 35 |
| STACK_ALL | 2026 | REF | 0.7667 | 1 |
| STACK_ALL | 2026 | TRK | 0.1784 | 67 |
| RESID_NONE | 2026 | BASE | 1.0000 | 2 |
| RESID_TRK | 2026 | BASE | 0.0319 | 2 |
| RESID_TRK | 2026 | TRK | 0.9681 | 67 |
| RESID_OPP | 2026 | BASE | 0.0307 | 2 |
| RESID_OPP | 2026 | OPP | 0.9693 | 35 |
| RESID_MU | 2026 | BASE | 0.0960 | 2 |
| RESID_MU | 2026 | MU | 0.9040 | 21 |
| RESID_ALL | 2026 | BASE | 0.0000 | 2 |
| RESID_ALL | 2026 | MU | 0.1985 | 21 |
| RESID_ALL | 2026 | OPP | 0.3242 | 35 |
| RESID_ALL | 2026 | TRK | 0.4773 | 67 |

## Top 30 features by gain share (BASE+ALL, STACK_ALL and RESID_ALL)
| model | season | rank | feature | group | gain_share |
|---|---|---|---|---|---|
| BASE+ALL | 2025 | 1 | dd_rate_ewm | BASE | 0.38825 |
| BASE+ALL | 2025 | 2 | dd_rate_l20 | BASE | 0.10300 |
| BASE+ALL | 2025 | 3 | prev_dd_rate | BASE | 0.05002 |
| BASE+ALL | 2025 | 4 | dd_rate_szn | BASE | 0.03048 |
| BASE+ALL | 2025 | 5 | reb_ewm | BASE | 0.01678 |
| BASE+ALL | 2025 | 6 | reb_l10 | BASE | 0.01037 |
| BASE+ALL | 2025 | 7 | trk_potast_pg_ewm | TRK | 0.01017 |
| BASE+ALL | 2025 | 8 | trk_rebch_pg_ewm | TRK | 0.00858 |
| BASE+ALL | 2025 | 9 | reb_l20 | BASE | 0.00595 |
| BASE+ALL | 2025 | 10 | reb8_rate_szn | BASE | 0.00554 |
| BASE+ALL | 2025 | 11 | abs_absent_rebounds_pg | BASE | 0.00504 |
| BASE+ALL | 2025 | 12 | reb8_rate_ewm | BASE | 0.00500 |
| BASE+ALL | 2025 | 13 | oppt_al_rebcon_share_l20 | OPP | 0.00482 |
| BASE+ALL | 2025 | 14 | opp_allow_pts_szn | BASE | 0.00462 |
| BASE+ALL | 2025 | 15 | last_starter | BASE | 0.00433 |
| BASE+ALL | 2025 | 16 | trk_rebdist_l10 | TRK | 0.00407 |
| BASE+ALL | 2025 | 17 | reb_szn | BASE | 0.00393 |
| BASE+ALL | 2025 | 18 | trk_loose_pm_l10 | TRK | 0.00379 |
| BASE+ALL | 2025 | 19 | abs_absent_points_pg | BASE | 0.00366 |
| BASE+ALL | 2025 | 20 | exp_potast | TRK | 0.00356 |
| BASE+ALL | 2025 | 21 | oppt_al_rebch_conv_l10 | OPP | 0.00349 |
| BASE+ALL | 2025 | 22 | ast_l10 | BASE | 0.00346 |
| BASE+ALL | 2025 | 23 | fta_szn | BASE | 0.00331 |
| BASE+ALL | 2025 | 24 | team_reb_share_l20 | BASE | 0.00325 |
| BASE+ALL | 2025 | 25 | min_l5 | BASE | 0.00324 |
| BASE+ALL | 2025 | 26 | mu_h2h_ast100 | MU | 0.00323 |
| BASE+ALL | 2025 | 27 | mu_off_fit | MU | 0.00312 |
| BASE+ALL | 2025 | 28 | opp_allow_ast_szn | BASE | 0.00306 |
| BASE+ALL | 2025 | 29 | oppt_contested_l10 | OPP | 0.00294 |
| BASE+ALL | 2025 | 30 | ast_szn | BASE | 0.00292 |
| STACK_ALL | 2025 | 1 | z_ref | REF | 0.67516 |
| STACK_ALL | 2025 | 2 | trk_rebch_pg_ewm | TRK | 0.06960 |
| STACK_ALL | 2025 | 3 | exp_rebch | TRK | 0.01874 |
| STACK_ALL | 2025 | 4 | exp_potast | TRK | 0.01360 |
| STACK_ALL | 2025 | 5 | min_ewm | BASE | 0.00968 |
| STACK_ALL | 2025 | 6 | trk_potast_pg_ewm | TRK | 0.00906 |
| STACK_ALL | 2025 | 7 | trk_rebdist_l10 | TRK | 0.00614 |
| STACK_ALL | 2025 | 8 | oppt_al_rebcon_share_l20 | OPP | 0.00478 |
| STACK_ALL | 2025 | 9 | trk_min_ewm | TRK | 0.00467 |
| STACK_ALL | 2025 | 10 | mu_off_pts100 | MU | 0.00450 |
| STACK_ALL | 2025 | 11 | trk_passes_pm_l10 | TRK | 0.00395 |
| STACK_ALL | 2025 | 12 | mu_def_pos_F | MU | 0.00366 |
| STACK_ALL | 2025 | 13 | oppx_ast36_allowed_pos_l20 | OPP | 0.00362 |
| STACK_ALL | 2025 | 14 | trk_rebch_conv_l20 | TRK | 0.00360 |
| STACK_ALL | 2025 | 15 | trk_screenast_pm_ewm | TRK | 0.00356 |
| STACK_ALL | 2025 | 16 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.00345 |
| STACK_ALL | 2025 | 17 | oppt_contested_l10 | OPP | 0.00339 |
| STACK_ALL | 2025 | 18 | trk_loose_pm_l10 | TRK | 0.00333 |
| STACK_ALL | 2025 | 19 | mu_h2h_pts100 | MU | 0.00330 |
| STACK_ALL | 2025 | 20 | mu_off_fit | MU | 0.00329 |
| STACK_ALL | 2025 | 21 | oppt_al_rebch_conv_l10 | OPP | 0.00304 |
| STACK_ALL | 2025 | 22 | trk_loose_pm_ewm | TRK | 0.00295 |
| STACK_ALL | 2025 | 23 | trk_drebch_pm_ewm | TRK | 0.00287 |
| STACK_ALL | 2025 | 24 | oppx_pts36_allowed_pos_l20 | OPP | 0.00277 |
| STACK_ALL | 2025 | 25 | mu_def_pos_C | MU | 0.00272 |
| STACK_ALL | 2025 | 26 | trk_rebch_conv_ewm | TRK | 0.00268 |
| STACK_ALL | 2025 | 27 | oppt_al_potast_l10 | OPP | 0.00263 |
| STACK_ALL | 2025 | 28 | oppt_al_ast_conv_l20 | OPP | 0.00252 |
| STACK_ALL | 2025 | 29 | mu_off_defby_F | MU | 0.00247 |
| STACK_ALL | 2025 | 30 | oppt_boxouts_l10 | OPP | 0.00238 |
| RESID_ALL | 2025 | 1 | oppt_al_passes_l20 | OPP | 0.15697 |
| RESID_ALL | 2025 | 2 | trk_loose_pm_ewm | TRK | 0.14142 |
| RESID_ALL | 2025 | 3 | trk_secast_pm_ewm | TRK | 0.10549 |
| RESID_ALL | 2025 | 4 | oppx_ast36_allowed_pos_l20 | OPP | 0.10429 |
| RESID_ALL | 2025 | 5 | trk_potast_last | TRK | 0.07502 |
| RESID_ALL | 2025 | 6 | trk_rebdefer_pm_l10 | TRK | 0.07451 |
| RESID_ALL | 2025 | 7 | oppx_mins_allowed_pos_l20 | OPP | 0.06247 |
| RESID_ALL | 2025 | 8 | oppx_dd_allowed_pos_l20 | OPP | 0.05982 |
| RESID_ALL | 2025 | 9 | mu_off_pts100 | MU | 0.05781 |
| RESID_ALL | 2025 | 10 | trk_rebch_conv_l5 | TRK | 0.05777 |
| RESID_ALL | 2025 | 11 | trk_passes_pm_l5 | TRK | 0.05304 |
| RESID_ALL | 2025 | 12 | oppt_al_ast_conv_l10 | OPP | 0.05141 |
| RESID_ALL | 2025 | 13 | trk_potast_pm_l5 | TRK | 0.00000 |
| RESID_ALL | 2025 | 14 | trk_potast_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 15 | trk_passes_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 16 | trk_passrec_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 17 | trk_secast_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 18 | trk_astpts_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 19 | trk_boxouts_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 20 | trk_defbox_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 21 | trk_boxreb_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 22 | trk_deflect_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 23 | trk_rebch_pm_l5 | TRK | 0.00000 |
| RESID_ALL | 2025 | 24 | trk_games_prior | TRK | 0.00000 |
| RESID_ALL | 2025 | 25 | trk_boxouts_pm_l5 | TRK | 0.00000 |
| RESID_ALL | 2025 | 26 | trk_ast_conv_l5 | TRK | 0.00000 |
| RESID_ALL | 2025 | 27 | trk_rebch_pm_l10 | TRK | 0.00000 |
| RESID_ALL | 2025 | 28 | position | BASE | 0.00000 |
| RESID_ALL | 2025 | 29 | min_ewm | BASE | 0.00000 |
| RESID_ALL | 2025 | 30 | trk_boxout_teamsuccess_l10 | TRK | 0.00000 |
| BASE+ALL | 2026 | 1 | dd_rate_ewm | BASE | 0.40372 |
| BASE+ALL | 2026 | 2 | dd_rate_l20 | BASE | 0.08736 |
| BASE+ALL | 2026 | 3 | prev_dd_rate | BASE | 0.04334 |
| BASE+ALL | 2026 | 4 | dd_rate_szn | BASE | 0.02303 |
| BASE+ALL | 2026 | 5 | reb_l10 | BASE | 0.01587 |
| BASE+ALL | 2026 | 6 | reb_ewm | BASE | 0.01431 |
| BASE+ALL | 2026 | 7 | trk_rebch_pg_ewm | TRK | 0.01388 |
| BASE+ALL | 2026 | 8 | trk_potast_pg_ewm | TRK | 0.00721 |
| BASE+ALL | 2026 | 9 | abs_absent_rebounds_pg | BASE | 0.00554 |
| BASE+ALL | 2026 | 10 | last_starter | BASE | 0.00535 |
| BASE+ALL | 2026 | 11 | reb_szn | BASE | 0.00527 |
| BASE+ALL | 2026 | 12 | abs_absent_points_pg | BASE | 0.00510 |
| BASE+ALL | 2026 | 13 | min_trend | BASE | 0.00469 |
| BASE+ALL | 2026 | 14 | last_min | BASE | 0.00440 |
| BASE+ALL | 2026 | 15 | trk_rebch_last | TRK | 0.00429 |
| BASE+ALL | 2026 | 16 | abs_absent_assists_pg | BASE | 0.00424 |
| BASE+ALL | 2026 | 17 | opp_allow_reb_l20 | BASE | 0.00421 |
| BASE+ALL | 2026 | 18 | reb8_rate_szn | BASE | 0.00402 |
| BASE+ALL | 2026 | 19 | oppt_al_rebcon_share_l20 | OPP | 0.00398 |
| BASE+ALL | 2026 | 20 | mu_off_fit | MU | 0.00391 |
| BASE+ALL | 2026 | 21 | opp_allow_pts_szn | BASE | 0.00348 |
| BASE+ALL | 2026 | 22 | mu_h2h_pts100 | MU | 0.00335 |
| BASE+ALL | 2026 | 23 | trk_passes_pm_l10 | TRK | 0.00314 |
| BASE+ALL | 2026 | 24 | trk_loose_pm_l10 | TRK | 0.00303 |
| BASE+ALL | 2026 | 25 | trk_rebch_conv_l20 | TRK | 0.00302 |
| BASE+ALL | 2026 | 26 | oppt_screenast_l20 | OPP | 0.00295 |
| BASE+ALL | 2026 | 27 | team_pd_l10 | BASE | 0.00282 |
| BASE+ALL | 2026 | 28 | oppt_al_rebch_conv_l10 | OPP | 0.00276 |
| BASE+ALL | 2026 | 29 | ast_ewm | BASE | 0.00276 |
| BASE+ALL | 2026 | 30 | reb8_rate_ewm | BASE | 0.00272 |
| STACK_ALL | 2026 | 1 | z_ref | REF | 0.76669 |
| STACK_ALL | 2026 | 2 | trk_rebch_pg_ewm | TRK | 0.07948 |
| STACK_ALL | 2026 | 3 | exp_rebch | TRK | 0.02345 |
| STACK_ALL | 2026 | 4 | trk_potast_pg_ewm | TRK | 0.01379 |
| STACK_ALL | 2026 | 5 | exp_potast | TRK | 0.01102 |
| STACK_ALL | 2026 | 6 | trk_min_ewm | TRK | 0.00524 |
| STACK_ALL | 2026 | 7 | min_ewm | BASE | 0.00402 |
| STACK_ALL | 2026 | 8 | mu_off_pts100 | MU | 0.00318 |
| STACK_ALL | 2026 | 9 | oppt_al_rebcon_share_l20 | OPP | 0.00273 |
| STACK_ALL | 2026 | 10 | mu_h2h_pts100 | MU | 0.00260 |
| STACK_ALL | 2026 | 11 | trk_rebch_conv_ewm | TRK | 0.00258 |
| STACK_ALL | 2026 | 12 | trk_rebdist_l10 | TRK | 0.00253 |
| STACK_ALL | 2026 | 13 | mu_off_ast100 | MU | 0.00234 |
| STACK_ALL | 2026 | 14 | mu_off_fit | MU | 0.00217 |
| STACK_ALL | 2026 | 15 | trk_rebch_conv_l20 | TRK | 0.00194 |
| STACK_ALL | 2026 | 16 | trk_passes_pm_l10 | TRK | 0.00189 |
| STACK_ALL | 2026 | 17 | oppt_deflect_l20 | OPP | 0.00167 |
| STACK_ALL | 2026 | 18 | mu_best_def_vs_pos | MU | 0.00159 |
| STACK_ALL | 2026 | 19 | oppt_screenast_l20 | OPP | 0.00153 |
| STACK_ALL | 2026 | 20 | trk_reb_contest_share_l10 | TRK | 0.00150 |
| STACK_ALL | 2026 | 21 | trk_ast_conv_l20 | TRK | 0.00148 |
| STACK_ALL | 2026 | 22 | trk_ast_conv_l5 | TRK | 0.00148 |
| STACK_ALL | 2026 | 23 | oppx_pts36_allowed_pos_l20 | OPP | 0.00147 |
| STACK_ALL | 2026 | 24 | trk_rebch_last | TRK | 0.00146 |
| STACK_ALL | 2026 | 25 | oppt_al_ast_conv_l10 | OPP | 0.00145 |
| STACK_ALL | 2026 | 26 | oppt_al_potast_l10 | OPP | 0.00143 |
| STACK_ALL | 2026 | 27 | trk_boxout_defshare_l10 | TRK | 0.00141 |
| STACK_ALL | 2026 | 28 | oppt_al_potast_l20 | OPP | 0.00140 |
| STACK_ALL | 2026 | 29 | trk_rebch_conv_l5 | TRK | 0.00137 |
| STACK_ALL | 2026 | 30 | trk_astpts_pm_ewm | TRK | 0.00128 |
| RESID_ALL | 2026 | 1 | trk_rebch_conv_l20 | TRK | 0.12028 |
| RESID_ALL | 2026 | 2 | oppt_al_rebcon_share_l20 | OPP | 0.07097 |
| RESID_ALL | 2026 | 3 | mu_def_ast_vs_exp | MU | 0.05442 |
| RESID_ALL | 2026 | 4 | oppt_al_passes_l20 | OPP | 0.04638 |
| RESID_ALL | 2026 | 5 | oppt_al_potast_l20 | OPP | 0.04396 |
| RESID_ALL | 2026 | 6 | oppt_deflect_l20 | OPP | 0.03419 |
| RESID_ALL | 2026 | 7 | mu_off_defby_G | MU | 0.03280 |
| RESID_ALL | 2026 | 8 | mu_def_pos_C | MU | 0.03274 |
| RESID_ALL | 2026 | 9 | oppx_pts36_allowed_pos_l20 | OPP | 0.02617 |
| RESID_ALL | 2026 | 10 | trk_boxout_defshare_l10 | TRK | 0.02598 |
| RESID_ALL | 2026 | 11 | trk_passes_pm_l5 | TRK | 0.02573 |
| RESID_ALL | 2026 | 12 | mu_def_defbox_pm | MU | 0.02560 |
| RESID_ALL | 2026 | 13 | trk_passes_pm_l10 | TRK | 0.02518 |
| RESID_ALL | 2026 | 14 | oppt_deflect_l10 | OPP | 0.01881 |
| RESID_ALL | 2026 | 15 | trk_passrec_pm_ewm | TRK | 0.01777 |
| RESID_ALL | 2026 | 16 | oppx_pts_allowed_pos_l10 | OPP | 0.01730 |
| RESID_ALL | 2026 | 17 | oppt_al_rebch_conv_l20 | OPP | 0.01701 |
| RESID_ALL | 2026 | 18 | mu_def_pts_vs_exp | MU | 0.01586 |
| RESID_ALL | 2026 | 19 | trk_drebch_pm_l10 | TRK | 0.01499 |
| RESID_ALL | 2026 | 20 | trk_reb_contest_share_l10 | TRK | 0.01493 |
| RESID_ALL | 2026 | 21 | trk_rebdefer_pm_ewm | TRK | 0.01483 |
| RESID_ALL | 2026 | 22 | mu_off_fit | MU | 0.01451 |
| RESID_ALL | 2026 | 23 | trk_defbox_pm_l10 | TRK | 0.01401 |
| RESID_ALL | 2026 | 24 | oppt_contested_l20 | OPP | 0.01399 |
| RESID_ALL | 2026 | 25 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.01373 |
| RESID_ALL | 2026 | 26 | trk_loose_pm_ewm | TRK | 0.01358 |
| RESID_ALL | 2026 | 27 | trk_boxreb_pm_l10 | TRK | 0.01338 |
| RESID_ALL | 2026 | 28 | trk_potast_pm_l5 | TRK | 0.01295 |
| RESID_ALL | 2026 | 29 | trk_contested_pm_ewm | TRK | 0.01288 |
| RESID_ALL | 2026 | 30 | mu_def_rebch_pm | MU | 0.01282 |

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
    "BASE+TRK_best_iteration": 171,
    "BASE+TRK_holdout_logloss": 0.209841593974867,
    "BASE+OPP_best_iteration": 117,
    "BASE+OPP_holdout_logloss": 0.211087413230205,
    "BASE+MU_best_iteration": 158,
    "BASE+MU_holdout_logloss": 0.21018077509445174,
    "BASE+ALL_best_iteration": 139,
    "BASE+ALL_holdout_logloss": 0.21054640963345767,
    "STACK_BASE_best_iteration": 544,
    "STACK_BASE_holdout_logloss": 0.2108647093254539,
    "STACK_ALL_best_iteration": 155,
    "STACK_ALL_holdout_logloss": 0.2028114249225051,
    "RESID_NONE_best_iteration": 7,
    "RESID_NONE_holdout_logloss": 0.20318533302391203,
    "RESID_TRK_best_iteration": 37,
    "RESID_TRK_holdout_logloss": 0.2026903759484689,
    "RESID_OPP_best_iteration": 11,
    "RESID_OPP_holdout_logloss": 0.20300775894496234,
    "RESID_MU_best_iteration": 67,
    "RESID_MU_holdout_logloss": 0.2026074345172758,
    "RESID_ALL_best_iteration": 1,
    "RESID_ALL_holdout_logloss": 0.2032090448171537
  },
  "2026": {
    "n_fit": 43767,
    "n_hold": 7776,
    "n_test": 26055,
    "cut_date": "2025-02-25",
    "BASE_best_iteration": 207,
    "BASE_holdout_logloss": 0.2071726278704816,
    "BASE+TRK_best_iteration": 142,
    "BASE+TRK_holdout_logloss": 0.20855795342139294,
    "BASE+OPP_best_iteration": 274,
    "BASE+OPP_holdout_logloss": 0.2071186953523475,
    "BASE+MU_best_iteration": 192,
    "BASE+MU_holdout_logloss": 0.20734695640208486,
    "BASE+ALL_best_iteration": 257,
    "BASE+ALL_holdout_logloss": 0.20808393050599236,
    "STACK_BASE_best_iteration": 768,
    "STACK_BASE_holdout_logloss": 0.20751908512946754,
    "STACK_ALL_best_iteration": 116,
    "STACK_ALL_holdout_logloss": 0.20604543499979988,
    "RESID_NONE_best_iteration": 2,
    "RESID_NONE_holdout_logloss": 0.20659804174081567,
    "RESID_TRK_best_iteration": 13,
    "RESID_TRK_holdout_logloss": 0.2064776787425774,
    "RESID_OPP_best_iteration": 4,
    "RESID_OPP_holdout_logloss": 0.2065552213497972,
    "RESID_MU_best_iteration": 2,
    "RESID_MU_holdout_logloss": 0.20664834615958338,
    "RESID_ALL_best_iteration": 5,
    "RESID_ALL_holdout_logloss": 0.2065344685072743
  }
}
```
