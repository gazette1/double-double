# GAMESTATE feature lift test (full history)

v1 rows, features and folds (test 2022-23 through 2025-26, trained on every earlier season back to 2017-18, all season types; metrics on regular-season test rows). BASE is the 155 v1 features with Platt calibration; BASE+GAMESTATE adds 6 features from `gamestate_features.parquet` merged on ['game_id', 'team_id']. Same rows, hyperparameters, seed, holdout and calibration, so the difference comes from the features alone. V1_isotonic is the saved v1 prediction for scale.

## Coverage of the new features (mean non-null share) by season
| season | mean_non_null |
|---|---|
| 2018 | 1.0000 |
| 2019 | 1.0000 |
| 2020 | 1.0000 |
| 2021 | 1.0000 |
| 2022 | 1.0000 |
| 2023 | 1.0000 |
| 2024 | 1.0000 |
| 2025 | 1.0000 |
| 2026 | 1.0000 |
| 2027 | 1.0000 |

## Calibrated log loss, Brier, AUC
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2023 | A | 25411 | 0.0849 | 0.0893 | 0.2058 | 0.0588 | 0.8694 |
| 2023 | V1_isotonic | 25411 | 0.0849 | 0.0867 | 0.1948 | 0.0574 | 0.8946 |
| 2023 | BASE | 25411 | 0.0849 | 0.0866 | 0.1940 | 0.0574 | 0.8950 |
| 2023 | BASE+GAMESTATE | 25411 | 0.0849 | 0.0868 | 0.1937 | 0.0573 | 0.8953 |
| 2024 | A | 25820 | 0.0869 | 0.0858 | 0.2000 | 0.0565 | 0.8793 |
| 2024 | V1_isotonic | 25820 | 0.0869 | 0.0845 | 0.1907 | 0.0552 | 0.8990 |
| 2024 | BASE | 25820 | 0.0869 | 0.0843 | 0.1900 | 0.0551 | 0.8995 |
| 2024 | BASE+GAMESTATE | 25820 | 0.0869 | 0.0849 | 0.1897 | 0.0549 | 0.8996 |
| 2025 | A | 25723 | 0.0872 | 0.0870 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | V1_isotonic | 25723 | 0.0872 | 0.0877 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2025 | BASE+GAMESTATE | 25723 | 0.0872 | 0.0875 | 0.1925 | 0.0564 | 0.8988 |
| 2026 | A | 26055 | 0.0733 | 0.0769 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | V1_isotonic | 26055 | 0.0733 | 0.0781 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.0781 | 0.1805 | 0.0517 | 0.8868 |
| 2026 | BASE+GAMESTATE | 26055 | 0.0733 | 0.0782 | 0.1803 | 0.0517 | 0.8875 |
| all | A | 103009 | 0.0831 | 0.0847 | 0.2009 | 0.0567 | 0.8693 |
| all | V1_isotonic | 103009 | 0.0831 | 0.0842 | 0.1899 | 0.0552 | 0.8946 |
| all | BASE | 103009 | 0.0831 | 0.0841 | 0.1892 | 0.0551 | 0.8954 |
| all | BASE+GAMESTATE | 103009 | 0.0831 | 0.0843 | 0.1890 | 0.0551 | 0.8957 |

## Bootstrap of the log-loss difference against BASE (block bootstrap by game date, 1000 resamples; negative favors the new features)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2023 | p_BASE+GAMESTATE_cal | p_BASE_cal | -0.00027 | -0.00076 | 0.00020 | 0.87100 |
| 2024 | p_BASE+GAMESTATE_cal | p_BASE_cal | -0.00027 | -0.00074 | 0.00021 | 0.86100 |
| 2025 | p_BASE+GAMESTATE_cal | p_BASE_cal | -0.00006 | -0.00046 | 0.00034 | 0.63300 |
| 2026 | p_BASE+GAMESTATE_cal | p_BASE_cal | -0.00027 | -0.00066 | 0.00014 | 0.91700 |
| all | p_BASE+GAMESTATE_cal | p_BASE_cal | -0.00022 | -0.00045 | -0.00001 | 0.98000 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2023 | A | 2599 | 0.3744 | 0.3992 | 0.6416 | 0.2250 | 0.6227 |
| 2023 | V1_isotonic | 2599 | 0.3744 | 0.3851 | 0.6330 | 0.2214 | 0.6363 |
| 2023 | BASE | 2599 | 0.3744 | 0.3845 | 0.6334 | 0.2216 | 0.6379 |
| 2023 | BASE+GAMESTATE | 2599 | 0.3744 | 0.3826 | 0.6339 | 0.2220 | 0.6360 |
| 2024 | A | 1667 | 0.4439 | 0.4285 | 0.6628 | 0.2350 | 0.6204 |
| 2024 | V1_isotonic | 1667 | 0.4439 | 0.4298 | 0.6537 | 0.2308 | 0.6555 |
| 2024 | BASE | 1667 | 0.4439 | 0.4347 | 0.6516 | 0.2298 | 0.6557 |
| 2024 | BASE+GAMESTATE | 1667 | 0.4439 | 0.4390 | 0.6490 | 0.2287 | 0.6587 |
| 2025 | A | 2129 | 0.4298 | 0.4371 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | V1_isotonic | 2129 | 0.4298 | 0.4278 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2025 | BASE+GAMESTATE | 2129 | 0.4298 | 0.4299 | 0.6592 | 0.2336 | 0.6290 |
| 2026 | A | 1976 | 0.3806 | 0.4104 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | V1_isotonic | 1976 | 0.3806 | 0.3999 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.4010 | 0.6277 | 0.2186 | 0.6618 |
| 2026 | BASE+GAMESTATE | 1976 | 0.3806 | 0.4027 | 0.6263 | 0.2182 | 0.6642 |
| all | A | 8371 | 0.4038 | 0.4173 | 0.6527 | 0.2303 | 0.6236 |
| all | V1_isotonic | 8371 | 0.4038 | 0.4083 | 0.6437 | 0.2262 | 0.6454 |
| all | BASE | 8371 | 0.4038 | 0.4091 | 0.6425 | 0.2257 | 0.6479 |
| all | BASE+GAMESTATE | 8371 | 0.4038 | 0.4106 | 0.6416 | 0.2254 | 0.6492 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 |
|---|---|---|---|---|---|---|
| 2023 | A | 164 | 0.7317 | 0.6565 | 0.3171 | 0.6458 |
| 2023 | V1_isotonic | 164 | 0.7317 | 0.6524 | 0.3171 | 0.6776 |
| 2023 | BASE | 164 | 0.7195 | 0.6504 | 0.3171 | 0.6784 |
| 2023 | BASE+GAMESTATE | 164 | 0.7256 | 0.6545 | 0.2988 | 0.6776 |
| 2024 | A | 161 | 0.8758 | 0.7578 | 0.4472 | 0.7739 |
| 2024 | V1_isotonic | 161 | 0.8758 | 0.7785 | 0.4720 | 0.7468 |
| 2024 | BASE | 161 | 0.8634 | 0.7640 | 0.4410 | 0.7270 |
| 2024 | BASE+GAMESTATE | 161 | 0.8571 | 0.7805 | 0.4596 | 0.7326 |
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 |
| 2025 | V1_isotonic | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 |
| 2025 | BASE | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2025 | BASE+GAMESTATE | 164 | 0.8049 | 0.6951 | 0.3598 | 0.7113 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 |
| 2026 | V1_isotonic | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 |
| 2026 | BASE | 165 | 0.6970 | 0.5980 | 0.2000 | 0.6571 |
| 2026 | BASE+GAMESTATE | 165 | 0.6909 | 0.6040 | 0.2061 | 0.6584 |
| all | A | 654 | 0.7691 | 0.6835 | 0.3425 | 0.6993 |
| all | V1_isotonic | 654 | 0.7752 | 0.6814 | 0.3349 | 0.7066 |
| all | BASE | 654 | 0.7737 | 0.6769 | 0.3318 | 0.6922 |
| all | BASE+GAMESTATE | 654 | 0.7691 | 0.6830 | 0.3303 | 0.6947 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2023 | A | 492 | 0.2276 | 0.2696 | 0.2496 | -0.0200 | -0.1409 |
| 2023 | V1_isotonic | 492 | 0.4146 | 0.4125 | 0.4995 | 0.0869 | 0.0099 |
| 2023 | BASE | 492 | 0.4573 | 0.4322 | 0.5182 | 0.0859 | 0.0555 |
| 2023 | BASE+GAMESTATE | 492 | 0.4492 | 0.4300 | 0.5131 | 0.0831 | 0.0535 |
| 2024 | A | 483 | 0.2298 | 0.2503 | 0.2318 | -0.0185 | -0.0907 |
| 2024 | V1_isotonic | 483 | 0.4431 | 0.3735 | 0.4795 | 0.1060 | 0.2088 |
| 2024 | BASE | 483 | 0.4286 | 0.3600 | 0.4687 | 0.1088 | 0.1931 |
| 2024 | BASE+GAMESTATE | 483 | 0.4306 | 0.3652 | 0.4753 | 0.1101 | 0.1898 |
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | V1_isotonic | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2025 | BASE+GAMESTATE | 491 | 0.4297 | 0.3595 | 0.4475 | 0.0881 | 0.2446 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | V1_isotonic | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4202 | 0.3665 | 0.4513 | 0.0848 | 0.2040 |
| 2026 | BASE+GAMESTATE | 495 | 0.4404 | 0.3755 | 0.4628 | 0.0872 | 0.2459 |
| all | A | 1961 | 0.2167 | 0.2423 | 0.2244 | -0.0179 | -0.1011 |
| all | V1_isotonic | 1961 | 0.4329 | 0.3945 | 0.4892 | 0.0947 | 0.1375 |
| all | BASE | 1961 | 0.4273 | 0.3782 | 0.4693 | 0.0911 | 0.1634 |
| all | BASE+GAMESTATE | 1961 | 0.4375 | 0.3826 | 0.4747 | 0.0920 | 0.1835 |

## Disagreement buckets (BASE+new minus BASE, calibrated)
| bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|
| < -0.05 | 589 | 0.3877 | 0.3245 | 0.3514 |
| [-0.05, -0.02) | 4260 | 0.2995 | 0.2693 | 0.2683 |
| [-0.02, 0.02] | 92621 | 0.0599 | 0.0599 | 0.0592 |
| (0.02, 0.05] | 4773 | 0.2809 | 0.3116 | 0.2977 |
| > 0.05 | 766 | 0.3491 | 0.4134 | 0.3890 |

## Gain share by group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2023 | GAMESTATE | 0.0000 | 0 |
| BASE | 2023 | BASE | 1.0000 | 155 |
| BASE+GAMESTATE | 2023 | GAMESTATE | 0.0088 | 6 |
| BASE+GAMESTATE | 2023 | BASE | 0.9912 | 155 |
| BASE | 2024 | GAMESTATE | 0.0000 | 0 |
| BASE | 2024 | BASE | 1.0000 | 155 |
| BASE+GAMESTATE | 2024 | GAMESTATE | 0.0094 | 6 |
| BASE+GAMESTATE | 2024 | BASE | 0.9906 | 155 |
| BASE | 2025 | GAMESTATE | 0.0000 | 0 |
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+GAMESTATE | 2025 | GAMESTATE | 0.0079 | 6 |
| BASE+GAMESTATE | 2025 | BASE | 0.9921 | 155 |
| BASE | 2026 | GAMESTATE | 0.0000 | 0 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+GAMESTATE | 2026 | GAMESTATE | 0.0065 | 6 |
| BASE+GAMESTATE | 2026 | BASE | 0.9935 | 155 |

## Top 20 new features by gain share
| season | rank | feature | gain_share |
|---|---|---|---|
| 2023 | 1 | gs_abs_exp_margin | 0.00187 |
| 2023 | 2 | gs_exp_total | 0.00179 |
| 2023 | 3 | gs_exp_pace | 0.00170 |
| 2023 | 4 | gs_exp_margin | 0.00152 |
| 2023 | 5 | gs_pace_gap | 0.00132 |
| 2023 | 6 | gs_opp_pd_l20 | 0.00063 |
| 2024 | 1 | gs_exp_pace | 0.00192 |
| 2024 | 2 | gs_exp_total | 0.00181 |
| 2024 | 3 | gs_pace_gap | 0.00175 |
| 2024 | 4 | gs_abs_exp_margin | 0.00150 |
| 2024 | 5 | gs_exp_margin | 0.00140 |
| 2024 | 6 | gs_opp_pd_l20 | 0.00100 |
| 2025 | 1 | gs_exp_pace | 0.00175 |
| 2025 | 2 | gs_exp_margin | 0.00140 |
| 2025 | 3 | gs_pace_gap | 0.00135 |
| 2025 | 4 | gs_abs_exp_margin | 0.00126 |
| 2025 | 5 | gs_exp_total | 0.00112 |
| 2025 | 6 | gs_opp_pd_l20 | 0.00101 |
| 2026 | 1 | gs_exp_pace | 0.00147 |
| 2026 | 2 | gs_abs_exp_margin | 0.00123 |
| 2026 | 3 | gs_exp_margin | 0.00120 |
| 2026 | 4 | gs_exp_total | 0.00118 |
| 2026 | 5 | gs_pace_gap | 0.00100 |
| 2026 | 6 | gs_opp_pd_l20 | 0.00043 |

## Folds
```
{
  "2023": {
    "n_fit": 108266,
    "n_hold": 19126,
    "n_test": 27230,
    "cut_date": "2021-12-12",
    "BASE_best_iteration": 244,
    "BASE_holdout_logloss": 0.19091115823245022,
    "BASE+GAMESTATE_best_iteration": 279,
    "BASE+GAMESTATE_holdout_logloss": 0.1908921837060178
  },
  "2024": {
    "n_fit": 131428,
    "n_hold": 23194,
    "n_test": 27609,
    "cut_date": "2022-11-14",
    "BASE_best_iteration": 415,
    "BASE_holdout_logloss": 0.19248008849375692,
    "BASE+GAMESTATE_best_iteration": 333,
    "BASE+GAMESTATE_holdout_logloss": 0.1923139551877595
  },
  "2025": {
    "n_fit": 154663,
    "n_hold": 27568,
    "n_test": 27646,
    "cut_date": "2023-10-25",
    "BASE_best_iteration": 291,
    "BASE_holdout_logloss": 0.18845978204044328,
    "BASE+GAMESTATE_best_iteration": 307,
    "BASE+GAMESTATE_holdout_logloss": 0.18844788173964488
  },
  "2026": {
    "n_fit": 178306,
    "n_hold": 31571,
    "n_test": 28078,
    "cut_date": "2024-04-03",
    "BASE_best_iteration": 371,
    "BASE_holdout_logloss": 0.1916744493628809,
    "BASE+GAMESTATE_best_iteration": 301,
    "BASE+GAMESTATE_holdout_logloss": 0.19149364847148012
  }
}
```
