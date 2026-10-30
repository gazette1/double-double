# BOXOUT feature lift test (full history)

v1 rows, features and folds (test 2022-23 through 2025-26, trained on every earlier season back to 2017-18, all season types; metrics on regular-season test rows). BASE is the 155 v1 features with Platt calibration; BASE+BOXOUT adds 8 features from `boxout_features.parquet` merged on ['game_id', 'athlete_id']. Same rows, hyperparameters, seed, holdout and calibration, so the difference comes from the features alone. V1_isotonic is the saved v1 prediction for scale.

## Coverage of the new features (mean non-null share) by season
| season | mean_non_null |
|---|---|
| 2018 | 0.0000 |
| 2019 | 0.0000 |
| 2020 | 0.0000 |
| 2021 | 0.0000 |
| 2022 | 0.0000 |
| 2023 | 0.0000 |
| 2024 | 0.8360 |
| 2025 | 0.8861 |
| 2026 | 0.8804 |
| 2027 | 0.9584 |

## Calibrated log loss, Brier, AUC
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2025 | A | 25723 | 0.0872 | 0.0870 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | V1_isotonic | 25723 | 0.0872 | 0.0877 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2025 | BASE+BOXOUT | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2026 | A | 26055 | 0.0733 | 0.0769 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | V1_isotonic | 26055 | 0.0733 | 0.0781 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.0781 | 0.1805 | 0.0517 | 0.8868 |
| 2026 | BASE+BOXOUT | 26055 | 0.0733 | 0.0782 | 0.1805 | 0.0517 | 0.8869 |
| all | A | 51778 | 0.0802 | 0.0819 | 0.1989 | 0.0557 | 0.8643 |
| all | V1_isotonic | 51778 | 0.0802 | 0.0829 | 0.1871 | 0.0541 | 0.8925 |
| all | BASE | 51778 | 0.0802 | 0.0827 | 0.1865 | 0.0541 | 0.8934 |
| all | BASE+BOXOUT | 51778 | 0.0802 | 0.0828 | 0.1865 | 0.0540 | 0.8935 |

## Bootstrap of the log-loss difference against BASE (block bootstrap by game date, 1000 resamples; negative favors the new features)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2025 | p_BASE+BOXOUT_cal | p_BASE_cal | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| 2026 | p_BASE+BOXOUT_cal | p_BASE_cal | -0.00005 | -0.00043 | 0.00039 | 0.59200 |
| all | p_BASE+BOXOUT_cal | p_BASE_cal | -0.00002 | -0.00022 | 0.00018 | 0.59600 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2025 | A | 2129 | 0.4298 | 0.4371 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | V1_isotonic | 2129 | 0.4298 | 0.4278 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2025 | BASE+BOXOUT | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2026 | A | 1976 | 0.3806 | 0.4104 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | V1_isotonic | 1976 | 0.3806 | 0.3999 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.4010 | 0.6277 | 0.2186 | 0.6618 |
| 2026 | BASE+BOXOUT | 1976 | 0.3806 | 0.4036 | 0.6264 | 0.2182 | 0.6640 |
| all | A | 4105 | 0.4061 | 0.4243 | 0.6557 | 0.2318 | 0.6196 |
| all | V1_isotonic | 4105 | 0.4061 | 0.4143 | 0.6463 | 0.2274 | 0.6442 |
| all | BASE | 4105 | 0.4061 | 0.4142 | 0.6446 | 0.2267 | 0.6465 |
| all | BASE+BOXOUT | 4105 | 0.4061 | 0.4155 | 0.6440 | 0.2265 | 0.6473 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 |
|---|---|---|---|---|---|---|
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 |
| 2025 | V1_isotonic | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 |
| 2025 | BASE | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2025 | BASE+BOXOUT | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 |
| 2026 | V1_isotonic | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 |
| 2026 | BASE | 165 | 0.6970 | 0.5980 | 0.2000 | 0.6571 |
| 2026 | BASE+BOXOUT | 165 | 0.7030 | 0.6141 | 0.2182 | 0.6572 |
| all | A | 329 | 0.7356 | 0.6606 | 0.3040 | 0.6895 |
| all | V1_isotonic | 329 | 0.7477 | 0.6484 | 0.2766 | 0.7013 |
| all | BASE | 329 | 0.7568 | 0.6474 | 0.2857 | 0.6820 |
| all | BASE+BOXOUT | 329 | 0.7599 | 0.6555 | 0.2948 | 0.6821 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | V1_isotonic | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2025 | BASE+BOXOUT | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | V1_isotonic | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4202 | 0.3665 | 0.4513 | 0.0848 | 0.2040 |
| 2026 | BASE+BOXOUT | 495 | 0.4303 | 0.3595 | 0.4424 | 0.0829 | 0.2569 |
| all | A | 986 | 0.2049 | 0.2248 | 0.2081 | -0.0167 | -0.0864 |
| all | V1_isotonic | 986 | 0.4371 | 0.3958 | 0.4888 | 0.0930 | 0.1662 |
| all | BASE | 986 | 0.4118 | 0.3601 | 0.4452 | 0.0851 | 0.2027 |
| all | BASE+BOXOUT | 986 | 0.4168 | 0.3566 | 0.4407 | 0.0841 | 0.2292 |

## Disagreement buckets (BASE+new minus BASE, calibrated)
| bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|
| < -0.05 | 92 | 0.3814 | 0.3194 | 0.2935 |
| [-0.05, -0.02) | 1018 | 0.2906 | 0.2608 | 0.2662 |
| [-0.02, 0.02] | 49492 | 0.0735 | 0.0735 | 0.0714 |
| (0.02, 0.05] | 1055 | 0.2590 | 0.2892 | 0.2635 |
| > 0.05 | 121 | 0.3269 | 0.3878 | 0.3636 |

## Gain share by group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2025 | BOXOUT | 0.0000 | 0 |
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+BOXOUT | 2025 | BOXOUT | 0.0000 | 8 |
| BASE+BOXOUT | 2025 | BASE | 1.0000 | 155 |
| BASE | 2026 | BOXOUT | 0.0000 | 0 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+BOXOUT | 2026 | BOXOUT | 0.0008 | 8 |
| BASE+BOXOUT | 2026 | BASE | 0.9992 | 155 |

## Top 20 new features by gain share
| season | rank | feature | gain_share |
|---|---|---|---|
| 2025 | 1 | trk_boxout_success_l10 | 0.00000 |
| 2025 | 2 | trk_boxout_teamsuccess_l10 | 0.00000 |
| 2025 | 3 | trk_boxout_defshare_l10 | 0.00000 |
| 2025 | 4 | trk_boxout_success_l20 | 0.00000 |
| 2025 | 5 | trk_boxout_teamsuccess_l20 | 0.00000 |
| 2025 | 6 | trk_boxout_defshare_l20 | 0.00000 |
| 2025 | 7 | trk_boxout_success_ewm | 0.00000 |
| 2025 | 8 | trk_boxout_teamsuccess_ewm | 0.00000 |
| 2026 | 1 | trk_boxout_success_l20 | 0.00020 |
| 2026 | 2 | trk_boxout_defshare_l20 | 0.00019 |
| 2026 | 3 | trk_boxout_defshare_l10 | 0.00014 |
| 2026 | 4 | trk_boxout_teamsuccess_ewm | 0.00008 |
| 2026 | 5 | trk_boxout_success_ewm | 0.00007 |
| 2026 | 6 | trk_boxout_teamsuccess_l10 | 0.00003 |
| 2026 | 7 | trk_boxout_teamsuccess_l20 | 0.00002 |
| 2026 | 8 | trk_boxout_success_l10 | 0.00001 |

## Folds
```
{
  "2025": {
    "n_fit": 154663,
    "n_hold": 27568,
    "n_test": 27646,
    "cut_date": "2023-10-25",
    "BASE_best_iteration": 291,
    "BASE_holdout_logloss": 0.18845978204044328,
    "BASE+BOXOUT_best_iteration": 291,
    "BASE+BOXOUT_holdout_logloss": 0.18845978204044328
  },
  "2026": {
    "n_fit": 178306,
    "n_hold": 31571,
    "n_test": 28078,
    "cut_date": "2024-04-03",
    "BASE_best_iteration": 371,
    "BASE_holdout_logloss": 0.1916744493628809,
    "BASE+BOXOUT_best_iteration": 274,
    "BASE+BOXOUT_holdout_logloss": 0.19157424402764114
  }
}
```
