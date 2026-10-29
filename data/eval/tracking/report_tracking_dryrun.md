# Tracking, opponent and matchup feature lift test

Regular-season rows, season keys 2024 to 2026 (2023-24 to 2025-26). Test 2025 is trained on 2024; test 2026 on 2024 and 2025. All variants use identical rows, hyperparameters, seed, holdout split and Platt calibration. REF is the saved v1 C_full prediction, trained on 2018 onward with all season types, so it has more history than the era-only variants; the STACK rows measure the new features as increments over REF. The RESID rows boost from logit(REF) as the initial score and see only the new features (plus min_ewm and position), so zero trees equals REF exactly and every departure from REF is chosen by the holdout; RESID_NONE is the control with no new features, and the raw rows skip the Platt step. BLEND_REF_ALL is a 0.5/0.5 logit blend of REF and BASE+ALL. The proxy price q = min(0.97, 1.08 x Baseline A) is an assumption, not a book price.

## Coverage
| season | rows | trk_5plus_prior | oppt_present | mu_present |
|---|---|---|---|---|
| 2024 | 25820 | 0.9104 | 1.0000 | 1.0000 |
| 2025 | 25723 | 0.9958 | 1.0000 | 1.0000 |
| 2026 | 26055 | 0.8144 | 1.0000 | 1.0000 |

## Metric 1: calibrated log loss, Brier, AUC
| season | model | n | base_rate | logloss | brier | auc |
|---|---|---|---|---|---|---|
| 2025 | A | 25723 | 0.0872 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | REF | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.1975 | 0.0569 | 0.8933 |
| 2025 | BASE+TRK | 25723 | 0.0872 | 0.1976 | 0.0571 | 0.8936 |
| 2025 | BASE+OPP | 25723 | 0.0872 | 0.1983 | 0.0571 | 0.8921 |
| 2025 | BASE+MU | 25723 | 0.0872 | 0.1981 | 0.0571 | 0.8924 |
| 2025 | BASE+ALL | 25723 | 0.0872 | 0.1977 | 0.0572 | 0.8936 |
| 2025 | STACK_BASE | 25723 | 0.0872 | 0.1994 | 0.0579 | 0.8897 |
| 2025 | STACK_ALL | 25723 | 0.0872 | 0.1950 | 0.0567 | 0.8962 |
| 2025 | RESID_NONE | 25723 | 0.0872 | 0.1940 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK | 25723 | 0.0872 | 0.1938 | 0.0564 | 0.8980 |
| 2025 | RESID_OPP | 25723 | 0.0872 | 0.1941 | 0.0565 | 0.8984 |
| 2025 | RESID_MU | 25723 | 0.0872 | 0.1943 | 0.0566 | 0.8979 |
| 2025 | RESID_ALL | 25723 | 0.0872 | 0.1949 | 0.0566 | 0.8972 |
| 2025 | RESID_NONE raw | 25723 | 0.0872 | 0.1935 | 0.0565 | 0.8985 |
| 2025 | RESID_TRK raw | 25723 | 0.0872 | 0.1935 | 0.0565 | 0.8980 |
| 2025 | RESID_OPP raw | 25723 | 0.0872 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | RESID_MU raw | 25723 | 0.0872 | 0.1937 | 0.0566 | 0.8979 |
| 2025 | RESID_ALL raw | 25723 | 0.0872 | 0.1944 | 0.0567 | 0.8972 |
| 2025 | BLEND_REF_ALL | 25723 | 0.0872 | 0.1931 | 0.0564 | 0.8985 |
| 2026 | A | 26055 | 0.0733 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | REF | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.1838 | 0.0524 | 0.8810 |
| 2026 | BASE+TRK | 26055 | 0.0733 | 0.1851 | 0.0525 | 0.8773 |
| 2026 | BASE+OPP | 26055 | 0.0733 | 0.1840 | 0.0525 | 0.8806 |
| 2026 | BASE+MU | 26055 | 0.0733 | 0.1843 | 0.0525 | 0.8797 |
| 2026 | BASE+ALL | 26055 | 0.0733 | 0.1849 | 0.0524 | 0.8784 |
| 2026 | STACK_BASE | 26055 | 0.0733 | 0.1841 | 0.0525 | 0.8800 |
| 2026 | STACK_ALL | 26055 | 0.0733 | 0.1824 | 0.0520 | 0.8840 |
| 2026 | RESID_NONE | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK | 26055 | 0.0733 | 0.1808 | 0.0517 | 0.8861 |
| 2026 | RESID_OPP | 26055 | 0.0733 | 0.1809 | 0.0517 | 0.8860 |
| 2026 | RESID_MU | 26055 | 0.0733 | 0.1809 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL | 26055 | 0.0733 | 0.1806 | 0.0517 | 0.8864 |
| 2026 | RESID_NONE raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8863 |
| 2026 | RESID_TRK raw | 26055 | 0.0733 | 0.1807 | 0.0518 | 0.8861 |
| 2026 | RESID_OPP raw | 26055 | 0.0733 | 0.1807 | 0.0518 | 0.8860 |
| 2026 | RESID_MU raw | 26055 | 0.0733 | 0.1808 | 0.0518 | 0.8862 |
| 2026 | RESID_ALL raw | 26055 | 0.0733 | 0.1806 | 0.0517 | 0.8864 |
| 2026 | BLEND_REF_ALL | 26055 | 0.0733 | 0.1813 | 0.0519 | 0.8848 |
| all | A | 51778 | 0.0802 | 0.1989 | 0.0557 | 0.8643 |
| all | REF | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | BASE | 51778 | 0.0802 | 0.1906 | 0.0546 | 0.8871 |
| all | BASE+TRK | 51778 | 0.0802 | 0.1913 | 0.0548 | 0.8848 |
| all | BASE+OPP | 51778 | 0.0802 | 0.1911 | 0.0548 | 0.8863 |
| all | BASE+MU | 51778 | 0.0802 | 0.1911 | 0.0548 | 0.8861 |
| all | BASE+ALL | 51778 | 0.0802 | 0.1913 | 0.0548 | 0.8859 |
| all | STACK_BASE | 51778 | 0.0802 | 0.1917 | 0.0552 | 0.8850 |
| all | STACK_ALL | 51778 | 0.0802 | 0.1887 | 0.0543 | 0.8907 |
| all | RESID_NONE | 51778 | 0.0802 | 0.1874 | 0.0541 | 0.8927 |
| all | RESID_TRK | 51778 | 0.0802 | 0.1873 | 0.0540 | 0.8926 |
| all | RESID_OPP | 51778 | 0.0802 | 0.1875 | 0.0541 | 0.8926 |
| all | RESID_MU | 51778 | 0.0802 | 0.1875 | 0.0542 | 0.8924 |
| all | RESID_ALL | 51778 | 0.0802 | 0.1877 | 0.0541 | 0.8921 |
| all | RESID_NONE raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8925 |
| all | RESID_TRK raw | 51778 | 0.0802 | 0.1870 | 0.0541 | 0.8925 |
| all | RESID_OPP raw | 51778 | 0.0802 | 0.1871 | 0.0541 | 0.8926 |
| all | RESID_MU raw | 51778 | 0.0802 | 0.1872 | 0.0542 | 0.8924 |
| all | RESID_ALL raw | 51778 | 0.0802 | 0.1874 | 0.0542 | 0.8922 |
| all | BLEND_REF_ALL | 51778 | 0.0802 | 0.1872 | 0.0541 | 0.8923 |

## Bootstrap of log-loss differences (block bootstrap by game date, 1000 resamples; negative favors the model)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2025 | p_BASE+TRK_cal | p_BASE_cal | 0.00012 | -0.00052 | 0.00078 | 0.35600 |
| 2025 | p_BASE+OPP_cal | p_BASE_cal | 0.00078 | 0.00014 | 0.00152 | 0.00600 |
| 2025 | p_BASE+MU_cal | p_BASE_cal | 0.00061 | 0.00005 | 0.00118 | 0.01400 |
| 2025 | p_BASE+ALL_cal | p_BASE_cal | 0.00017 | -0.00070 | 0.00100 | 0.31900 |
| 2025 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00434 | -0.00587 | -0.00292 | 1.00000 |
| 2025 | p_STACK_ALL_cal | p_REF_cal | 0.00143 | -0.00000 | 0.00274 | 0.02600 |
| 2025 | p_STACK_BASE_cal | p_REF_cal | 0.00578 | 0.00416 | 0.00751 | 0.00000 |
| 2025 | p_BASE+ALL_cal | p_REF_cal | 0.00407 | 0.00216 | 0.00595 | 0.00000 |
| 2025 | p_RESID_NONE_cal | p_REF_cal | 0.00043 | -0.00012 | 0.00096 | 0.06300 |
| 2025 | p_RESID_TRK_cal | p_REF_cal | 0.00024 | -0.00054 | 0.00092 | 0.26000 |
| 2025 | p_RESID_OPP_cal | p_REF_cal | 0.00054 | -0.00004 | 0.00112 | 0.03600 |
| 2025 | p_RESID_MU_cal | p_REF_cal | 0.00065 | 0.00009 | 0.00121 | 0.01300 |
| 2025 | p_RESID_ALL_cal | p_REF_cal | 0.00125 | 0.00030 | 0.00210 | 0.00700 |
| 2025 | p_RESID_NONE_raw | p_REF_cal | -0.00008 | -0.00017 | 0.00002 | 0.93700 |
| 2025 | p_RESID_TRK_raw | p_REF_cal | -0.00012 | -0.00067 | 0.00043 | 0.66900 |
| 2025 | p_RESID_OPP_raw | p_REF_cal | -0.00000 | -0.00018 | 0.00018 | 0.49800 |
| 2025 | p_RESID_MU_raw | p_REF_cal | 0.00014 | -0.00002 | 0.00030 | 0.03700 |
| 2025 | p_RESID_ALL_raw | p_REF_cal | 0.00079 | 0.00002 | 0.00150 | 0.02100 |
| 2025 | p_BLEND_cal | p_REF_cal | -0.00048 | -0.00143 | 0.00045 | 0.83800 |
| 2025 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00004 | -0.00061 | 0.00050 | 0.57300 |
| 2025 | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00008 | -0.00013 | 0.00029 | 0.25900 |
| 2025 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00022 | 0.00006 | 0.00039 | 0.00500 |
| 2025 | p_RESID_ALL_raw | p_RESID_NONE_raw | 0.00087 | 0.00012 | 0.00156 | 0.01000 |
| 2026 | p_BASE+TRK_cal | p_BASE_cal | 0.00122 | -0.00002 | 0.00273 | 0.02600 |
| 2026 | p_BASE+OPP_cal | p_BASE_cal | 0.00014 | -0.00052 | 0.00078 | 0.39600 |
| 2026 | p_BASE+MU_cal | p_BASE_cal | 0.00044 | -0.00015 | 0.00097 | 0.06800 |
| 2026 | p_BASE+ALL_cal | p_BASE_cal | 0.00108 | -0.00008 | 0.00233 | 0.04100 |
| 2026 | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00167 | -0.00286 | -0.00055 | 0.99700 |
| 2026 | p_STACK_ALL_cal | p_REF_cal | 0.00167 | 0.00058 | 0.00273 | 0.00000 |
| 2026 | p_STACK_BASE_cal | p_REF_cal | 0.00334 | 0.00223 | 0.00440 | 0.00000 |
| 2026 | p_BASE+ALL_cal | p_REF_cal | 0.00417 | 0.00218 | 0.00644 | 0.00000 |
| 2026 | p_RESID_NONE_cal | p_REF_cal | 0.00016 | -0.00011 | 0.00039 | 0.11400 |
| 2026 | p_RESID_TRK_cal | p_REF_cal | 0.00003 | -0.00024 | 0.00027 | 0.41600 |
| 2026 | p_RESID_OPP_cal | p_REF_cal | 0.00010 | -0.00016 | 0.00033 | 0.21900 |
| 2026 | p_RESID_MU_cal | p_REF_cal | 0.00017 | -0.00012 | 0.00039 | 0.12200 |
| 2026 | p_RESID_ALL_cal | p_REF_cal | -0.00013 | -0.00047 | 0.00018 | 0.78200 |
| 2026 | p_RESID_NONE_raw | p_REF_cal | 0.00000 | -0.00002 | 0.00003 | 0.47200 |
| 2026 | p_RESID_TRK_raw | p_REF_cal | -0.00007 | -0.00016 | 0.00002 | 0.95200 |
| 2026 | p_RESID_OPP_raw | p_REF_cal | -0.00005 | -0.00010 | 0.00000 | 0.96000 |
| 2026 | p_RESID_MU_raw | p_REF_cal | 0.00001 | -0.00003 | 0.00004 | 0.38600 |
| 2026 | p_RESID_ALL_raw | p_REF_cal | -0.00019 | -0.00040 | 0.00003 | 0.95400 |
| 2026 | p_BLEND_cal | p_REF_cal | 0.00056 | -0.00037 | 0.00161 | 0.11700 |
| 2026 | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00008 | -0.00017 | 0.00002 | 0.94500 |
| 2026 | p_RESID_OPP_raw | p_RESID_NONE_raw | -0.00005 | -0.00011 | 0.00001 | 0.95600 |
| 2026 | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00000 | -0.00004 | 0.00004 | 0.43500 |
| 2026 | p_RESID_ALL_raw | p_RESID_NONE_raw | -0.00019 | -0.00041 | 0.00003 | 0.95200 |
| all | p_BASE+TRK_cal | p_BASE_cal | 0.00067 | -0.00009 | 0.00146 | 0.04800 |
| all | p_BASE+OPP_cal | p_BASE_cal | 0.00046 | -0.00002 | 0.00095 | 0.03100 |
| all | p_BASE+MU_cal | p_BASE_cal | 0.00052 | 0.00012 | 0.00091 | 0.00400 |
| all | p_BASE+ALL_cal | p_BASE_cal | 0.00063 | -0.00011 | 0.00135 | 0.05600 |
| all | p_STACK_ALL_cal | p_STACK_BASE_cal | -0.00300 | -0.00396 | -0.00201 | 1.00000 |
| all | p_STACK_ALL_cal | p_REF_cal | 0.00155 | 0.00070 | 0.00236 | 0.00100 |
| all | p_STACK_BASE_cal | p_REF_cal | 0.00455 | 0.00349 | 0.00551 | 0.00000 |
| all | p_BASE+ALL_cal | p_REF_cal | 0.00412 | 0.00269 | 0.00554 | 0.00000 |
| all | p_RESID_NONE_cal | p_REF_cal | 0.00029 | -0.00001 | 0.00061 | 0.03000 |
| all | p_RESID_TRK_cal | p_REF_cal | 0.00014 | -0.00024 | 0.00051 | 0.25700 |
| all | p_RESID_OPP_cal | p_REF_cal | 0.00032 | -0.00000 | 0.00068 | 0.02700 |
| all | p_RESID_MU_cal | p_REF_cal | 0.00041 | 0.00009 | 0.00075 | 0.00300 |
| all | p_RESID_ALL_cal | p_REF_cal | 0.00056 | 0.00010 | 0.00107 | 0.00900 |
| all | p_RESID_NONE_raw | p_REF_cal | -0.00004 | -0.00008 | 0.00001 | 0.95400 |
| all | p_RESID_TRK_raw | p_REF_cal | -0.00010 | -0.00036 | 0.00017 | 0.74900 |
| all | p_RESID_OPP_raw | p_REF_cal | -0.00003 | -0.00012 | 0.00007 | 0.67000 |
| all | p_RESID_MU_raw | p_REF_cal | 0.00007 | -0.00001 | 0.00016 | 0.04100 |
| all | p_RESID_ALL_raw | p_REF_cal | 0.00030 | -0.00007 | 0.00067 | 0.06300 |
| all | p_BLEND_cal | p_REF_cal | 0.00004 | -0.00064 | 0.00071 | 0.46700 |
| all | p_RESID_TRK_raw | p_RESID_NONE_raw | -0.00006 | -0.00032 | 0.00021 | 0.66300 |
| all | p_RESID_OPP_raw | p_RESID_NONE_raw | 0.00001 | -0.00010 | 0.00013 | 0.38000 |
| all | p_RESID_MU_raw | p_RESID_NONE_raw | 0.00011 | 0.00002 | 0.00021 | 0.00900 |
| all | p_RESID_ALL_raw | p_RESID_NONE_raw | 0.00034 | -0.00004 | 0.00072 | 0.04300 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | logloss | brier | auc |
|---|---|---|---|---|---|---|
| 2025 | A | 2129 | 0.4298 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | REF | 2129 | 0.4298 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.6604 | 0.2339 | 0.6328 |
| 2025 | BASE+TRK | 2129 | 0.4298 | 0.6611 | 0.2344 | 0.6290 |
| 2025 | BASE+OPP | 2129 | 0.4298 | 0.6622 | 0.2349 | 0.6266 |
| 2025 | BASE+MU | 2129 | 0.4298 | 0.6638 | 0.2354 | 0.6264 |
| 2025 | BASE+ALL | 2129 | 0.4298 | 0.6626 | 0.2349 | 0.6265 |
| 2025 | STACK_BASE | 2129 | 0.4298 | 0.6815 | 0.2424 | 0.6151 |
| 2025 | STACK_ALL | 2129 | 0.4298 | 0.6629 | 0.2350 | 0.6294 |
| 2025 | RESID_NONE | 2129 | 0.4298 | 0.6615 | 0.2346 | 0.6276 |
| 2025 | RESID_TRK | 2129 | 0.4298 | 0.6595 | 0.2335 | 0.6325 |
| 2025 | RESID_OPP | 2129 | 0.4298 | 0.6621 | 0.2349 | 0.6249 |
| 2025 | RESID_MU | 2129 | 0.4298 | 0.6627 | 0.2352 | 0.6212 |
| 2025 | RESID_ALL | 2129 | 0.4298 | 0.6633 | 0.2353 | 0.6244 |
| 2025 | RESID_NONE raw | 2129 | 0.4298 | 0.6633 | 0.2353 | 0.6276 |
| 2025 | RESID_TRK raw | 2129 | 0.4298 | 0.6625 | 0.2347 | 0.6325 |
| 2025 | RESID_OPP raw | 2129 | 0.4298 | 0.6642 | 0.2358 | 0.6249 |
| 2025 | RESID_MU raw | 2129 | 0.4298 | 0.6644 | 0.2359 | 0.6212 |
| 2025 | RESID_ALL raw | 2129 | 0.4298 | 0.6678 | 0.2372 | 0.6244 |
| 2025 | BLEND_REF_ALL | 2129 | 0.4298 | 0.6579 | 0.2329 | 0.6344 |
| 2026 | A | 1976 | 0.3806 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | REF | 1976 | 0.3806 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.6311 | 0.2204 | 0.6558 |
| 2026 | BASE+TRK | 1976 | 0.3806 | 0.6295 | 0.2195 | 0.6576 |
| 2026 | BASE+OPP | 1976 | 0.3806 | 0.6311 | 0.2205 | 0.6547 |
| 2026 | BASE+MU | 1976 | 0.3806 | 0.6318 | 0.2206 | 0.6533 |
| 2026 | BASE+ALL | 1976 | 0.3806 | 0.6273 | 0.2185 | 0.6611 |
| 2026 | STACK_BASE | 1976 | 0.3806 | 0.6326 | 0.2210 | 0.6497 |
| 2026 | STACK_ALL | 1976 | 0.3806 | 0.6269 | 0.2183 | 0.6620 |
| 2026 | RESID_NONE | 1976 | 0.3806 | 0.6264 | 0.2181 | 0.6620 |
| 2026 | RESID_TRK | 1976 | 0.3806 | 0.6257 | 0.2178 | 0.6637 |
| 2026 | RESID_OPP | 1976 | 0.3806 | 0.6261 | 0.2180 | 0.6636 |
| 2026 | RESID_MU | 1976 | 0.3806 | 0.6263 | 0.2181 | 0.6622 |
| 2026 | RESID_ALL | 1976 | 0.3806 | 0.6254 | 0.2177 | 0.6634 |
| 2026 | RESID_NONE raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6620 |
| 2026 | RESID_TRK raw | 1976 | 0.3806 | 0.6268 | 0.2183 | 0.6637 |
| 2026 | RESID_OPP raw | 1976 | 0.3806 | 0.6272 | 0.2184 | 0.6636 |
| 2026 | RESID_MU raw | 1976 | 0.3806 | 0.6276 | 0.2186 | 0.6622 |
| 2026 | RESID_ALL raw | 1976 | 0.3806 | 0.6261 | 0.2180 | 0.6634 |
| 2026 | BLEND_REF_ALL | 1976 | 0.3806 | 0.6242 | 0.2173 | 0.6651 |
| all | A | 4105 | 0.4061 | 0.6557 | 0.2318 | 0.6196 |
| all | REF | 4105 | 0.4061 | 0.6463 | 0.2274 | 0.6442 |
| all | BASE | 4105 | 0.4061 | 0.6462 | 0.2274 | 0.6456 |
| all | BASE+TRK | 4105 | 0.4061 | 0.6459 | 0.2272 | 0.6456 |
| all | BASE+OPP | 4105 | 0.4061 | 0.6472 | 0.2280 | 0.6422 |
| all | BASE+MU | 4105 | 0.4061 | 0.6484 | 0.2283 | 0.6421 |
| all | BASE+ALL | 4105 | 0.4061 | 0.6456 | 0.2270 | 0.6459 |
| all | STACK_BASE | 4105 | 0.4061 | 0.6580 | 0.2321 | 0.6279 |
| all | STACK_ALL | 4105 | 0.4061 | 0.6456 | 0.2269 | 0.6475 |
| all | RESID_NONE | 4105 | 0.4061 | 0.6446 | 0.2267 | 0.6451 |
| all | RESID_TRK | 4105 | 0.4061 | 0.6432 | 0.2259 | 0.6493 |
| all | RESID_OPP | 4105 | 0.4061 | 0.6447 | 0.2267 | 0.6447 |
| all | RESID_MU | 4105 | 0.4061 | 0.6452 | 0.2270 | 0.6423 |
| all | RESID_ALL | 4105 | 0.4061 | 0.6450 | 0.2268 | 0.6456 |
| all | RESID_NONE raw | 4105 | 0.4061 | 0.6461 | 0.2273 | 0.6451 |
| all | RESID_TRK raw | 4105 | 0.4061 | 0.6453 | 0.2268 | 0.6494 |
| all | RESID_OPP raw | 4105 | 0.4061 | 0.6464 | 0.2274 | 0.6447 |
| all | RESID_MU raw | 4105 | 0.4061 | 0.6467 | 0.2276 | 0.6425 |
| all | RESID_ALL raw | 4105 | 0.4061 | 0.6477 | 0.2280 | 0.6458 |
| all | BLEND_REF_ALL | 4105 | 0.4061 | 0.6417 | 0.2254 | 0.6521 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 | distinct_players |
|---|---|---|---|---|---|---|---|
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 | 31 |
| 2025 | REF | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 | 33 |
| 2025 | BASE | 164 | 0.7805 | 0.6829 | 0.3841 | 0.7065 | 35 |
| 2025 | BASE+TRK | 164 | 0.8110 | 0.6972 | 0.3476 | 0.7053 | 32 |
| 2025 | BASE+OPP | 164 | 0.7927 | 0.6829 | 0.3598 | 0.7000 | 34 |
| 2025 | BASE+MU | 164 | 0.8049 | 0.6768 | 0.3598 | 0.7122 | 32 |
| 2025 | BASE+ALL | 164 | 0.7927 | 0.6707 | 0.3232 | 0.6923 | 32 |
| 2025 | STACK_BASE | 164 | 0.7622 | 0.6626 | 0.3110 | 0.6552 | 35 |
| 2025 | STACK_ALL | 164 | 0.8110 | 0.7114 | 0.3841 | 0.7053 | 36 |
| 2025 | RESID_NONE | 164 | 0.8171 | 0.7012 | 0.3537 | 0.6950 | 35 |
| 2025 | RESID_TRK | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7110 | 33 |
| 2025 | RESID_OPP | 164 | 0.8415 | 0.6992 | 0.3720 | 0.6984 | 35 |
| 2025 | RESID_MU | 164 | 0.8293 | 0.6972 | 0.3598 | 0.6936 | 33 |
| 2025 | RESID_ALL | 164 | 0.8537 | 0.6972 | 0.3537 | 0.7100 | 35 |
| 2025 | RESID_NONE raw | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7390 | 35 |
| 2025 | RESID_TRK raw | 164 | 0.8171 | 0.7012 | 0.3537 | 0.7566 | 33 |
| 2025 | RESID_OPP raw | 164 | 0.8415 | 0.6992 | 0.3720 | 0.7441 | 35 |
| 2025 | RESID_MU raw | 164 | 0.8293 | 0.6972 | 0.3598 | 0.7384 | 33 |
| 2025 | RESID_ALL raw | 164 | 0.8537 | 0.6972 | 0.3537 | 0.7630 | 35 |
| 2025 | BLEND_REF_ALL | 164 | 0.8476 | 0.7093 | 0.3780 | 0.7144 | 33 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 | 31 |
| 2026 | REF | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 | 35 |
| 2026 | BASE | 165 | 0.6848 | 0.6081 | 0.2182 | 0.6598 | 36 |
| 2026 | BASE+TRK | 165 | 0.6788 | 0.5980 | 0.2061 | 0.6273 | 35 |
| 2026 | BASE+OPP | 165 | 0.6848 | 0.5980 | 0.2061 | 0.6245 | 37 |
| 2026 | BASE+MU | 165 | 0.6485 | 0.5960 | 0.2061 | 0.6451 | 36 |
| 2026 | BASE+ALL | 165 | 0.6606 | 0.6040 | 0.1939 | 0.6172 | 36 |
| 2026 | STACK_BASE | 165 | 0.6909 | 0.5939 | 0.1697 | 0.6487 | 37 |
| 2026 | STACK_ALL | 165 | 0.6727 | 0.6162 | 0.2061 | 0.5993 | 38 |
| 2026 | RESID_NONE | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6397 | 35 |
| 2026 | RESID_TRK | 165 | 0.6970 | 0.6141 | 0.2303 | 0.6339 | 36 |
| 2026 | RESID_OPP | 165 | 0.6788 | 0.6141 | 0.2182 | 0.6378 | 35 |
| 2026 | RESID_MU | 165 | 0.6667 | 0.6081 | 0.2182 | 0.6401 | 37 |
| 2026 | RESID_ALL | 165 | 0.6727 | 0.6242 | 0.2303 | 0.6257 | 36 |
| 2026 | RESID_NONE raw | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6642 | 35 |
| 2026 | RESID_TRK raw | 165 | 0.6970 | 0.6141 | 0.2303 | 0.6616 | 36 |
| 2026 | RESID_OPP raw | 165 | 0.6788 | 0.6141 | 0.2182 | 0.6624 | 35 |
| 2026 | RESID_MU raw | 165 | 0.6667 | 0.6081 | 0.2182 | 0.6649 | 37 |
| 2026 | RESID_ALL raw | 165 | 0.6727 | 0.6242 | 0.2303 | 0.6577 | 36 |
| 2026 | BLEND_REF_ALL | 165 | 0.6970 | 0.6101 | 0.2061 | 0.6398 | 34 |
| all | A | 329 | 0.7356 | 0.6606 | 0.3040 | 0.6895 | 41 |
| all | REF | 329 | 0.7477 | 0.6484 | 0.2766 | 0.7013 | 46 |
| all | BASE | 329 | 0.7325 | 0.6454 | 0.3009 | 0.6831 | 47 |
| all | BASE+TRK | 329 | 0.7447 | 0.6474 | 0.2766 | 0.6662 | 44 |
| all | BASE+OPP | 329 | 0.7386 | 0.6403 | 0.2827 | 0.6622 | 45 |
| all | BASE+MU | 329 | 0.7264 | 0.6363 | 0.2827 | 0.6785 | 44 |
| all | BASE+ALL | 329 | 0.7264 | 0.6373 | 0.2584 | 0.6547 | 45 |
| all | STACK_BASE | 329 | 0.7264 | 0.6282 | 0.2401 | 0.6519 | 48 |
| all | STACK_ALL | 329 | 0.7416 | 0.6636 | 0.2948 | 0.6521 | 48 |
| all | RESID_NONE | 329 | 0.7508 | 0.6535 | 0.2796 | 0.6673 | 47 |
| all | RESID_TRK | 329 | 0.7568 | 0.6575 | 0.2918 | 0.6723 | 48 |
| all | RESID_OPP | 329 | 0.7599 | 0.6565 | 0.2948 | 0.6680 | 47 |
| all | RESID_MU | 329 | 0.7477 | 0.6525 | 0.2888 | 0.6668 | 48 |
| all | RESID_ALL | 329 | 0.7629 | 0.6606 | 0.2918 | 0.6677 | 47 |
| all | RESID_NONE raw | 329 | 0.7508 | 0.6535 | 0.2796 | 0.7015 | 47 |
| all | RESID_TRK raw | 329 | 0.7568 | 0.6575 | 0.2918 | 0.7089 | 48 |
| all | RESID_OPP raw | 329 | 0.7599 | 0.6565 | 0.2948 | 0.7031 | 47 |
| all | RESID_MU raw | 329 | 0.7477 | 0.6525 | 0.2888 | 0.7016 | 48 |
| all | RESID_ALL raw | 329 | 0.7629 | 0.6606 | 0.2918 | 0.7102 | 47 |
| all | BLEND_REF_ALL | 329 | 0.7720 | 0.6596 | 0.2918 | 0.6770 | 45 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | REF | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4216 | 0.3686 | 0.4614 | 0.0928 | 0.1783 |
| 2025 | BASE+TRK | 491 | 0.3890 | 0.3525 | 0.4559 | 0.1035 | 0.1183 |
| 2025 | BASE+OPP | 491 | 0.3931 | 0.3494 | 0.4510 | 0.1016 | 0.1396 |
| 2025 | BASE+MU | 491 | 0.4033 | 0.3678 | 0.4636 | 0.0958 | 0.1258 |
| 2025 | BASE+ALL | 491 | 0.3890 | 0.3384 | 0.4480 | 0.1097 | 0.1615 |
| 2025 | STACK_BASE | 491 | 0.4277 | 0.4044 | 0.4500 | 0.0457 | 0.0804 |
| 2025 | STACK_ALL | 491 | 0.4216 | 0.3619 | 0.4756 | 0.1137 | 0.2265 |
| 2025 | RESID_NONE | 491 | 0.4094 | 0.3715 | 0.4415 | 0.0700 | 0.1835 |
| 2025 | RESID_TRK | 491 | 0.3870 | 0.3591 | 0.4448 | 0.0857 | 0.1246 |
| 2025 | RESID_OPP | 491 | 0.4175 | 0.3654 | 0.4404 | 0.0750 | 0.2066 |
| 2025 | RESID_MU | 491 | 0.4073 | 0.3667 | 0.4377 | 0.0711 | 0.1799 |
| 2025 | RESID_ALL | 491 | 0.4073 | 0.3576 | 0.4527 | 0.0951 | 0.2250 |
| 2025 | RESID_NONE raw | 491 | 0.4297 | 0.4055 | 0.5004 | 0.0950 | 0.1191 |
| 2025 | RESID_TRK raw | 491 | 0.4094 | 0.3974 | 0.5126 | 0.1152 | 0.0765 |
| 2025 | RESID_OPP raw | 491 | 0.4358 | 0.3994 | 0.5027 | 0.1033 | 0.1543 |
| 2025 | RESID_MU raw | 491 | 0.4297 | 0.3987 | 0.4956 | 0.0969 | 0.1387 |
| 2025 | RESID_ALL raw | 491 | 0.4196 | 0.3859 | 0.5187 | 0.1329 | 0.1626 |
| 2025 | BLEND_REF_ALL | 491 | 0.4155 | 0.3549 | 0.4400 | 0.0851 | 0.2211 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | REF | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4263 | 0.3732 | 0.4518 | 0.0786 | 0.1891 |
| 2026 | BASE+TRK | 495 | 0.3980 | 0.3662 | 0.4118 | 0.0456 | 0.1180 |
| 2026 | BASE+OPP | 495 | 0.3980 | 0.3661 | 0.4199 | 0.0538 | 0.1091 |
| 2026 | BASE+MU | 495 | 0.3758 | 0.3564 | 0.4336 | 0.0772 | 0.0793 |
| 2026 | BASE+ALL | 495 | 0.3960 | 0.3519 | 0.3976 | 0.0457 | 0.1726 |
| 2026 | STACK_BASE | 495 | 0.4000 | 0.3710 | 0.4801 | 0.1090 | 0.1484 |
| 2026 | STACK_ALL | 495 | 0.3939 | 0.3364 | 0.3964 | 0.0600 | 0.1971 |
| 2026 | RESID_NONE | 495 | 0.4263 | 0.3638 | 0.4389 | 0.0752 | 0.2441 |
| 2026 | RESID_TRK | 495 | 0.4182 | 0.3584 | 0.4294 | 0.0710 | 0.2473 |
| 2026 | RESID_OPP | 495 | 0.4323 | 0.3607 | 0.4344 | 0.0737 | 0.2696 |
| 2026 | RESID_MU | 495 | 0.4343 | 0.3630 | 0.4388 | 0.0759 | 0.2718 |
| 2026 | RESID_ALL | 495 | 0.4141 | 0.3544 | 0.4189 | 0.0644 | 0.2291 |
| 2026 | RESID_NONE raw | 495 | 0.4424 | 0.3878 | 0.4777 | 0.0899 | 0.1996 |
| 2026 | RESID_TRK raw | 495 | 0.4444 | 0.3865 | 0.4751 | 0.0886 | 0.2152 |
| 2026 | RESID_OPP raw | 495 | 0.4404 | 0.3853 | 0.4739 | 0.0886 | 0.2165 |
| 2026 | RESID_MU raw | 495 | 0.4485 | 0.3868 | 0.4777 | 0.0909 | 0.2280 |
| 2026 | RESID_ALL raw | 495 | 0.4343 | 0.3817 | 0.4675 | 0.0858 | 0.1951 |
| 2026 | BLEND_REF_ALL | 495 | 0.4364 | 0.3741 | 0.4337 | 0.0596 | 0.2228 |
| all | A | 986 | 0.2049 | 0.2248 | 0.2081 | -0.0167 | -0.0864 |
| all | REF | 986 | 0.4371 | 0.3958 | 0.4888 | 0.0930 | 0.1662 |
| all | BASE | 986 | 0.4239 | 0.3709 | 0.4566 | 0.0856 | 0.1837 |
| all | BASE+TRK | 986 | 0.3935 | 0.3594 | 0.4338 | 0.0744 | 0.1182 |
| all | BASE+OPP | 986 | 0.3955 | 0.3578 | 0.4353 | 0.0776 | 0.1243 |
| all | BASE+MU | 986 | 0.3895 | 0.3621 | 0.4485 | 0.0865 | 0.1025 |
| all | BASE+ALL | 986 | 0.3925 | 0.3452 | 0.4227 | 0.0775 | 0.1670 |
| all | STACK_BASE | 986 | 0.4138 | 0.3876 | 0.4651 | 0.0775 | 0.1146 |
| all | STACK_ALL | 986 | 0.4077 | 0.3491 | 0.4358 | 0.0867 | 0.2117 |
| all | RESID_NONE | 986 | 0.4178 | 0.3676 | 0.4402 | 0.0726 | 0.2139 |
| all | RESID_TRK | 986 | 0.4026 | 0.3588 | 0.4371 | 0.0783 | 0.1862 |
| all | RESID_OPP | 986 | 0.4249 | 0.3631 | 0.4374 | 0.0744 | 0.2382 |
| all | RESID_MU | 986 | 0.4209 | 0.3648 | 0.4383 | 0.0735 | 0.2260 |
| all | RESID_ALL | 986 | 0.4108 | 0.3560 | 0.4357 | 0.0797 | 0.2270 |
| all | RESID_NONE raw | 986 | 0.4361 | 0.3966 | 0.4890 | 0.0924 | 0.1595 |
| all | RESID_TRK raw | 986 | 0.4270 | 0.3919 | 0.4938 | 0.1019 | 0.1461 |
| all | RESID_OPP raw | 986 | 0.4381 | 0.3924 | 0.4883 | 0.0959 | 0.1855 |
| all | RESID_MU raw | 986 | 0.4391 | 0.3927 | 0.4866 | 0.0939 | 0.1835 |
| all | RESID_ALL raw | 986 | 0.4270 | 0.3838 | 0.4930 | 0.1092 | 0.1790 |
| all | BLEND_REF_ALL | 986 | 0.4260 | 0.3645 | 0.4368 | 0.0723 | 0.2219 |

## Disagreement buckets (model minus comparison, calibrated)
| model | vs | bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|---|---|
| p_BASE+ALL_cal | p_BASE_cal | < -0.05 | 2259 | 0.3715 | 0.2929 | 0.3351 |
| p_BASE+ALL_cal | p_BASE_cal | [-0.05, 0.05] | 47789 | 0.0683 | 0.0678 | 0.0620 |
| p_BASE+ALL_cal | p_BASE_cal | > 0.05 | 1730 | 0.2253 | 0.3030 | 0.2503 |
| p_RESID_ALL_raw | p_REF_cal | < -0.05 | 148 | 0.4074 | 0.3433 | 0.3581 |
| p_RESID_ALL_raw | p_REF_cal | [-0.05, 0.05] | 50519 | 0.0761 | 0.0770 | 0.0733 |
| p_RESID_ALL_raw | p_REF_cal | > 0.05 | 1111 | 0.3460 | 0.4238 | 0.3591 |
| p_STACK_ALL_cal | p_REF_cal | < -0.05 | 2715 | 0.3911 | 0.3057 | 0.3606 |
| p_STACK_ALL_cal | p_REF_cal | [-0.05, 0.05] | 47313 | 0.0587 | 0.0620 | 0.0561 |
| p_STACK_ALL_cal | p_REF_cal | > 0.05 | 1750 | 0.2581 | 0.3352 | 0.2971 |
| p_BASE+TRK_cal | p_BASE_cal | < -0.05 | 2120 | 0.3313 | 0.2548 | 0.2943 |
| p_BASE+TRK_cal | p_BASE_cal | [-0.05, 0.05] | 48440 | 0.0722 | 0.0708 | 0.0663 |
| p_BASE+TRK_cal | p_BASE_cal | > 0.05 | 1218 | 0.2421 | 0.3136 | 0.2603 |
| p_BASE+OPP_cal | p_BASE_cal | < -0.05 | 1399 | 0.3998 | 0.3238 | 0.3674 |
| p_BASE+OPP_cal | p_BASE_cal | [-0.05, 0.05] | 49366 | 0.0743 | 0.0740 | 0.0680 |
| p_BASE+OPP_cal | p_BASE_cal | > 0.05 | 1013 | 0.2629 | 0.3336 | 0.2774 |
| p_BASE+MU_cal | p_BASE_cal | < -0.05 | 827 | 0.3938 | 0.3253 | 0.3567 |
| p_BASE+MU_cal | p_BASE_cal | [-0.05, 0.05] | 50043 | 0.0776 | 0.0772 | 0.0712 |
| p_BASE+MU_cal | p_BASE_cal | > 0.05 | 908 | 0.3145 | 0.3834 | 0.3238 |

## Gain share by feature group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+TRK | 2025 | BASE | 0.8765 | 155 |
| BASE+TRK | 2025 | TRK | 0.1235 | 59 |
| BASE+OPP | 2025 | BASE | 0.9196 | 155 |
| BASE+OPP | 2025 | OPP | 0.0804 | 35 |
| BASE+MU | 2025 | BASE | 0.9527 | 155 |
| BASE+MU | 2025 | MU | 0.0473 | 21 |
| BASE+ALL | 2025 | BASE | 0.7611 | 155 |
| BASE+ALL | 2025 | MU | 0.0414 | 21 |
| BASE+ALL | 2025 | OPP | 0.0798 | 35 |
| BASE+ALL | 2025 | TRK | 0.1177 | 59 |
| STACK_BASE | 2025 | BASE | 0.6699 | 2 |
| STACK_BASE | 2025 | REF | 0.3301 | 1 |
| STACK_ALL | 2025 | BASE | 0.0339 | 2 |
| STACK_ALL | 2025 | MU | 0.0445 | 21 |
| STACK_ALL | 2025 | OPP | 0.0630 | 35 |
| STACK_ALL | 2025 | REF | 0.5680 | 1 |
| STACK_ALL | 2025 | TRK | 0.2907 | 59 |
| RESID_NONE | 2025 | BASE | 1.0000 | 2 |
| RESID_TRK | 2025 | BASE | 0.0216 | 2 |
| RESID_TRK | 2025 | TRK | 0.9784 | 59 |
| RESID_OPP | 2025 | BASE | 0.0282 | 2 |
| RESID_OPP | 2025 | OPP | 0.9718 | 35 |
| RESID_MU | 2025 | BASE | 0.0452 | 2 |
| RESID_MU | 2025 | MU | 0.9548 | 21 |
| RESID_ALL | 2025 | BASE | 0.0062 | 2 |
| RESID_ALL | 2025 | MU | 0.1837 | 21 |
| RESID_ALL | 2025 | OPP | 0.3636 | 35 |
| RESID_ALL | 2025 | TRK | 0.4465 | 59 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+TRK | 2026 | BASE | 0.8804 | 155 |
| BASE+TRK | 2026 | TRK | 0.1196 | 59 |
| BASE+OPP | 2026 | BASE | 0.9055 | 155 |
| BASE+OPP | 2026 | OPP | 0.0945 | 35 |
| BASE+MU | 2026 | BASE | 0.9350 | 155 |
| BASE+MU | 2026 | MU | 0.0650 | 21 |
| BASE+ALL | 2026 | BASE | 0.8484 | 155 |
| BASE+ALL | 2026 | MU | 0.0230 | 21 |
| BASE+ALL | 2026 | OPP | 0.0416 | 35 |
| BASE+ALL | 2026 | TRK | 0.0869 | 59 |
| STACK_BASE | 2026 | BASE | 0.6429 | 2 |
| STACK_BASE | 2026 | REF | 0.3571 | 1 |
| STACK_ALL | 2026 | BASE | 0.0190 | 2 |
| STACK_ALL | 2026 | MU | 0.0256 | 21 |
| STACK_ALL | 2026 | OPP | 0.0305 | 35 |
| STACK_ALL | 2026 | REF | 0.6353 | 1 |
| STACK_ALL | 2026 | TRK | 0.2896 | 59 |
| RESID_NONE | 2026 | BASE | 1.0000 | 2 |
| RESID_TRK | 2026 | BASE | 0.0158 | 2 |
| RESID_TRK | 2026 | TRK | 0.9842 | 59 |
| RESID_OPP | 2026 | BASE | 0.0307 | 2 |
| RESID_OPP | 2026 | OPP | 0.9693 | 35 |
| RESID_MU | 2026 | BASE | 0.0731 | 2 |
| RESID_MU | 2026 | MU | 0.9269 | 21 |
| RESID_ALL | 2026 | BASE | 0.0109 | 2 |
| RESID_ALL | 2026 | MU | 0.1843 | 21 |
| RESID_ALL | 2026 | OPP | 0.3402 | 35 |
| RESID_ALL | 2026 | TRK | 0.4646 | 59 |

## Top 30 features by gain share (BASE+ALL, STACK_ALL and RESID_ALL)
| model | season | rank | feature | group | gain_share |
|---|---|---|---|---|---|
| BASE+ALL | 2025 | 1 | dd_rate_ewm | BASE | 0.33757 |
| BASE+ALL | 2025 | 2 | dd_rate_l20 | BASE | 0.08096 |
| BASE+ALL | 2025 | 3 | dd_rate_szn | BASE | 0.04583 |
| BASE+ALL | 2025 | 4 | prev_dd_rate | BASE | 0.03370 |
| BASE+ALL | 2025 | 5 | reb_ewm | BASE | 0.01611 |
| BASE+ALL | 2025 | 6 | reb_l20 | BASE | 0.01475 |
| BASE+ALL | 2025 | 7 | trk_potast_pg_ewm | TRK | 0.01171 |
| BASE+ALL | 2025 | 8 | dd_rate_l10 | BASE | 0.01000 |
| BASE+ALL | 2025 | 9 | trk_rebch_pg_ewm | TRK | 0.00729 |
| BASE+ALL | 2025 | 10 | reb_l10 | BASE | 0.00662 |
| BASE+ALL | 2025 | 11 | abs_absent_rebounds_pg | BASE | 0.00571 |
| BASE+ALL | 2025 | 12 | oppt_al_rebcon_share_l20 | OPP | 0.00501 |
| BASE+ALL | 2025 | 13 | trk_rebdist_l10 | TRK | 0.00464 |
| BASE+ALL | 2025 | 14 | reb8_rate_szn | BASE | 0.00460 |
| BASE+ALL | 2025 | 15 | mu_h2h_pts100 | MU | 0.00453 |
| BASE+ALL | 2025 | 16 | reb8_rate_ewm | BASE | 0.00445 |
| BASE+ALL | 2025 | 17 | reb_szn | BASE | 0.00438 |
| BASE+ALL | 2025 | 18 | oppt_al_rebch_conv_l10 | OPP | 0.00417 |
| BASE+ALL | 2025 | 19 | min_trend | BASE | 0.00416 |
| BASE+ALL | 2025 | 20 | fta_szn | BASE | 0.00415 |
| BASE+ALL | 2025 | 21 | oppt_contested_l10 | OPP | 0.00407 |
| BASE+ALL | 2025 | 22 | team_reb_share_l20 | BASE | 0.00406 |
| BASE+ALL | 2025 | 23 | trk_loose_pm_l10 | TRK | 0.00403 |
| BASE+ALL | 2025 | 24 | opp_allow_pts_szn | BASE | 0.00396 |
| BASE+ALL | 2025 | 25 | mu_off_fit | MU | 0.00388 |
| BASE+ALL | 2025 | 26 | last_starter | BASE | 0.00374 |
| BASE+ALL | 2025 | 27 | min_l5 | BASE | 0.00370 |
| BASE+ALL | 2025 | 28 | ast_l10 | BASE | 0.00363 |
| BASE+ALL | 2025 | 29 | trk_loose_pm_ewm | TRK | 0.00360 |
| BASE+ALL | 2025 | 30 | oppt_al_rebch_conv_l20 | OPP | 0.00339 |
| STACK_ALL | 2025 | 1 | z_ref | REF | 0.56798 |
| STACK_ALL | 2025 | 2 | trk_rebch_pg_ewm | TRK | 0.12745 |
| STACK_ALL | 2025 | 3 | min_ewm | BASE | 0.03366 |
| STACK_ALL | 2025 | 4 | exp_rebch | TRK | 0.02027 |
| STACK_ALL | 2025 | 5 | trk_potast_pg_ewm | TRK | 0.01853 |
| STACK_ALL | 2025 | 6 | trk_rebch_last | TRK | 0.01166 |
| STACK_ALL | 2025 | 7 | exp_potast | TRK | 0.00924 |
| STACK_ALL | 2025 | 8 | trk_drebch_pm_ewm | TRK | 0.00794 |
| STACK_ALL | 2025 | 9 | trk_rebdist_l10 | TRK | 0.00598 |
| STACK_ALL | 2025 | 10 | mu_off_pts100 | MU | 0.00550 |
| STACK_ALL | 2025 | 11 | trk_min_ewm | TRK | 0.00499 |
| STACK_ALL | 2025 | 12 | trk_rebch_conv_ewm | TRK | 0.00493 |
| STACK_ALL | 2025 | 13 | oppt_al_rebcon_share_l20 | OPP | 0.00473 |
| STACK_ALL | 2025 | 14 | mu_def_pos_F | MU | 0.00406 |
| STACK_ALL | 2025 | 15 | mu_off_fit | MU | 0.00387 |
| STACK_ALL | 2025 | 16 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.00360 |
| STACK_ALL | 2025 | 17 | trk_rebch_conv_l20 | TRK | 0.00327 |
| STACK_ALL | 2025 | 18 | oppx_ast36_allowed_pos_l20 | OPP | 0.00313 |
| STACK_ALL | 2025 | 19 | trk_passes_pm_l10 | TRK | 0.00304 |
| STACK_ALL | 2025 | 20 | trk_loose_pm_l10 | TRK | 0.00302 |
| STACK_ALL | 2025 | 21 | oppt_contested_l10 | OPP | 0.00300 |
| STACK_ALL | 2025 | 22 | trk_loose_pm_ewm | TRK | 0.00290 |
| STACK_ALL | 2025 | 23 | oppt_al_potast_l20 | OPP | 0.00271 |
| STACK_ALL | 2025 | 24 | oppt_al_passes_l20 | OPP | 0.00270 |
| STACK_ALL | 2025 | 25 | oppt_al_rebch_conv_l10 | OPP | 0.00265 |
| STACK_ALL | 2025 | 26 | trk_passes_pm_ewm | TRK | 0.00263 |
| STACK_ALL | 2025 | 27 | trk_screenast_pm_ewm | TRK | 0.00259 |
| STACK_ALL | 2025 | 28 | oppt_deflect_l20 | OPP | 0.00257 |
| STACK_ALL | 2025 | 29 | trk_rebdefer_pm_ewm | TRK | 0.00256 |
| STACK_ALL | 2025 | 30 | trk_boxouts_pm_l10 | TRK | 0.00255 |
| RESID_ALL | 2025 | 1 | oppt_al_rebcon_share_l20 | OPP | 0.03296 |
| RESID_ALL | 2025 | 2 | oppx_ast36_allowed_pos_l20 | OPP | 0.02874 |
| RESID_ALL | 2025 | 3 | oppt_al_rebch_conv_l10 | OPP | 0.02242 |
| RESID_ALL | 2025 | 4 | trk_rebdefer_pm_ewm | TRK | 0.02122 |
| RESID_ALL | 2025 | 5 | trk_rebdist_l10 | TRK | 0.01976 |
| RESID_ALL | 2025 | 6 | trk_screenast_pm_ewm | TRK | 0.01967 |
| RESID_ALL | 2025 | 7 | mu_h2h_ast100 | MU | 0.01961 |
| RESID_ALL | 2025 | 8 | trk_loose_pm_ewm | TRK | 0.01849 |
| RESID_ALL | 2025 | 9 | oppt_al_ast_conv_l10 | OPP | 0.01751 |
| RESID_ALL | 2025 | 10 | trk_rebch_conv_l5 | TRK | 0.01750 |
| RESID_ALL | 2025 | 11 | trk_potast_pm_ewm | TRK | 0.01718 |
| RESID_ALL | 2025 | 12 | oppx_dd_allowed_pos_l20 | OPP | 0.01602 |
| RESID_ALL | 2025 | 13 | oppt_al_potast_l20 | OPP | 0.01602 |
| RESID_ALL | 2025 | 14 | oppt_contested_l10 | OPP | 0.01585 |
| RESID_ALL | 2025 | 15 | trk_loose_pm_l10 | TRK | 0.01538 |
| RESID_ALL | 2025 | 16 | mu_def_pos_C | MU | 0.01513 |
| RESID_ALL | 2025 | 17 | trk_rebch_last | TRK | 0.01503 |
| RESID_ALL | 2025 | 18 | trk_rebch_conv_ewm | TRK | 0.01491 |
| RESID_ALL | 2025 | 19 | oppx_pts36_allowed_pos_l20 | OPP | 0.01415 |
| RESID_ALL | 2025 | 20 | mu_def_ast_vs_exp | MU | 0.01375 |
| RESID_ALL | 2025 | 21 | oppt_contested_l20 | OPP | 0.01341 |
| RESID_ALL | 2025 | 22 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.01287 |
| RESID_ALL | 2025 | 23 | mu_h2h_pts100 | MU | 0.01213 |
| RESID_ALL | 2025 | 24 | oppt_al_rebch_conv_l20 | OPP | 0.01210 |
| RESID_ALL | 2025 | 25 | oppx_pts_allowed_pos_rel_l20 | OPP | 0.01187 |
| RESID_ALL | 2025 | 26 | oppt_al_passes_l20 | OPP | 0.01164 |
| RESID_ALL | 2025 | 27 | mu_h2h_poss | MU | 0.01147 |
| RESID_ALL | 2025 | 28 | mu_def_defbox_pm | MU | 0.01130 |
| RESID_ALL | 2025 | 29 | mu_def_pos_F | MU | 0.01126 |
| RESID_ALL | 2025 | 30 | trk_screenast_pm_l10 | TRK | 0.01102 |
| BASE+ALL | 2026 | 1 | dd_rate_ewm | BASE | 0.41791 |
| BASE+ALL | 2026 | 2 | dd_rate_l20 | BASE | 0.11325 |
| BASE+ALL | 2026 | 3 | dd_rate_szn | BASE | 0.04687 |
| BASE+ALL | 2026 | 4 | prev_dd_rate | BASE | 0.04432 |
| BASE+ALL | 2026 | 5 | reb_ewm | BASE | 0.01995 |
| BASE+ALL | 2026 | 6 | dd_rate_l10 | BASE | 0.01827 |
| BASE+ALL | 2026 | 7 | reb_l10 | BASE | 0.01771 |
| BASE+ALL | 2026 | 8 | trk_rebch_pg_ewm | TRK | 0.01602 |
| BASE+ALL | 2026 | 9 | last_starter | BASE | 0.00755 |
| BASE+ALL | 2026 | 10 | trk_potast_pg_ewm | TRK | 0.00728 |
| BASE+ALL | 2026 | 11 | reb_szn | BASE | 0.00630 |
| BASE+ALL | 2026 | 12 | abs_absent_rebounds_pg | BASE | 0.00615 |
| BASE+ALL | 2026 | 13 | abs_absent_assists_pg | BASE | 0.00487 |
| BASE+ALL | 2026 | 14 | last_min | BASE | 0.00476 |
| BASE+ALL | 2026 | 15 | ast_ewm | BASE | 0.00430 |
| BASE+ALL | 2026 | 16 | reb8_rate_szn | BASE | 0.00407 |
| BASE+ALL | 2026 | 17 | abs_absent_points_pg | BASE | 0.00379 |
| BASE+ALL | 2026 | 18 | min_trend | BASE | 0.00332 |
| BASE+ALL | 2026 | 19 | opp_allow_reb_l20 | BASE | 0.00323 |
| BASE+ALL | 2026 | 20 | trk_rebch_last | TRK | 0.00319 |
| BASE+ALL | 2026 | 21 | oppt_al_rebcon_share_l20 | OPP | 0.00309 |
| BASE+ALL | 2026 | 22 | trk_rebdist_l10 | TRK | 0.00301 |
| BASE+ALL | 2026 | 23 | opp_allow_pts_szn | BASE | 0.00279 |
| BASE+ALL | 2026 | 24 | exp_potast | TRK | 0.00274 |
| BASE+ALL | 2026 | 25 | min_l5 | BASE | 0.00260 |
| BASE+ALL | 2026 | 26 | ast_szn | BASE | 0.00255 |
| BASE+ALL | 2026 | 27 | pts_pm_szn | BASE | 0.00254 |
| BASE+ALL | 2026 | 28 | reb_l20 | BASE | 0.00252 |
| BASE+ALL | 2026 | 29 | trk_passes_pm_l10 | TRK | 0.00249 |
| BASE+ALL | 2026 | 30 | abs_absent_minutes_share | BASE | 0.00242 |
| STACK_ALL | 2026 | 1 | z_ref | REF | 0.63533 |
| STACK_ALL | 2026 | 2 | trk_rebch_pg_ewm | TRK | 0.12800 |
| STACK_ALL | 2026 | 3 | exp_rebch | TRK | 0.04674 |
| STACK_ALL | 2026 | 4 | exp_potast | TRK | 0.02155 |
| STACK_ALL | 2026 | 5 | trk_potast_pg_ewm | TRK | 0.01959 |
| STACK_ALL | 2026 | 6 | min_ewm | BASE | 0.01883 |
| STACK_ALL | 2026 | 7 | trk_rebch_last | TRK | 0.01290 |
| STACK_ALL | 2026 | 8 | trk_min_ewm | TRK | 0.00536 |
| STACK_ALL | 2026 | 9 | mu_off_ast100 | MU | 0.00445 |
| STACK_ALL | 2026 | 10 | trk_potast_last | TRK | 0.00391 |
| STACK_ALL | 2026 | 11 | trk_rebch_conv_ewm | TRK | 0.00390 |
| STACK_ALL | 2026 | 12 | mu_off_pts100 | MU | 0.00374 |
| STACK_ALL | 2026 | 13 | trk_drebch_pm_l10 | TRK | 0.00338 |
| STACK_ALL | 2026 | 14 | trk_drebch_pm_ewm | TRK | 0.00337 |
| STACK_ALL | 2026 | 15 | trk_rebdist_l10 | TRK | 0.00250 |
| STACK_ALL | 2026 | 16 | trk_passes_pm_l10 | TRK | 0.00247 |
| STACK_ALL | 2026 | 17 | oppt_al_rebcon_share_l20 | OPP | 0.00244 |
| STACK_ALL | 2026 | 18 | trk_rebch_conv_l20 | TRK | 0.00237 |
| STACK_ALL | 2026 | 19 | mu_h2h_pts100 | MU | 0.00222 |
| STACK_ALL | 2026 | 20 | trk_ast_conv_l20 | TRK | 0.00200 |
| STACK_ALL | 2026 | 21 | oppt_al_potast_l20 | OPP | 0.00191 |
| STACK_ALL | 2026 | 22 | oppx_pts36_allowed_pos_l20 | OPP | 0.00191 |
| STACK_ALL | 2026 | 23 | mu_off_fit | MU | 0.00180 |
| STACK_ALL | 2026 | 24 | oppt_deflect_l20 | OPP | 0.00176 |
| STACK_ALL | 2026 | 25 | trk_rebch_pm_l10 | TRK | 0.00169 |
| STACK_ALL | 2026 | 26 | trk_passes_pm_ewm | TRK | 0.00167 |
| STACK_ALL | 2026 | 27 | oppt_al_ast_conv_l10 | OPP | 0.00167 |
| STACK_ALL | 2026 | 28 | oppx_ast_allowed_pos_rel_l20 | OPP | 0.00162 |
| STACK_ALL | 2026 | 29 | mu_best_def_vs_pos | MU | 0.00156 |
| STACK_ALL | 2026 | 30 | trk_rebch_pm_l20 | TRK | 0.00154 |
| RESID_ALL | 2026 | 1 | trk_rebch_conv_l20 | TRK | 0.08430 |
| RESID_ALL | 2026 | 2 | oppt_al_rebcon_share_l20 | OPP | 0.04420 |
| RESID_ALL | 2026 | 3 | oppt_al_passes_l20 | OPP | 0.03691 |
| RESID_ALL | 2026 | 4 | trk_rebch_conv_l5 | TRK | 0.03460 |
| RESID_ALL | 2026 | 5 | trk_astpts_pm_l10 | TRK | 0.02875 |
| RESID_ALL | 2026 | 6 | mu_def_pos_C | MU | 0.02770 |
| RESID_ALL | 2026 | 7 | oppx_pts36_allowed_pos_l20 | OPP | 0.02761 |
| RESID_ALL | 2026 | 8 | oppt_al_potast_l20 | OPP | 0.02422 |
| RESID_ALL | 2026 | 9 | oppt_al_ast_conv_l10 | OPP | 0.02233 |
| RESID_ALL | 2026 | 10 | trk_passes_pm_l5 | TRK | 0.01978 |
| RESID_ALL | 2026 | 11 | oppx_pts_allowed_pos_l10 | OPP | 0.01841 |
| RESID_ALL | 2026 | 12 | mu_off_ast100 | MU | 0.01775 |
| RESID_ALL | 2026 | 13 | trk_passes_pm_l10 | TRK | 0.01744 |
| RESID_ALL | 2026 | 14 | mu_def_ast_vs_exp | MU | 0.01723 |
| RESID_ALL | 2026 | 15 | oppt_deflect_l20 | OPP | 0.01714 |
| RESID_ALL | 2026 | 16 | mu_h2h_pts100 | MU | 0.01672 |
| RESID_ALL | 2026 | 17 | trk_ast_conv_l20 | TRK | 0.01632 |
| RESID_ALL | 2026 | 18 | oppx_ast_allowed_pos_l10 | OPP | 0.01613 |
| RESID_ALL | 2026 | 19 | trk_screenast_pm_ewm | TRK | 0.01611 |
| RESID_ALL | 2026 | 20 | mu_h2h_ast100 | MU | 0.01546 |
| RESID_ALL | 2026 | 21 | mu_def_defbox_pm | MU | 0.01504 |
| RESID_ALL | 2026 | 22 | oppt_al_rebch_conv_l20 | OPP | 0.01493 |
| RESID_ALL | 2026 | 23 | oppt_contested_l20 | OPP | 0.01443 |
| RESID_ALL | 2026 | 24 | oppt_al_potast_l10 | OPP | 0.01359 |
| RESID_ALL | 2026 | 25 | trk_rebdist_l10 | TRK | 0.01335 |
| RESID_ALL | 2026 | 26 | trk_astpts_pm_ewm | TRK | 0.01261 |
| RESID_ALL | 2026 | 27 | trk_boxouts_pm_l20 | TRK | 0.01201 |
| RESID_ALL | 2026 | 28 | trk_games_prior | TRK | 0.01174 |
| RESID_ALL | 2026 | 29 | oppt_deflect_l10 | OPP | 0.01153 |
| RESID_ALL | 2026 | 30 | mu_off_defby_C | MU | 0.01147 |

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
    "BASE+MU_best_iteration": 103,
    "BASE+MU_holdout_logloss": 0.21020869102964881,
    "BASE+ALL_best_iteration": 192,
    "BASE+ALL_holdout_logloss": 0.209814419230493,
    "STACK_BASE_best_iteration": 544,
    "STACK_BASE_holdout_logloss": 0.2108647093254539,
    "STACK_ALL_best_iteration": 148,
    "STACK_ALL_holdout_logloss": 0.20356907902449864,
    "RESID_NONE_best_iteration": 7,
    "RESID_NONE_holdout_logloss": 0.20318533302391203,
    "RESID_TRK_best_iteration": 90,
    "RESID_TRK_holdout_logloss": 0.20241765555955307,
    "RESID_OPP_best_iteration": 11,
    "RESID_OPP_holdout_logloss": 0.20300775894496234,
    "RESID_MU_best_iteration": 15,
    "RESID_MU_holdout_logloss": 0.20281119349480395,
    "RESID_ALL_best_iteration": 89,
    "RESID_ALL_holdout_logloss": 0.20269295745499066
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
    "BASE+MU_best_iteration": 283,
    "BASE+MU_holdout_logloss": 0.20742543813216519,
    "BASE+ALL_best_iteration": 148,
    "BASE+ALL_holdout_logloss": 0.20900247982228606,
    "STACK_BASE_best_iteration": 768,
    "STACK_BASE_holdout_logloss": 0.20751908512946754,
    "STACK_ALL_best_iteration": 120,
    "STACK_ALL_holdout_logloss": 0.20624936172704142,
    "RESID_NONE_best_iteration": 2,
    "RESID_NONE_holdout_logloss": 0.20659804174081567,
    "RESID_TRK_best_iteration": 5,
    "RESID_TRK_holdout_logloss": 0.20652986212248534,
    "RESID_OPP_best_iteration": 4,
    "RESID_OPP_holdout_logloss": 0.2065552213497972,
    "RESID_MU_best_iteration": 3,
    "RESID_MU_holdout_logloss": 0.20665708743502137,
    "RESID_ALL_best_iteration": 17,
    "RESID_ALL_holdout_logloss": 0.20645710773767917
  }
}
```
