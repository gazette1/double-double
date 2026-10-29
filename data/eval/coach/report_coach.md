# COACH feature lift test (full history)

v1 rows, features and folds (test 2022-23 through 2025-26, trained on every earlier season back to 2017-18, all season types; metrics on regular-season test rows). BASE is the 155 v1 features with Platt calibration; BASE+COACH adds 35 features from `coach_features.parquet` merged on ['game_id', 'team_id']. Same rows, hyperparameters, seed, holdout and calibration, so the difference comes from the features alone. V1_isotonic is the saved v1 prediction for scale.

## Coverage of the new features (mean non-null share) by season
| season | mean_non_null |
|---|---|
| 2018 | 0.9410 |
| 2019 | 0.9695 |
| 2020 | 0.9619 |
| 2021 | 0.9660 |
| 2022 | 0.9651 |
| 2023 | 0.9690 |
| 2024 | 0.9663 |
| 2025 | 0.9661 |
| 2026 | 0.9661 |
| 2027 | 0.9117 |

## Calibrated log loss, Brier, AUC
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2023 | A | 25411 | 0.0849 | 0.0893 | 0.2058 | 0.0588 | 0.8694 |
| 2023 | V1_isotonic | 25411 | 0.0849 | 0.0867 | 0.1948 | 0.0574 | 0.8946 |
| 2023 | BASE | 25411 | 0.0849 | 0.0866 | 0.1940 | 0.0574 | 0.8950 |
| 2023 | BASE+COACH | 25411 | 0.0849 | 0.0867 | 0.1943 | 0.0575 | 0.8947 |
| 2024 | A | 25820 | 0.0869 | 0.0858 | 0.2000 | 0.0565 | 0.8793 |
| 2024 | V1_isotonic | 25820 | 0.0869 | 0.0845 | 0.1907 | 0.0552 | 0.8990 |
| 2024 | BASE | 25820 | 0.0869 | 0.0843 | 0.1900 | 0.0551 | 0.8995 |
| 2024 | BASE+COACH | 25820 | 0.0869 | 0.0849 | 0.1894 | 0.0548 | 0.9000 |
| 2025 | A | 25723 | 0.0872 | 0.0870 | 0.2041 | 0.0579 | 0.8745 |
| 2025 | V1_isotonic | 25723 | 0.0872 | 0.0877 | 0.1936 | 0.0565 | 0.8984 |
| 2025 | BASE | 25723 | 0.0872 | 0.0874 | 0.1925 | 0.0564 | 0.8988 |
| 2025 | BASE+COACH | 25723 | 0.0872 | 0.0871 | 0.1926 | 0.0564 | 0.8987 |
| 2026 | A | 26055 | 0.0733 | 0.0769 | 0.1938 | 0.0536 | 0.8525 |
| 2026 | V1_isotonic | 26055 | 0.0733 | 0.0781 | 0.1808 | 0.0518 | 0.8861 |
| 2026 | BASE | 26055 | 0.0733 | 0.0781 | 0.1805 | 0.0517 | 0.8868 |
| 2026 | BASE+COACH | 26055 | 0.0733 | 0.0788 | 0.1810 | 0.0519 | 0.8862 |
| all | A | 103009 | 0.0831 | 0.0847 | 0.2009 | 0.0567 | 0.8693 |
| all | V1_isotonic | 103009 | 0.0831 | 0.0842 | 0.1899 | 0.0552 | 0.8946 |
| all | BASE | 103009 | 0.0831 | 0.0841 | 0.1892 | 0.0551 | 0.8954 |
| all | BASE+COACH | 103009 | 0.0831 | 0.0843 | 0.1893 | 0.0551 | 0.8953 |

## Bootstrap of the log-loss difference against BASE (block bootstrap by game date, 1000 resamples; negative favors the new features)
| season | model | vs | logloss_diff | ci_lo | ci_hi | share_resamples_better |
|---|---|---|---|---|---|---|
| 2023 | p_BASE+COACH_cal | p_BASE_cal | 0.00028 | -0.00025 | 0.00080 | 0.17700 |
| 2024 | p_BASE+COACH_cal | p_BASE_cal | -0.00059 | -0.00111 | -0.00005 | 0.98500 |
| 2025 | p_BASE+COACH_cal | p_BASE_cal | 0.00005 | -0.00039 | 0.00051 | 0.41600 |
| 2026 | p_BASE+COACH_cal | p_BASE_cal | 0.00044 | -0.00003 | 0.00093 | 0.03600 |
| all | p_BASE+COACH_cal | p_BASE_cal | 0.00005 | -0.00020 | 0.00031 | 0.37900 |

## Mid-tier slice (Baseline A between 0.25 and 0.65)
| season | model | n | base_rate | mean_p | logloss | brier | auc |
|---|---|---|---|---|---|---|---|
| 2023 | A | 2599 | 0.3744 | 0.3992 | 0.6416 | 0.2250 | 0.6227 |
| 2023 | V1_isotonic | 2599 | 0.3744 | 0.3851 | 0.6330 | 0.2214 | 0.6363 |
| 2023 | BASE | 2599 | 0.3744 | 0.3845 | 0.6334 | 0.2216 | 0.6379 |
| 2023 | BASE+COACH | 2599 | 0.3744 | 0.3819 | 0.6377 | 0.2235 | 0.6286 |
| 2024 | A | 1667 | 0.4439 | 0.4285 | 0.6628 | 0.2350 | 0.6204 |
| 2024 | V1_isotonic | 1667 | 0.4439 | 0.4298 | 0.6537 | 0.2308 | 0.6555 |
| 2024 | BASE | 1667 | 0.4439 | 0.4347 | 0.6516 | 0.2298 | 0.6557 |
| 2024 | BASE+COACH | 1667 | 0.4439 | 0.4389 | 0.6491 | 0.2286 | 0.6590 |
| 2025 | A | 2129 | 0.4298 | 0.4371 | 0.6683 | 0.2378 | 0.6064 |
| 2025 | V1_isotonic | 2129 | 0.4298 | 0.4278 | 0.6637 | 0.2355 | 0.6245 |
| 2025 | BASE | 2129 | 0.4298 | 0.4265 | 0.6603 | 0.2342 | 0.6260 |
| 2025 | BASE+COACH | 2129 | 0.4298 | 0.4248 | 0.6594 | 0.2338 | 0.6274 |
| 2026 | A | 1976 | 0.3806 | 0.4104 | 0.6421 | 0.2253 | 0.6323 |
| 2026 | V1_isotonic | 1976 | 0.3806 | 0.3999 | 0.6275 | 0.2186 | 0.6618 |
| 2026 | BASE | 1976 | 0.3806 | 0.4010 | 0.6277 | 0.2186 | 0.6618 |
| 2026 | BASE+COACH | 1976 | 0.3806 | 0.4063 | 0.6279 | 0.2189 | 0.6622 |
| all | A | 8371 | 0.4038 | 0.4173 | 0.6527 | 0.2303 | 0.6236 |
| all | V1_isotonic | 8371 | 0.4038 | 0.4083 | 0.6437 | 0.2262 | 0.6454 |
| all | BASE | 8371 | 0.4038 | 0.4091 | 0.6425 | 0.2257 | 0.6479 |
| all | BASE+COACH | 8371 | 0.4038 | 0.4099 | 0.6432 | 0.2261 | 0.6458 |

## Nightly top-3 by probability
| season | model | nights | top1_hit | top3_hit | all3_hit | mean_p_top3 |
|---|---|---|---|---|---|---|
| 2023 | A | 164 | 0.7317 | 0.6565 | 0.3171 | 0.6458 |
| 2023 | V1_isotonic | 164 | 0.7317 | 0.6524 | 0.3171 | 0.6776 |
| 2023 | BASE | 164 | 0.7195 | 0.6504 | 0.3171 | 0.6784 |
| 2023 | BASE+COACH | 164 | 0.7317 | 0.6667 | 0.3598 | 0.6672 |
| 2024 | A | 161 | 0.8758 | 0.7578 | 0.4472 | 0.7739 |
| 2024 | V1_isotonic | 161 | 0.8758 | 0.7785 | 0.4720 | 0.7468 |
| 2024 | BASE | 161 | 0.8634 | 0.7640 | 0.4410 | 0.7270 |
| 2024 | BASE+COACH | 161 | 0.8696 | 0.7805 | 0.4658 | 0.7302 |
| 2025 | A | 164 | 0.7988 | 0.7154 | 0.4146 | 0.7504 |
| 2025 | V1_isotonic | 164 | 0.8110 | 0.6951 | 0.3537 | 0.7393 |
| 2025 | BASE | 164 | 0.8171 | 0.6972 | 0.3720 | 0.7071 |
| 2025 | BASE+COACH | 164 | 0.8110 | 0.7093 | 0.3720 | 0.7045 |
| 2026 | A | 165 | 0.6727 | 0.6061 | 0.1939 | 0.6290 |
| 2026 | V1_isotonic | 165 | 0.6848 | 0.6020 | 0.2000 | 0.6636 |
| 2026 | BASE | 165 | 0.6970 | 0.5980 | 0.2000 | 0.6571 |
| 2026 | BASE+COACH | 165 | 0.6848 | 0.6061 | 0.2061 | 0.6559 |
| all | A | 654 | 0.7691 | 0.6835 | 0.3425 | 0.6993 |
| all | V1_isotonic | 654 | 0.7752 | 0.6814 | 0.3349 | 0.7066 |
| all | BASE | 654 | 0.7737 | 0.6769 | 0.3318 | 0.6922 |
| all | BASE+COACH | 654 | 0.7737 | 0.6901 | 0.3502 | 0.6892 |

## Nightly top-3 by proxy edge (q >= 0.2; assumption, not a price backtest)
| season | model | picks | hit | mean_q | mean_p | mean_edge | ret_per_unit |
|---|---|---|---|---|---|---|---|
| 2023 | A | 492 | 0.2276 | 0.2696 | 0.2496 | -0.0200 | -0.1409 |
| 2023 | V1_isotonic | 492 | 0.4146 | 0.4125 | 0.4995 | 0.0869 | 0.0099 |
| 2023 | BASE | 492 | 0.4573 | 0.4322 | 0.5182 | 0.0859 | 0.0555 |
| 2023 | BASE+COACH | 492 | 0.4228 | 0.4284 | 0.5118 | 0.0834 | -0.0166 |
| 2024 | A | 483 | 0.2298 | 0.2503 | 0.2318 | -0.0185 | -0.0907 |
| 2024 | V1_isotonic | 483 | 0.4431 | 0.3735 | 0.4795 | 0.1060 | 0.2088 |
| 2024 | BASE | 483 | 0.4286 | 0.3600 | 0.4687 | 0.1088 | 0.1931 |
| 2024 | BASE+COACH | 483 | 0.4431 | 0.3654 | 0.4717 | 0.1063 | 0.2387 |
| 2025 | A | 491 | 0.2037 | 0.2263 | 0.2095 | -0.0168 | -0.0915 |
| 2025 | V1_isotonic | 491 | 0.4338 | 0.4034 | 0.4998 | 0.0965 | 0.1419 |
| 2025 | BASE | 491 | 0.4033 | 0.3537 | 0.4390 | 0.0853 | 0.2013 |
| 2025 | BASE+COACH | 491 | 0.4073 | 0.3504 | 0.4330 | 0.0826 | 0.2148 |
| 2026 | A | 495 | 0.2061 | 0.2233 | 0.2068 | -0.0165 | -0.0813 |
| 2026 | V1_isotonic | 495 | 0.4404 | 0.3882 | 0.4778 | 0.0896 | 0.1903 |
| 2026 | BASE | 495 | 0.4202 | 0.3665 | 0.4513 | 0.0848 | 0.2040 |
| 2026 | BASE+COACH | 495 | 0.4384 | 0.3631 | 0.4506 | 0.0875 | 0.2547 |
| all | A | 1961 | 0.2167 | 0.2423 | 0.2244 | -0.0179 | -0.1011 |
| all | V1_isotonic | 1961 | 0.4329 | 0.3945 | 0.4892 | 0.0947 | 0.1375 |
| all | BASE | 1961 | 0.4273 | 0.3782 | 0.4693 | 0.0911 | 0.1634 |
| all | BASE+COACH | 1961 | 0.4278 | 0.3769 | 0.4668 | 0.0899 | 0.1727 |

## Disagreement buckets (BASE+new minus BASE, calibrated)
| bucket | n | mean_base | mean_model | realized |
|---|---|---|---|---|
| < -0.05 | 1261 | 0.4092 | 0.3416 | 0.3743 |
| [-0.05, -0.02) | 4790 | 0.3028 | 0.2716 | 0.2854 |
| [-0.02, 0.02] | 90274 | 0.0548 | 0.0549 | 0.0539 |
| (0.02, 0.05] | 5355 | 0.2420 | 0.2728 | 0.2530 |
| > 0.05 | 1329 | 0.3375 | 0.4048 | 0.3725 |

## Gain share by group
| model | season | group | gain_share | n_features |
|---|---|---|---|---|
| BASE | 2023 | COACH | 0.0000 | 0 |
| BASE | 2023 | BASE | 1.0000 | 155 |
| BASE+COACH | 2023 | COACH | 0.0560 | 35 |
| BASE+COACH | 2023 | BASE | 0.9440 | 155 |
| BASE | 2024 | COACH | 0.0000 | 0 |
| BASE | 2024 | BASE | 1.0000 | 155 |
| BASE+COACH | 2024 | COACH | 0.0484 | 35 |
| BASE+COACH | 2024 | BASE | 0.9516 | 155 |
| BASE | 2025 | COACH | 0.0000 | 0 |
| BASE | 2025 | BASE | 1.0000 | 155 |
| BASE+COACH | 2025 | COACH | 0.0331 | 35 |
| BASE+COACH | 2025 | BASE | 0.9669 | 155 |
| BASE | 2026 | COACH | 0.0000 | 0 |
| BASE | 2026 | BASE | 1.0000 | 155 |
| BASE+COACH | 2026 | COACH | 0.0372 | 35 |
| BASE+COACH | 2026 | BASE | 0.9628 | 155 |

## Top 20 new features by gain share
| season | rank | feature | gain_share |
|---|---|---|---|
| 2023 | 1 | oppc_fp_top5_min_share | 0.00289 |
| 2023 | 2 | coach_fp_fta_rate | 0.00269 |
| 2023 | 3 | oppc_fp_ast_allowed_rate | 0.00268 |
| 2023 | 4 | coach_fp_minus_team_dreb_share | 0.00262 |
| 2023 | 5 | coach_fp_minus_team_pace | 0.00258 |
| 2023 | 6 | coach_fp_minus_team_top5_min_share | 0.00248 |
| 2023 | 7 | oppc_fp_fg3a_allowed_rate | 0.00244 |
| 2023 | 8 | oppc_fp_pace | 0.00240 |
| 2023 | 9 | oppc_tenure_games | 0.00232 |
| 2023 | 10 | coach_fp_ast_allowed_rate | 0.00229 |
| 2023 | 11 | coach_fp_fg3a_allowed_rate | 0.00228 |
| 2023 | 12 | coach_fp_minus_team_ast_rate | 0.00217 |
| 2023 | 13 | coach_fp_oreb_share | 0.00215 |
| 2023 | 14 | coach_fp_pace | 0.00214 |
| 2023 | 15 | oppc_career_games | 0.00208 |
| 2023 | 16 | oppc_fp_oreb_allowed_share | 0.00202 |
| 2023 | 17 | coach_fp_ast_rate | 0.00198 |
| 2023 | 18 | coach_fp_margin | 0.00197 |
| 2023 | 19 | coach_fp_fg3a_rate | 0.00192 |
| 2023 | 20 | oppc_fp_dreb_share | 0.00165 |
| 2024 | 1 | oppc_fp_top5_min_share | 0.00278 |
| 2024 | 2 | oppc_fp_fg3a_allowed_rate | 0.00240 |
| 2024 | 3 | coach_fp_oreb_share | 0.00228 |
| 2024 | 4 | oppc_tenure_games | 0.00226 |
| 2024 | 5 | coach_fp_minus_team_ast_rate | 0.00223 |
| 2024 | 6 | coach_fp_fta_rate | 0.00219 |
| 2024 | 7 | oppc_fp_ast_allowed_rate | 0.00206 |
| 2024 | 8 | coach_fp_minus_team_pace | 0.00205 |
| 2024 | 9 | coach_fp_minus_team_dreb_share | 0.00202 |
| 2024 | 10 | coach_fp_minus_team_top5_min_share | 0.00190 |
| 2024 | 11 | coach_fp_margin | 0.00182 |
| 2024 | 12 | oppc_fp_pace | 0.00181 |
| 2024 | 13 | coach_fp_fg3a_rate | 0.00174 |
| 2024 | 14 | oppc_fp_oreb_allowed_share | 0.00171 |
| 2024 | 15 | coach_fp_fg3a_allowed_rate | 0.00168 |
| 2024 | 16 | coach_fp_pace | 0.00164 |
| 2024 | 17 | oppc_fp_dreb_share | 0.00163 |
| 2024 | 18 | oppc_career_games | 0.00161 |
| 2024 | 19 | coach_fp_ast_allowed_rate | 0.00155 |
| 2024 | 20 | coach_fp_ast_rate | 0.00146 |
| 2025 | 1 | oppc_fp_top5_min_share | 0.00202 |
| 2025 | 2 | coach_fp_minus_team_ast_rate | 0.00163 |
| 2025 | 3 | oppc_fp_fg3a_allowed_rate | 0.00162 |
| 2025 | 4 | oppc_tenure_games | 0.00159 |
| 2025 | 5 | coach_fp_oreb_share | 0.00156 |
| 2025 | 6 | oppc_fp_dreb_share | 0.00151 |
| 2025 | 7 | oppc_career_games | 0.00148 |
| 2025 | 8 | oppc_fp_ast_allowed_rate | 0.00147 |
| 2025 | 9 | coach_fp_margin | 0.00138 |
| 2025 | 10 | coach_fp_minus_team_dreb_share | 0.00137 |
| 2025 | 11 | coach_fp_minus_team_top5_min_share | 0.00134 |
| 2025 | 12 | coach_fp_fg3a_allowed_rate | 0.00133 |
| 2025 | 13 | coach_fp_fta_rate | 0.00123 |
| 2025 | 14 | oppc_fp_pace | 0.00123 |
| 2025 | 15 | oppc_fp_oreb_allowed_share | 0.00117 |
| 2025 | 16 | coach_fp_ast_rate | 0.00117 |
| 2025 | 17 | coach_fp_ast_allowed_rate | 0.00116 |
| 2025 | 18 | coach_fp_fg3a_rate | 0.00106 |
| 2025 | 19 | coach_fp_minus_team_pace | 0.00103 |
| 2025 | 20 | coach_fp_dreb_share | 0.00098 |
| 2026 | 1 | oppc_tenure_games | 0.00203 |
| 2026 | 2 | coach_fp_oreb_share | 0.00184 |
| 2026 | 3 | oppc_fp_pace | 0.00181 |
| 2026 | 4 | oppc_fp_top5_min_share | 0.00175 |
| 2026 | 5 | oppc_fp_ast_allowed_rate | 0.00169 |
| 2026 | 6 | coach_fp_minus_team_top5_min_share | 0.00162 |
| 2026 | 7 | coach_fp_fg3a_allowed_rate | 0.00160 |
| 2026 | 8 | coach_fp_minus_team_pace | 0.00160 |
| 2026 | 9 | coach_fp_minus_team_ast_rate | 0.00157 |
| 2026 | 10 | coach_fp_minus_team_dreb_share | 0.00155 |
| 2026 | 11 | coach_fp_fta_rate | 0.00152 |
| 2026 | 12 | oppc_fp_dreb_share | 0.00143 |
| 2026 | 13 | oppc_fp_fg3a_allowed_rate | 0.00142 |
| 2026 | 14 | oppc_career_games | 0.00135 |
| 2026 | 15 | coach_fp_dreb_share | 0.00132 |
| 2026 | 16 | oppc_fp_oreb_allowed_share | 0.00129 |
| 2026 | 17 | coach_fp_ast_rate | 0.00118 |
| 2026 | 18 | coach_fp_n10 | 0.00111 |
| 2026 | 19 | coach_fp_margin | 0.00108 |
| 2026 | 20 | coach_fp_fg3a_rate | 0.00106 |

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
    "BASE+COACH_best_iteration": 387,
    "BASE+COACH_holdout_logloss": 0.19121311238464966
  },
  "2024": {
    "n_fit": 131428,
    "n_hold": 23194,
    "n_test": 27609,
    "cut_date": "2022-11-14",
    "BASE_best_iteration": 415,
    "BASE_holdout_logloss": 0.19248008849375692,
    "BASE+COACH_best_iteration": 393,
    "BASE+COACH_holdout_logloss": 0.19241655037736324
  },
  "2025": {
    "n_fit": 154663,
    "n_hold": 27568,
    "n_test": 27646,
    "cut_date": "2023-10-25",
    "BASE_best_iteration": 291,
    "BASE_holdout_logloss": 0.18845978204044328,
    "BASE+COACH_best_iteration": 308,
    "BASE+COACH_holdout_logloss": 0.18869216855139925
  },
  "2026": {
    "n_fit": 178306,
    "n_hold": 31571,
    "n_test": 28078,
    "cut_date": "2024-04-03",
    "BASE_best_iteration": 371,
    "BASE_holdout_logloss": 0.1916744493628809,
    "BASE+COACH_best_iteration": 382,
    "BASE+COACH_holdout_logloss": 0.19185070302908008
  }
}
```
