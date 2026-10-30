# SHOTS feature lift test (full history)

v1 rows, features and folds (test 2022-23 through 2025-26, trained on every earlier season back to 2017-18, all season types; metrics on regular-season test rows). BASE is the 155 v1 features with Platt calibration; BASE+SHOTS adds 11 features from `shot_features.parquet` merged on ['game_id', 'athlete_id']. Same rows, hyperparameters, seed, holdout and calibration, so the difference comes from the features alone. V1_isotonic is the saved v1 prediction for scale.

## Coverage of the new features (mean non-null share) by season
| season | mean_non_null |
|---|---|
| 2018 | 0.0000 |
| 2019 | 0.0000 |
| 2020 | 0.0000 |
| 2021 | 0.0000 |
| 2022 | 0.0000 |
| 2023 | 0.0000 |
| 2024 | 0.8766 |
| 2025 | 0.9202 |
| 2026 | 0.9193 |
| 2027 | 0.9904 |

## Calibrated log loss, Brier, AUC
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2025 | A | 25723 | 0.0872 | 0.0870 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | V1_isotonic | 25723 | 0.0872 | 0.0877 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2025 | BASE+SHOTS | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2026 | A | 26055 | 0.0733 | 0.0769 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | V1_isotonic | 26055 | 0.0733 | 0.0781 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.0781 | 0.1805 | 0.0517 | 0.8868 |
| 2026 | BASE+SHOTS | 26055 | 0.0733 | 0.0783 | 0.1807 | 0.0518 | 0.8867 |
| all | A | 51778 | 0.0802 | 0.0819 | 0.1989 | 0.0557 | 0.8643 |
| all | V1_isotonic | 51778 | 0.0802 | 0.0829 | 0.1871 | 0.0541 | 0.8925 |
| all | BASE | 51778 | 0.0802 | 0.0827 | 0.1865 | 0.0541 | 0.8934 |
| all | BASE+SHOTS | 51778 | 0.0802 | 0.0828 | 0.1866 | 0.0541 | 0.8934 |

## Bootstrap of the log-loss difference against BASE (block bootstrap by game date, 1000 resamples; negative favors the new features)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2025 | p_BASE+SHOTS_cal | p_BASE_cal | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| 2026 | p_BASE+SHOTS_cal | p_BASE_cal | 0.00014 | -0.00030 | 0.00066 | 0.25800 |
| all | p_BASE+SHOTS_cal | p_BASE_cal | 0.00007 | -0.00014 | 0.00030 | 0.26200 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2025 | A | 2129 | 0.4298 | 0.4371 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | V1_isotonic | 2129 | 0.4298 | 0.4278 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2025 | BASE+SHOTS | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2026 | A | 1976 | 0.3806 | 0.4104 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | V1_isotonic | 1976 | 0.3806 | 0.3999 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.4010 | 0.6277 | 0.2186 | 0.6618 |
| 2026 | BASE+SHOTS | 1976 | 0.3806 | 0.4036 | 0.6274 | 0.2187 | 0.6624 |
| all | A | 4105 | 0.4061 | 0.4243 | 0.6557 | 0.2318 | 0.6196 |
| all | V1_isotonic | 4105 | 0.4061 | 0.4143 | 0.6463 | 0.2274 | 0.6442 |
| all | BASE | 4105 | 0.4061 | 0.4142 | 0.6446 | 0.2267 | 0.6465 |
| all | BASE+SHOTS | 4105 | 0.4061 | 0.4155 | 0.6445 | 0.2267 | 0.6462 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 |
|---|---|---|---|---|---|---|
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 |
| 2025 | V1_isotonic | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 |
| 2025 | BASE | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2025 | BASE+SHOTS | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 |
| 2026 | V1_isotonic | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 |
| 2026 | BASE | 165 | 0.6970 | 0.5980 | 0.2000 | 0.6571 |
| 2026 | BASE+SHOTS | 165 | 0.7030 | 0.6081 | 0.1879 | 0.6598 |
| all | A | 329 | 0.7356 | 0.6606 | 0.3040 | 0.6895 |
| all | V1_isotonic | 329 | 0.7477 | 0.6484 | 0.2766 | 0.7013 |
| all | BASE | 329 | 0.7568 | 0.6474 | 0.2857 | 0.6820 |
| all | BASE+SHOTS | 329 | 0.7599 | 0.6525 | 0.2796 | 0.6834 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | V1_isotonic | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2025 | BASE+SHOTS | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | V1_isotonic | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4202 | 0.3665 | 0.4513 | 0.0848 | 0.2040 |
| 2026 | BASE+SHOTS | 495 | 0.4545 | 0.3729 | 0.4605 | 0.0876 | 0.2848 |
| all | A | 986 | 0.2049 | 0.2248 | 0.2081 | -0.0167 | -0.0864 |
| all | V1_isotonic | 986 | 0.4371 | 0.3958 | 0.4888 | 0.0930 | 0.1662 |
| all | BASE | 986 | 0.4118 | 0.3601 | 0.4452 | 0.0851 | 0.2027 |
| all | BASE+SHOTS | 986 | 0.4290 | 0.3633 | 0.4498 | 0.0865 | 0.2432 |

## Disagreement buckets (BASE+new minus BASE, calibrated)
| bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|
| < -0.05 | 107 | 0.3941 | 0.3315 | 0.3832 |
| [-0.05, -0.02) | 994 | 0.2780 | 0.2487 | 0.2545 |
| [-0.02, 0.02] | 49444 | 0.0734 | 0.0734 | 0.0712 |
| (0.02, 0.05] | 1090 | 0.2621 | 0.2926 | 0.2615 |
| > 0.05 | 143 | 0.3433 | 0.4062 | 0.3846 |

## Gain share by group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2025 | SHOTS | 0.0000 | 0 |
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+SHOTS | 2025 | SHOTS | 0.0000 | 11 |
| BASE+SHOTS | 2025 | BASE | 1.0000 | 155 |
| BASE | 2026 | SHOTS | 0.0000 | 0 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+SHOTS | 2026 | SHOTS | 0.0020 | 11 |
| BASE+SHOTS | 2026 | BASE | 0.9980 | 155 |

## Top 20 new features by gain share
| season | rank | feature | gain_share |
|---|---|---|---|
| 2025 | 1 | shot_open3a_pm_l10 | 0.00000 |
| 2025 | 2 | shot_wide3a_pm_l10 | 0.00000 |
| 2025 | 3 | shot_openfga_pm_l10 | 0.00000 |
| 2025 | 4 | shot_open3_share_l20 | 0.00000 |
| 2025 | 5 | shot_open3_pct_l20 | 0.00000 |
| 2025 | 6 | shot_open3a_pm_ewm | 0.00000 |
| 2025 | 7 | shot_tm_open3a_pg_l10 | 0.00000 |
| 2025 | 8 | shot_tm_open3_share_l20 | 0.00000 |
| 2025 | 9 | shot_tm_open3_pct_l20 | 0.00000 |
| 2025 | 10 | shot_opp_open3a_allowed_l10 | 0.00000 |
| 2025 | 11 | shot_tmx_open3a_pg_l10 | 0.00000 |
| 2026 | 1 | shot_opp_open3a_allowed_l10 | 0.00026 |
| 2026 | 2 | shot_tm_open3a_pg_l10 | 0.00025 |
| 2026 | 3 | shot_wide3a_pm_l10 | 0.00022 |
| 2026 | 4 | shot_open3_pct_l20 | 0.00021 |
| 2026 | 5 | shot_open3_share_l20 | 0.00021 |
| 2026 | 6 | shot_open3a_pm_l10 | 0.00019 |
| 2026 | 7 | shot_open3a_pm_ewm | 0.00017 |
| 2026 | 8 | shot_tmx_open3a_pg_l10 | 0.00017 |
| 2026 | 9 | shot_tm_open3_pct_l20 | 0.00012 |
| 2026 | 10 | shot_tm_open3_share_l20 | 0.00010 |
| 2026 | 11 | shot_openfga_pm_l10 | 0.00010 |

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
    "BASE+SHOTS_best_iteration": 291,
    "BASE+SHOTS_holdout_logloss": 0.18845978204044328
  },
  "2026": {
    "n_fit": 178306,
    "n_hold": 31571,
    "n_test": 28078,
    "cut_date": "2024-04-03",
    "BASE_best_iteration": 371,
    "BASE_holdout_logloss": 0.1916744493628809,
    "BASE+SHOTS_best_iteration": 334,
    "BASE+SHOTS_holdout_logloss": 0.1915792986513534
  }
}
```
