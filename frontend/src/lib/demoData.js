// Automatically generated high-fidelity demonstration dataset
export const DEMO_DATASET = {
  "schema_version": "1.0.0",
  "request_id": "b2f3ea569f204a7891ed66b425514277",
  "generated_at": "2026-09-06T00:13:38.496752Z",
  "duration_ms": 842.1,
  "input_source": "upload",
  "filename": "demo_early.csv",
  "outcome_filename": "demo_outcomes.csv",
  "profile_id": "mlcc_x7r_leakage_ua",
  "as_of_hour": 24.0,
  "target_hour": 168.0,
  "checkpoint_hours_used": [
    0.0,
    24.0
  ],
  "model_versions": {
    "anomaly": "mlcc-pilot-1.1",
    "forecast": "xgboost_v2",
    "bundle": "b5553f6f7032092e-s26170"
  },
  "model_info": {
    "prototype_version": "mlcc-pilot-1.1",
    "bundle_id": "b5553f6f7032092e-s26170",
    "selected_model": "xgboost_v2",
    "validation_winner": "xgboost_v2",
    "forecast_selection": "internal validation winner",
    "selection_warning": null,
    "model_training_data": "synthetic",
    "model_fitted_during_request": false,
    "supported_family": "MLCC_X7R",
    "supported_measurement": "leakage_ua",
    "available_models": [
      "hist_gradient_boosting",
      "linear_extrapolation",
      "persistence",
      "ridge",
      "xgboost",
      "xgboost_v2"
    ],
    "limitations": [
      "Only exact 0/24-hour MLCC_X7R leakage measurements in uA are supported",
      "Synthetic scenarios demonstrate pipeline; field accuracy requires measured hardware verification",
      "Candidate hyperparameters were fixed prior to test evaluation"
    ]
  },
  "batch_count": 4,
  "unique_component_count": 64,
  "measurement_record_count": 128,
  "scored_record_count": 64,
  "unscored_record_count": 0,
  "decision_counts": {
    "ACCEPT": 46,
    "MONITOR": 8,
    "RETEST": 6,
    "ENGINEER_REVIEW": 4
  },
  "within_limits_but_unusual_count": 16,
  "capabilities": {
    "anomaly": true,
    "forecast": true,
    "intervals": true,
    "explanations": true,
    "peer_statistics": true,
    "mode": "demo"
  },
  "provenance": "synthetic",
  "records": [
    {
      "component_id": "MLCC_C000147",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ENGINEER_REVIEW",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "Drift is unusually faster than comparable components",
        "The predicted final value crosses the approved limit",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 1.0,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.89131,
        "robust_deviation_score": 16.0304,
        "reason_codes": [
          "Current value is unusually above the batch norm",
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.9337062835693358,
        "prediction_lower": 0.6267158387824784,
        "prediction_upper": 1.2406967283561934,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.30716028809547424,
              "feature_value": 0.13079600842285716
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.14919772744178772,
              "feature_value": 0.3274133790014286
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.119488425552845,
              "feature_value": 0.6725866209985715
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.07524870336055756,
              "feature_value": 16.0303971372316
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.032404713332653046,
              "feature_value": 0.005449833684285715
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.4708,
        "headroom_fraction": 0.6726,
        "limit_fraction": 0.3274
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 6.785,
        "slope_batch_robust_z": 16.03,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1376,
      "latest_value": 0.2292,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0916,
      "percent_change": 0.6655,
      "percent_change_available": true,
      "slope_per_hour": 0.00381,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1376
        },
        {
          "hour": 24.0,
          "value": 0.2292
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.2072
        },
        {
          "hour": 72.0,
          "value": 0.1279
        },
        {
          "hour": 96.0,
          "value": 0.1271
        },
        {
          "hour": 120.0,
          "value": 0.1302
        },
        {
          "hour": 144.0,
          "value": 0.1284
        },
        {
          "hour": 168.0,
          "value": 0.2507
        }
      ],
      "observed_168h": 0.2507,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 1,
        "board_position": 1,
        "grid_row": 1,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C001046",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ENGINEER_REVIEW",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "Drift is unusually faster than comparable components",
        "Current value has used at least 80% of the safety limit",
        "The current measurement has crossed the approved limit"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 1.0,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.94681,
        "robust_deviation_score": 50.9323,
        "reason_codes": [
          "Current value is unusually above the batch norm",
          "Drift is unusually faster than comparable components",
          "Current value has used at least 80% of the safety limit"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.4999830782413483,
        "prediction_lower": 0.0,
        "prediction_upper": 1.0701081899883693,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.3076769709587097,
              "feature_value": 1.0667902745153846
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": -0.20821192860603333,
              "feature_value": -0.009982015917021272
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.20641334354877472,
              "feature_value": 24.70682108073235
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.19450682401657104,
              "feature_value": 15.7058373795
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.10792333632707596,
              "feature_value": -0.0667902745153846
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": -0.0868,
        "headroom_fraction": -0.0668,
        "limit_fraction": 1.0668
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 24.707,
        "slope_batch_robust_z": 50.932,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0997,
      "latest_value": 1.3868,
      "last_observation_hour": 24.0,
      "absolute_change": 1.2871,
      "percent_change": 12.906,
      "percent_change_available": true,
      "slope_per_hour": 0.05363,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0997
        },
        {
          "hour": 24.0,
          "value": 1.3868
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 1.384
        },
        {
          "hour": 72.0,
          "value": 1.1905
        },
        {
          "hour": 96.0,
          "value": 0.0952
        },
        {
          "hour": 120.0,
          "value": 0.0926
        },
        {
          "hour": 144.0,
          "value": 0.0897
        },
        {
          "hour": 168.0,
          "value": 0.9482
        }
      ],
      "observed_168h": 0.9482,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 2,
        "board_position": 2,
        "grid_row": 1,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C001733",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ENGINEER_REVIEW",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "Drift is unusually faster than comparable components",
        "The predicted final value crosses the approved limit",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.99748,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.86989,
        "robust_deviation_score": 9.4824,
        "reason_codes": [
          "Current value is unusually above the batch norm",
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.28777214884757996,
        "prediction_lower": 0.17813270428084513,
        "prediction_upper": 0.39741159341431476,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.1061507910490036,
              "feature_value": 0.10132637570599998
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.02982933260500431,
              "feature_value": 9.482383392648833
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.024227052927017212,
              "feature_value": 0.7367216300032
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.02270319312810898,
              "feature_value": 0.2632783699968
            },
            {
              "feature": "percent_change",
              "contribution_ua": 0.012992299161851406,
              "feature_value": 0.6256568568341243
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.1842,
        "headroom_fraction": 0.7367,
        "limit_fraction": 0.2633
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 3.922,
        "slope_batch_robust_z": 9.482,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0405,
      "latest_value": 0.0658,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0253,
      "percent_change": 0.6249,
      "percent_change_available": true,
      "slope_per_hour": 0.00106,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0405
        },
        {
          "hour": 24.0,
          "value": 0.0658
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1055
        },
        {
          "hour": 72.0,
          "value": 0.1472
        },
        {
          "hour": 96.0,
          "value": 0.1887
        },
        {
          "hour": 120.0,
          "value": 0.2297
        },
        {
          "hour": 144.0,
          "value": 0.274
        },
        {
          "hour": 168.0,
          "value": 0.3115
        }
      ],
      "observed_168h": 0.3115,
      "crossed_applicable_limit": true,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 3,
        "board_position": 3,
        "grid_row": 1,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C001874",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ENGINEER_REVIEW",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "Drift is unusually faster than comparable components",
        "The predicted final value crosses the approved limit",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.99712,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.89211,
        "robust_deviation_score": 9.3485,
        "reason_codes": [
          "Current value is unusually above the batch norm",
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 1.5291263699531557,
        "prediction_lower": 0.9590012582061345,
        "prediction_upper": 2.0992514817001764,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.5712088942527771,
              "feature_value": 0.1728226778476923
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.18874970078468323,
              "feature_value": 0.7312657274246154
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.14796894788742065,
              "feature_value": 9.348487233570454
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.1373966634273529,
              "feature_value": 0.2687342725753846
            },
            {
              "feature": "percent_change",
              "contribution_ua": 0.07367278635501862,
              "feature_value": 1.8018955720459278
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 0.9506,
        "headroom_fraction": 0.7313,
        "limit_fraction": 0.2687
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 3.98,
        "slope_batch_robust_z": 9.348,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1247,
      "latest_value": 0.3494,
      "last_observation_hour": 24.0,
      "absolute_change": 0.2247,
      "percent_change": 1.8021,
      "percent_change_available": true,
      "slope_per_hour": 0.00936,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1247
        },
        {
          "hour": 24.0,
          "value": 0.3494
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.5714
        },
        {
          "hour": 72.0,
          "value": 0.747
        },
        {
          "hour": 96.0,
          "value": 0.9127
        },
        {
          "hour": 120.0,
          "value": 1.2446
        },
        {
          "hour": 144.0,
          "value": 1.3076
        },
        {
          "hour": 168.0,
          "value": 1.513
        }
      ],
      "observed_168h": 1.513,
      "crossed_applicable_limit": true,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 4,
        "board_position": 4,
        "grid_row": 1,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000287",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Drift is unusually faster than comparable components",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.89581,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.80612,
        "robust_deviation_score": 5.6515,
        "reason_codes": [
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.10290067434310912,
        "prediction_lower": 0.05027374095107641,
        "prediction_upper": 0.15552760773514182,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.049718767404556274,
              "feature_value": 0.07273241055166667
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.007488348986953497,
              "feature_value": -0.095110138071
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.005465405061841011,
              "feature_value": 2.1723987088954706
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.0052724601700901985,
              "feature_value": 0.0030305171063194423
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.005203177221119404,
              "feature_value": 5.651506065511205
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1002,
        "headroom_fraction": 0.8354,
        "limit_fraction": 0.1646
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 2.172,
        "slope_batch_robust_z": 5.652,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.011,
      "latest_value": 0.0198,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0087,
      "percent_change": 0.7892,
      "percent_change_available": true,
      "slope_per_hour": 0.00036,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.011
        },
        {
          "hour": 24.0,
          "value": 0.0198
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.031
        },
        {
          "hour": 72.0,
          "value": 0.0423
        },
        {
          "hour": 96.0,
          "value": 0.0568
        },
        {
          "hour": 120.0,
          "value": 0.0665
        },
        {
          "hour": 144.0,
          "value": 0.0819
        },
        {
          "hour": 168.0,
          "value": 0.093
        }
      ],
      "observed_168h": 0.093,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 5,
        "board_position": 5,
        "grid_row": 1,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000889",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Drift is unusually faster than comparable components",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.9867,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.86607,
        "robust_deviation_score": 7.8066,
        "reason_codes": [
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.11967723369598388,
        "prediction_lower": 0.06705030030395116,
        "prediction_upper": 0.17230416708801657,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.05647151172161102,
              "feature_value": 0.10333243537750002
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.006062614731490612,
              "feature_value": 7.806568126997481
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.005270526744425297,
              "feature_value": 0.004305518140729166
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.005169733893126249,
              "feature_value": 0.7976357562774999
            },
            {
              "feature": "variability_fraction_of_limit",
              "contribution_ua": 0.0049669803120195866,
              "feature_value": 0.05166621768875001
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.0957,
        "headroom_fraction": 0.7976,
        "limit_fraction": 0.2024
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 3.406,
        "slope_batch_robust_z": 7.807,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0119,
      "latest_value": 0.0243,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0124,
      "percent_change": 1.0434,
      "percent_change_available": true,
      "slope_per_hour": 0.00052,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0119
        },
        {
          "hour": 24.0,
          "value": 0.0243
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0443
        },
        {
          "hour": 72.0,
          "value": 0.0662
        },
        {
          "hour": 96.0,
          "value": 0.0809
        },
        {
          "hour": 120.0,
          "value": 0.1047
        },
        {
          "hour": 144.0,
          "value": 0.1294
        },
        {
          "hour": 168.0,
          "value": 0.1462
        }
      ],
      "observed_168h": 0.1462,
      "crossed_applicable_limit": true,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 6,
        "board_position": 6,
        "grid_row": 1,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C001539",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "Drift is unusually faster than comparable components",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 1.0,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.93166,
        "robust_deviation_score": 32.8972,
        "reason_codes": [
          "Current value is unusually above the batch norm",
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.22314472496509552,
        "prediction_lower": 0.11350528039836069,
        "prediction_upper": 0.3327841695318303,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.07673797011375427,
              "feature_value": 0.37384490925040004
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.06310846656560898,
              "feature_value": 0.496379884524
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": -0.03364346921443939,
              "feature_value": -0.009369307240000069
            },
            {
              "feature": "percent_change",
              "contribution_ua": 0.016755331307649612,
              "feature_value": 3.05092410077749
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.015532190911471844,
              "feature_value": 0.503620115476
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.1259,
        "headroom_fraction": 0.5036,
        "limit_fraction": 0.4964
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 10.081,
        "slope_batch_robust_z": 32.897,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0306,
      "latest_value": 0.1241,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0935,
      "percent_change": 3.0522,
      "percent_change_available": true,
      "slope_per_hour": 0.00389,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0306
        },
        {
          "hour": 24.0,
          "value": 0.1241
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0273
        },
        {
          "hour": 72.0,
          "value": 0.026
        },
        {
          "hour": 96.0,
          "value": 0.0271
        },
        {
          "hour": 120.0,
          "value": 0.0687
        },
        {
          "hour": 144.0,
          "value": 0.1225
        },
        {
          "hour": 168.0,
          "value": 0.1181
        }
      ],
      "observed_168h": 0.1181,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 7,
        "board_position": 7,
        "grid_row": 1,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C001703",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Drift is unusually faster than comparable components",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.89621,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.83026,
        "robust_deviation_score": 5.6558,
        "reason_codes": [
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.11061792612075805,
        "prediction_lower": 0.057990992728725335,
        "prediction_upper": 0.16324485951279075,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.0533355176448822,
              "feature_value": 0.07279384140133333
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.007618546485900879,
              "feature_value": 5.655832444142433
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.004760103300213814,
              "feature_value": 0.003033076725055554
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.004562810063362122,
              "feature_value": 0.06416042484116667
            },
            {
              "feature": "percent_change",
              "contribution_ua": 0.003572870744392276,
              "feature_value": 1.1345598409228
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1036,
        "headroom_fraction": 0.863,
        "limit_fraction": 0.137
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.27,
        "slope_batch_robust_z": 5.656,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0077,
      "latest_value": 0.0164,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0087,
      "percent_change": 1.13,
      "percent_change_available": true,
      "slope_per_hour": 0.00036,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0077
        },
        {
          "hour": 24.0,
          "value": 0.0164
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0223
        },
        {
          "hour": 72.0,
          "value": 0.0303
        },
        {
          "hour": 96.0,
          "value": 0.0371
        },
        {
          "hour": 120.0,
          "value": 0.0461
        },
        {
          "hour": 144.0,
          "value": 0.0549
        },
        {
          "hour": 168.0,
          "value": 0.0625
        }
      ],
      "observed_168h": 0.0625,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 8,
        "board_position": 8,
        "grid_row": 1,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C002039",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Drift is unusually slower than comparable components"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.99787,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.86265,
        "robust_deviation_score": 9.6473,
        "reason_codes": [
          "Drift is unusually slower than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1557329535484314,
        "prediction_lower": 0.0,
        "prediction_upper": 0.46272339833528886,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "percent_change",
              "contribution_ua": -0.030817067250609398,
              "feature_value": -0.3786390092638488
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.025384604930877686,
              "feature_value": -0.0926514082457143
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": -0.01392486784607172,
              "feature_value": -0.013012929750000011
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.011953982524573803,
              "feature_value": 0.740250576971
            },
            {
              "feature": "current_capacitance_fraction",
              "contribution_ua": 0.011526941321790218,
              "feature_value": 1.10334161791
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.5936,
        "headroom_fraction": 0.848,
        "limit_fraction": 0.152
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.43,
        "slope_batch_robust_z": -9.647,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1713,
      "latest_value": 0.1064,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0649,
      "percent_change": -0.3789,
      "percent_change_available": true,
      "slope_per_hour": -0.0027,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1713
        },
        {
          "hour": 24.0,
          "value": 0.1064
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1169
        },
        {
          "hour": 72.0,
          "value": 0.1678
        },
        {
          "hour": 96.0,
          "value": 0.1383
        },
        {
          "hour": 120.0,
          "value": 0.1396
        },
        {
          "hour": 144.0,
          "value": 0.1391
        },
        {
          "hour": 168.0,
          "value": 0.1252
        }
      ],
      "observed_168h": 0.1252,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 9,
        "board_position": 9,
        "grid_row": 2,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C002700",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "RETEST",
      "recommendation_reasons": [
        "Drift is unusually faster than comparable components",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.98521,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.78513,
        "robust_deviation_score": 7.6992,
        "reason_codes": [
          "Drift is unusually faster than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.5487511277198791,
        "prediction_lower": 0.2417606829330216,
        "prediction_upper": 0.8557415725067365,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.2395448386669159,
              "feature_value": 0.05829744618571429
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.03570813313126564,
              "feature_value": 7.6991617045320835
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.030509496107697487,
              "feature_value": 0.15502759663428572
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.02289123646914959,
              "feature_value": 0.0024290602577380937
            },
            {
              "feature": "variability_fraction_of_limit",
              "contribution_ua": -0.020765729248523712,
              "feature_value": 0.029148723092857143
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.5915,
        "headroom_fraction": 0.845,
        "limit_fraction": 0.155
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.521,
        "slope_batch_robust_z": 7.699,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0677,
      "latest_value": 0.1085,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0408,
      "percent_change": 0.6026,
      "percent_change_available": true,
      "slope_per_hour": 0.0017,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0677
        },
        {
          "hour": 24.0,
          "value": 0.1085
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1594
        },
        {
          "hour": 72.0,
          "value": 0.2068
        },
        {
          "hour": 96.0,
          "value": 0.2542
        },
        {
          "hour": 120.0,
          "value": 0.3086
        },
        {
          "hour": 144.0,
          "value": 0.3596
        },
        {
          "hour": 168.0,
          "value": 0.4138
        }
      ],
      "observed_168h": 0.4138,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 10,
        "board_position": 10,
        "grid_row": 2,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000561",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "The combination of early measurements is unusual",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.64088,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.64088,
        "robust_deviation_score": 3.0578,
        "reason_codes": [
          "The combination of early measurements is unusual"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.8085993528366089,
        "prediction_lower": 0.23847424108958779,
        "prediction_upper": 1.3787244645836298,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.40856483578681946,
              "feature_value": 0.04919068574846154
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.04237348213791847,
              "feature_value": 3.057789288974402
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.041164692491292953,
              "feature_value": 0.002049611906185897
            },
            {
              "feature": "variability_fraction_of_limit",
              "contribution_ua": -0.03461795300245285,
              "feature_value": 0.02459534287423077
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.021018169820308685,
              "feature_value": 15.7058373795
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.0917,
        "headroom_fraction": 0.8398,
        "limit_fraction": 0.1602
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.162,
        "slope_batch_robust_z": 3.058,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1444,
      "latest_value": 0.2083,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0639,
      "percent_change": 0.4426,
      "percent_change_available": true,
      "slope_per_hour": 0.00266,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1444
        },
        {
          "hour": 24.0,
          "value": 0.2083
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1969
        },
        {
          "hour": 72.0,
          "value": 0.1434
        },
        {
          "hour": 96.0,
          "value": 0.1591
        },
        {
          "hour": 120.0,
          "value": 0.1458
        },
        {
          "hour": 144.0,
          "value": 0.1672
        },
        {
          "hour": 168.0,
          "value": 0.1808
        }
      ],
      "observed_168h": 0.1808,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 11,
        "board_position": 11,
        "grid_row": 2,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000591",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "The combination of early measurements is unusual"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.70057,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.70057,
        "robust_deviation_score": 2.5946,
        "reason_codes": [
          "The combination of early measurements is unusual"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.03500136733055115,
        "prediction_lower": 0.0,
        "prediction_upper": 0.14464081189728598,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "percent_change",
              "contribution_ua": -0.011526621878147125,
              "feature_value": -0.3650144055409322
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.007972121238708496,
              "feature_value": -0.03923368093879999
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.006673302501440048,
              "feature_value": 0.0682516137324
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.00652516121044755,
              "feature_value": 0.9317483862676
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.0044369748793542385,
              "feature_value": -1.2305209873720877
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2329,
        "headroom_fraction": 0.9317,
        "limit_fraction": 0.0683
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.231,
        "slope_batch_robust_z": -2.595,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0269,
      "latest_value": 0.0171,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0098,
      "percent_change": -0.3647,
      "percent_change_available": true,
      "slope_per_hour": -0.00041,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0269
        },
        {
          "hour": 24.0,
          "value": 0.0171
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0233
        },
        {
          "hour": 72.0,
          "value": 0.0225
        },
        {
          "hour": 96.0,
          "value": 0.023
        },
        {
          "hour": 120.0,
          "value": 0.0269
        },
        {
          "hour": 144.0,
          "value": 0.0232
        },
        {
          "hour": 168.0,
          "value": 0.0224
        }
      ],
      "observed_168h": 0.0224,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 12,
        "board_position": 12,
        "grid_row": 2,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000732",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.47918,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.47918,
        "robust_deviation_score": 3.3497,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.14340311288833618,
        "prediction_lower": 0.03376366832160135,
        "prediction_upper": 0.253042557455071,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.03411329537630081,
              "feature_value": 0.029950042218400003
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.009158595465123653,
              "feature_value": 1.8745584486963502
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.008887899108231068,
              "feature_value": 0.8142276621996
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.00750111136585474,
              "feature_value": 3.3497217167827205
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.005530843045562506,
              "feature_value": 0.1857723378004
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2036,
        "headroom_fraction": 0.8142,
        "limit_fraction": 0.1858
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.875,
        "slope_batch_robust_z": 3.35,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.039,
      "latest_value": 0.0464,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0075,
      "percent_change": 0.1925,
      "percent_change_available": true,
      "slope_per_hour": 0.00031,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.039
        },
        {
          "hour": 24.0,
          "value": 0.0464
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0571
        },
        {
          "hour": 72.0,
          "value": 0.0662
        },
        {
          "hour": 96.0,
          "value": 0.0822
        },
        {
          "hour": 120.0,
          "value": 0.0984
        },
        {
          "hour": 144.0,
          "value": 0.1106
        },
        {
          "hour": 168.0,
          "value": 0.1215
        }
      ],
      "observed_168h": 0.1215,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 13,
        "board_position": 13,
        "grid_row": 2,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000810",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "The combination of early measurements is unusual"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.57342,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.57342,
        "robust_deviation_score": 2.7414,
        "reason_codes": [
          "The combination of early measurements is unusual"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.03174727037549019,
        "prediction_lower": 0.0,
        "prediction_upper": 0.14138671494222502,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "percent_change",
              "contribution_ua": -0.011443562805652618,
              "feature_value": -0.295849676129784
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.007412255275994539,
              "feature_value": -0.040942413126
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.005461325403302908,
              "feature_value": 0.9025531687584
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.005245840642601252,
              "feature_value": 0.0974468312416
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.004961197264492512,
              "feature_value": -0.45913815052955703
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2256,
        "headroom_fraction": 0.9026,
        "limit_fraction": 0.0974
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.459,
        "slope_batch_robust_z": -2.741,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0346,
      "latest_value": 0.0244,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0102,
      "percent_change": -0.2948,
      "percent_change_available": true,
      "slope_per_hour": -0.00043,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0346
        },
        {
          "hour": 24.0,
          "value": 0.0244
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0217
        },
        {
          "hour": 72.0,
          "value": 0.0168
        },
        {
          "hour": 96.0,
          "value": 0.0357
        },
        {
          "hour": 120.0,
          "value": 0.029
        },
        {
          "hour": 144.0,
          "value": 0.0263
        },
        {
          "hour": 168.0,
          "value": 0.0257
        }
      ],
      "observed_168h": 0.0257,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 14,
        "board_position": 14,
        "grid_row": 2,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C002314",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "Drift is unusually slower than comparable components"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.78723,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.78723,
        "robust_deviation_score": 3.82,
        "reason_codes": [
          "Drift is unusually slower than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.02428719960153103,
        "prediction_lower": 0.0,
        "prediction_upper": 0.13392664416826586,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "percent_change",
              "contribution_ua": -0.010908090509474277,
              "feature_value": -0.37661900579498125
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.007430535741150379,
              "feature_value": -0.6942934513298467
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0068526617251336575,
              "feature_value": -0.053495967337999994
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.005963031202554703,
              "feature_value": 0.0885466978352
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.005798441357910633,
              "feature_value": -0.122289414072
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2279,
        "headroom_fraction": 0.9115,
        "limit_fraction": 0.0885
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.694,
        "slope_batch_robust_z": -3.82,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0355,
      "latest_value": 0.0221,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0134,
      "percent_change": -0.3774,
      "percent_change_available": true,
      "slope_per_hour": -0.00056,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0355
        },
        {
          "hour": 24.0,
          "value": 0.0221
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0264
        },
        {
          "hour": 72.0,
          "value": 0.0284
        },
        {
          "hour": 96.0,
          "value": 0.0254
        },
        {
          "hour": 120.0,
          "value": 0.0289
        },
        {
          "hour": 144.0,
          "value": 0.0219
        },
        {
          "hour": 168.0,
          "value": 0.0231
        }
      ],
      "observed_168h": 0.0231,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 15,
        "board_position": 15,
        "grid_row": 2,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C002704",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "Current value is unusually above the batch norm",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.5519,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.5519,
        "robust_deviation_score": 3.645,
        "reason_codes": [
          "Current value is unusually above the batch norm"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.14337672293186188,
        "prediction_lower": 0.03373727836512705,
        "prediction_upper": 0.2530161674985967,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.026964709162712097,
              "feature_value": 0.7472215776755999
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.024420153349637985,
              "feature_value": 0.2527784223244
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.0070554474368691444,
              "feature_value": 1.8669451704155782
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.006026545539498329,
              "feature_value": 0.012692420837200014
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.0025007198564708233,
              "feature_value": 0.0005288508682166649
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.1868,
        "headroom_fraction": 0.7472,
        "limit_fraction": 0.2528
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 3.645,
        "slope_batch_robust_z": 1.867,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.06,
      "latest_value": 0.0632,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0032,
      "percent_change": 0.0533,
      "percent_change_available": true,
      "slope_per_hour": 0.00013,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.06
        },
        {
          "hour": 24.0,
          "value": 0.0632
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0595
        },
        {
          "hour": 72.0,
          "value": 0.0595
        },
        {
          "hour": 96.0,
          "value": 0.0607
        },
        {
          "hour": 120.0,
          "value": 0.0601
        },
        {
          "hour": 144.0,
          "value": 0.0579
        },
        {
          "hour": 168.0,
          "value": 0.0572
        }
      ],
      "observed_168h": 0.0572,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 16,
        "board_position": 16,
        "grid_row": 2,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C002798",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "The combination of early measurements is unusual",
        "The prediction range includes a possible limit crossing"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.62344,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.62344,
        "robust_deviation_score": 3.1855,
        "reason_codes": [
          "The combination of early measurements is unusual"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.07323514938354492,
        "prediction_lower": 0.020608215991512205,
        "prediction_upper": 0.12586208277557762,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": true,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.03195944055914879,
              "feature_value": 0.03771790210858334
            },
            {
              "feature": "variability_fraction_of_limit",
              "contribution_ua": -0.005311538930982351,
              "feature_value": 0.01885895105429167
            },
            {
              "feature": "slope_fraction_per_hour",
              "contribution_ua": 0.004672312643378973,
              "feature_value": 0.001571579254524305
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.004242680501192808,
              "feature_value": 3.185546015584198
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.0033791924361139536,
              "feature_value": 0.07176310327641666
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1069,
        "headroom_fraction": 0.8905,
        "limit_fraction": 0.1095
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.372,
        "slope_batch_robust_z": 3.186,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0086,
      "latest_value": 0.0131,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0045,
      "percent_change": 0.5226,
      "percent_change_available": true,
      "slope_per_hour": 0.00019,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0086
        },
        {
          "hour": 24.0,
          "value": 0.0131
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0254
        },
        {
          "hour": 72.0,
          "value": 0.0417
        },
        {
          "hour": 96.0,
          "value": 0.06
        },
        {
          "hour": 120.0,
          "value": 0.0823
        },
        {
          "hour": 144.0,
          "value": 0.1069
        },
        {
          "hour": 168.0,
          "value": 0.1331
        }
      ],
      "observed_168h": 0.1331,
      "crossed_applicable_limit": true,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 1,
        "board_position": 17,
        "grid_row": 3,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C003039",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "MONITOR",
      "recommendation_reasons": [
        "Drift is unusually slower than comparable components"
      ],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.62832,
        "is_anomaly": true,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.62832,
        "robust_deviation_score": 3.8279,
        "reason_codes": [
          "Drift is unusually slower than comparable components"
        ],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.17547877430915831,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4824692190960158,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.021365130320191383,
              "feature_value": -0.042011200610000014
            },
            {
              "feature": "percent_change",
              "contribution_ua": -0.021253878250718117,
              "feature_value": -0.18895493268341554
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.016006983816623688,
              "feature_value": 2.2933136315257148
            },
            {
              "feature": "current_dissipation_factor_pct",
              "contribution_ua": 0.010750753805041313,
              "feature_value": 1.263767167
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.008043947629630566,
              "feature_value": 0.8196766999257142
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.5738,
        "headroom_fraction": 0.8197,
        "limit_fraction": 0.1803
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 2.293,
        "slope_batch_robust_z": -3.828,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1556,
      "latest_value": 0.1262,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0294,
      "percent_change": -0.1889,
      "percent_change_available": true,
      "slope_per_hour": -0.00123,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1556
        },
        {
          "hour": 24.0,
          "value": 0.1262
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1249
        },
        {
          "hour": 72.0,
          "value": 0.1138
        },
        {
          "hour": 96.0,
          "value": 0.116
        },
        {
          "hour": 120.0,
          "value": 0.1176
        },
        {
          "hour": 144.0,
          "value": 0.122
        },
        {
          "hour": 168.0,
          "value": 0.1129
        }
      ],
      "observed_168h": 0.1129,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": true,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 2,
        "board_position": 18,
        "grid_row": 3,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000005",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.09682,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00022,
        "robust_deviation_score": 1.267,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.21591844856739045,
        "prediction_lower": 0.0,
        "prediction_upper": 0.7860435603144116,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.043691884726285934,
              "feature_value": 0.06669439226215385
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.03082089312374592,
              "feature_value": -0.003109394613538466
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.03022390604019165,
              "feature_value": -1.2669702331249548
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.028988925740122795,
              "feature_value": 0.9333056077378462
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.020016243681311607,
              "feature_value": 0.0698037868756923
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.2133,
        "headroom_fraction": 0.9333,
        "limit_fraction": 0.0667
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.267,
        "slope_batch_robust_z": 0.397,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0907,
      "latest_value": 0.0867,
      "last_observation_hour": 24.0,
      "absolute_change": -0.004,
      "percent_change": -0.0441,
      "percent_change_available": true,
      "slope_per_hour": -0.00017,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0907
        },
        {
          "hour": 24.0,
          "value": 0.0867
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0829
        },
        {
          "hour": 72.0,
          "value": 0.0844
        },
        {
          "hour": 96.0,
          "value": 0.0819
        },
        {
          "hour": 120.0,
          "value": 0.0824
        },
        {
          "hour": 144.0,
          "value": 0.0834
        },
        {
          "hour": 168.0,
          "value": 0.0835
        }
      ],
      "observed_168h": 0.0835,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 3,
        "board_position": 19,
        "grid_row": 3,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000039",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.07243,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.95,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.02463306963443756,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07726000302647028,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.004959983751177788,
              "feature_value": -0.9499917492570843
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0031470751855522394,
              "feature_value": 0.06900641563875
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.002772032981738448,
              "feature_value": 0.93099358436125
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0027395503129810095,
              "feature_value": -0.006232380628916678
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0025588059797883034,
              "feature_value": 0.995600247908
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1117,
        "headroom_fraction": 0.931,
        "limit_fraction": 0.069
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.95,
        "slope_batch_robust_z": 0.09,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.009,
      "latest_value": 0.0083,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0007,
      "percent_change": -0.0775,
      "percent_change_available": true,
      "slope_per_hour": -3e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.009
        },
        {
          "hour": 24.0,
          "value": 0.0083
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0086
        },
        {
          "hour": 72.0,
          "value": 0.0082
        },
        {
          "hour": 96.0,
          "value": 0.0082
        },
        {
          "hour": 120.0,
          "value": 0.008
        },
        {
          "hour": 144.0,
          "value": 0.0082
        },
        {
          "hour": 168.0,
          "value": 0.0086
        }
      ],
      "observed_168h": 0.0086,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 4,
        "board_position": 20,
        "grid_row": 3,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000062",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.08817,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 1e-05,
        "robust_deviation_score": 1.1638,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.03828968480229378,
        "prediction_lower": 0.0,
        "prediction_upper": 0.1479291293690286,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.008136757649481297,
              "feature_value": 0.070776204774
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.007151707541197538,
              "feature_value": -1.163817384327412
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.006483107805252075,
              "feature_value": 0.929223795226
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.006254430860280991,
              "feature_value": -0.007093966131200002
            },
            {
              "feature": "current_capacitance_fraction",
              "contribution_ua": -0.0035530810710042715,
              "feature_value": 0.947479062165
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2323,
        "headroom_fraction": 0.9292,
        "limit_fraction": 0.0708
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.164,
        "slope_batch_robust_z": 0.167,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0195,
      "latest_value": 0.0177,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0018,
      "percent_change": -0.0925,
      "percent_change_available": true,
      "slope_per_hour": -7e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0195
        },
        {
          "hour": 24.0,
          "value": 0.0177
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0182
        },
        {
          "hour": 72.0,
          "value": 0.0171
        },
        {
          "hour": 96.0,
          "value": 0.0186
        },
        {
          "hour": 120.0,
          "value": 0.018
        },
        {
          "hour": 144.0,
          "value": 0.0176
        },
        {
          "hour": 168.0,
          "value": 0.0182
        }
      ],
      "observed_168h": 0.0182,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 5,
        "board_position": 21,
        "grid_row": 3,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000068",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05938,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.7375,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.30856375843286515,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8786888701798863,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.03532642498612404,
              "feature_value": -0.009667689673846151
            },
            {
              "feature": "current_dissipation_factor_pct",
              "contribution_ua": 0.014393203891813755,
              "feature_value": 1.20078282423
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.012736794538795948,
              "feature_value": 14.0547347969
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.012150767259299755,
              "feature_value": 15.7058373795
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": -0.009708019904792309,
              "feature_value": 0.06293128333625092
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.113,
        "headroom_fraction": 0.8561,
        "limit_fraction": 0.1439
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.737,
        "slope_batch_robust_z": 0.063,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1996,
      "latest_value": 0.187,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0126,
      "percent_change": -0.0631,
      "percent_change_available": true,
      "slope_per_hour": -0.00052,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1996
        },
        {
          "hour": 24.0,
          "value": 0.187
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1405
        },
        {
          "hour": 72.0,
          "value": 0.1672
        },
        {
          "hour": 96.0,
          "value": 0.1698
        },
        {
          "hour": 120.0,
          "value": 0.1899
        },
        {
          "hour": 144.0,
          "value": 0.1762
        },
        {
          "hour": 168.0,
          "value": 0.2207
        }
      ],
      "observed_168h": 0.2207,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 6,
        "board_position": 22,
        "grid_row": 3,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000082",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04423,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.4269,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.15175040662288664,
        "prediction_lower": 0.0,
        "prediction_upper": 0.45874085140974413,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.016107074916362762,
              "feature_value": 0.8902483322147143
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.01584552228450775,
              "feature_value": -0.012415299626285714
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0156058045104146,
              "feature_value": 0.10975166778528572
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.005019443575292826,
              "feature_value": 0.697229845609
            },
            {
              "feature": "current_dissipation_factor_pct",
              "contribution_ua": 0.004460291936993599,
              "feature_value": 0.742260625465
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6232,
        "headroom_fraction": 0.8902,
        "limit_fraction": 0.1098
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.138,
        "slope_batch_robust_z": -0.427,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0855,
      "latest_value": 0.0768,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0087,
      "percent_change": -0.1017,
      "percent_change_available": true,
      "slope_per_hour": -0.00036,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0855
        },
        {
          "hour": 24.0,
          "value": 0.0768
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0704
        },
        {
          "hour": 72.0,
          "value": 0.071
        },
        {
          "hour": 96.0,
          "value": 0.0765
        },
        {
          "hour": 120.0,
          "value": 0.067
        },
        {
          "hour": 144.0,
          "value": 0.0707
        },
        {
          "hour": 168.0,
          "value": 0.0727
        }
      ],
      "observed_168h": 0.0727,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 7,
        "board_position": 23,
        "grid_row": 3,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000090",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.08333,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 4e-05,
        "robust_deviation_score": 1.102,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.041742317378520966,
        "prediction_lower": 0.0,
        "prediction_upper": 0.1513817619452558,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.009635349735617638,
              "feature_value": -1.102039404752187
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.00698004849255085,
              "feature_value": 0.07311437133
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.006514851003885269,
              "feature_value": 0.92688562867
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.005497469566762447,
              "feature_value": -0.013013677356800007
            },
            {
              "feature": "percent_change",
              "contribution_ua": -0.004331027157604694,
              "feature_value": -0.15109685584685126
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2317,
        "headroom_fraction": 0.9269,
        "limit_fraction": 0.0731
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.102,
        "slope_batch_robust_z": -0.342,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0215,
      "latest_value": 0.0183,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0033,
      "percent_change": -0.1533,
      "percent_change_available": true,
      "slope_per_hour": -0.00014,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0215
        },
        {
          "hour": 24.0,
          "value": 0.0183
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0189
        },
        {
          "hour": 72.0,
          "value": 0.018
        },
        {
          "hour": 96.0,
          "value": 0.0182
        },
        {
          "hour": 120.0,
          "value": 0.0191
        },
        {
          "hour": 144.0,
          "value": 0.0188
        },
        {
          "hour": 168.0,
          "value": 0.0194
        }
      ],
      "observed_168h": 0.0194,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 8,
        "board_position": 24,
        "grid_row": 3,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000097",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.1782,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.02279,
        "robust_deviation_score": 1.9714,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.09745414555072784,
        "prediction_lower": 0.0,
        "prediction_upper": 0.20709359011746267,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.013507084921002388,
              "feature_value": 0.013908373437999999
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.009748979471623898,
              "feature_value": 1.971419938874952
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": 0.004136343020945787,
              "feature_value": 0.08493832857400008
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.003730570198968053,
              "feature_value": 0.814179688687
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0034498809836804867,
              "feature_value": 0.1378709781152
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2155,
        "headroom_fraction": 0.8621,
        "limit_fraction": 0.1379
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.609,
        "slope_batch_robust_z": 1.971,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.031,
      "latest_value": 0.0345,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0035,
      "percent_change": 0.1129,
      "percent_change_available": true,
      "slope_per_hour": 0.00014,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.031
        },
        {
          "hour": 24.0,
          "value": 0.0345
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0457
        },
        {
          "hour": 72.0,
          "value": 0.0578
        },
        {
          "hour": 96.0,
          "value": 0.0813
        },
        {
          "hour": 120.0,
          "value": 0.0954
        },
        {
          "hour": 144.0,
          "value": 0.1165
        },
        {
          "hour": 168.0,
          "value": 0.1436
        }
      ],
      "observed_168h": 0.1436,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 9,
        "board_position": 25,
        "grid_row": 4,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000107",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05954,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.7404,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.35897092521190643,
        "prediction_lower": 0.0,
        "prediction_upper": 0.9290960369589276,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.030885659158229828,
              "feature_value": -0.02121146800307693
            },
            {
              "feature": "current_capacitance_fraction",
              "contribution_ua": 0.017696799710392952,
              "feature_value": 1.0794591524553192
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.015196837484836578,
              "feature_value": 0.624089164243
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.011139191687107086,
              "feature_value": 15.7058373795
            },
            {
              "feature": "variability_fraction_of_limit",
              "contribution_ua": 0.010705114342272282,
              "feature_value": 0.010605734001538464
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1128,
        "headroom_fraction": 0.856,
        "limit_fraction": 0.144
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.74,
        "slope_batch_robust_z": -0.524,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.2148,
      "latest_value": 0.1872,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0276,
      "percent_change": -0.1285,
      "percent_change_available": true,
      "slope_per_hour": -0.00115,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.2148
        },
        {
          "hour": 24.0,
          "value": 0.1872
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1682
        },
        {
          "hour": 72.0,
          "value": 0.1789
        },
        {
          "hour": 96.0,
          "value": 0.1855
        },
        {
          "hour": 120.0,
          "value": 0.1753
        },
        {
          "hour": 144.0,
          "value": 0.1821
        },
        {
          "hour": 168.0,
          "value": 0.181
        }
      ],
      "observed_168h": 0.181,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 10,
        "board_position": 26,
        "grid_row": 4,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000114",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.03807,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.2705,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.06031082198023796,
        "prediction_lower": 0.0,
        "prediction_upper": 0.1699502665469728,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.005950700957328081,
              "feature_value": -0.005888149315999999
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.005831216461956501,
              "feature_value": 0.8853338598632
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0049103605560958385,
              "feature_value": 0.1146661401368
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": 0.0033457474783062935,
              "feature_value": 50.1369856847
            },
            {
              "feature": "measurement_temperature_c",
              "contribution_ua": 0.002111292677000165,
              "feature_value": 26.5854332302
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2213,
        "headroom_fraction": 0.8853,
        "limit_fraction": 0.1147
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.004,
        "slope_batch_robust_z": 0.271,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0301,
      "latest_value": 0.0287,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0015,
      "percent_change": -0.0498,
      "percent_change_available": true,
      "slope_per_hour": -6e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0301
        },
        {
          "hour": 24.0,
          "value": 0.0287
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0281
        },
        {
          "hour": 72.0,
          "value": 0.0283
        },
        {
          "hour": 96.0,
          "value": 0.0279
        },
        {
          "hour": 120.0,
          "value": 0.0271
        },
        {
          "hour": 144.0,
          "value": 0.0278
        },
        {
          "hour": 168.0,
          "value": 0.0276
        }
      ],
      "observed_168h": 0.0276,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 11,
        "board_position": 27,
        "grid_row": 4,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000125",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04889,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.5319,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.023800885677337645,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07642781906937036,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0034665660932660103,
              "feature_value": -0.01123809209333334
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0026839894708245993,
              "feature_value": 0.11437253970666668
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0026595378294587135,
              "feature_value": 0.8856274602933333
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.002066451357677579,
              "feature_value": 0.995600247908
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.0017954851500689983,
              "feature_value": 26.9994625407
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1063,
        "headroom_fraction": 0.8856,
        "limit_fraction": 0.1144
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.532,
        "slope_batch_robust_z": -0.262,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0151,
      "latest_value": 0.0137,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0013,
      "percent_change": -0.0862,
      "percent_change_available": true,
      "slope_per_hour": -6e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0151
        },
        {
          "hour": 24.0,
          "value": 0.0137
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0133
        },
        {
          "hour": 72.0,
          "value": 0.0127
        },
        {
          "hour": 96.0,
          "value": 0.0131
        },
        {
          "hour": 120.0,
          "value": 0.0143
        },
        {
          "hour": 144.0,
          "value": 0.0134
        },
        {
          "hour": 168.0,
          "value": 0.0148
        }
      ],
      "observed_168h": 0.0148,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 12,
        "board_position": 28,
        "grid_row": 4,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000128",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.12547,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00175,
        "robust_deviation_score": 1.5584,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.17957278490066528,
        "prediction_lower": 0.0,
        "prediction_upper": 0.48656322968752275,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.015611461363732815,
              "feature_value": 0.0048601207268571455
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.01514720730483532,
              "feature_value": 0.568391826849
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.010472727939486504,
              "feature_value": 0.13640540514414287
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0056752716191112995,
              "feature_value": 0.8635945948558571
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.0052440776489675045,
              "feature_value": 0.9521989266708141
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6045,
        "headroom_fraction": 0.8636,
        "limit_fraction": 0.1364
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.952,
        "slope_batch_robust_z": 1.558,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0921,
      "latest_value": 0.0955,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0034,
      "percent_change": 0.0369,
      "percent_change_available": true,
      "slope_per_hour": 0.00014,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0921
        },
        {
          "hour": 24.0,
          "value": 0.0955
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0882
        },
        {
          "hour": 72.0,
          "value": 0.0896
        },
        {
          "hour": 96.0,
          "value": 0.0829
        },
        {
          "hour": 120.0,
          "value": 0.0835
        },
        {
          "hour": 144.0,
          "value": 0.087
        },
        {
          "hour": 168.0,
          "value": 0.0817
        }
      ],
      "observed_168h": 0.0817,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 13,
        "board_position": 29,
        "grid_row": 4,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000157",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.0644,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.824,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.23031138330698014,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8004364950540013,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.048984795808792114,
              "feature_value": -0.8239585516123883
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.037007976323366165,
              "feature_value": 0.08375213146999999
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.030096659436821938,
              "feature_value": -0.0040483402430769285
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.028831584379076958,
              "feature_value": 0.91624786853
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.015026125125586987,
              "feature_value": 0.08780047171307692
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1911,
        "headroom_fraction": 0.9162,
        "limit_fraction": 0.0838
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.824,
        "slope_batch_robust_z": 0.349,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1141,
      "latest_value": 0.1089,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0053,
      "percent_change": -0.0464,
      "percent_change_available": true,
      "slope_per_hour": -0.00022,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1141
        },
        {
          "hour": 24.0,
          "value": 0.1089
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1076
        },
        {
          "hour": 72.0,
          "value": 0.1036
        },
        {
          "hour": 96.0,
          "value": 0.1082
        },
        {
          "hour": 120.0,
          "value": 0.1038
        },
        {
          "hour": 144.0,
          "value": 0.1028
        },
        {
          "hour": 168.0,
          "value": 0.1057
        }
      ],
      "observed_168h": 0.1057,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 14,
        "board_position": 30,
        "grid_row": 4,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000178",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04122,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.3533,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1475596711039543,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4545501158908118,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.01722014509141445,
              "feature_value": -0.008381622837999989
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.015566120855510235,
              "feature_value": 0.0936532316167143
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.01500289048999548,
              "feature_value": 0.9063467683832858
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.007397715002298355,
              "feature_value": 0.746222624754
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": 0.005539587698876858,
              "feature_value": -0.002832793209999977
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6344,
        "headroom_fraction": 0.9063,
        "limit_fraction": 0.0937
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.353,
        "slope_batch_robust_z": 0.037,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0714,
      "latest_value": 0.0656,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0059,
      "percent_change": -0.0826,
      "percent_change_available": true,
      "slope_per_hour": -0.00024,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0714
        },
        {
          "hour": 24.0,
          "value": 0.0656
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0589
        },
        {
          "hour": 72.0,
          "value": 0.06
        },
        {
          "hour": 96.0,
          "value": 0.0586
        },
        {
          "hour": 120.0,
          "value": 0.0619
        },
        {
          "hour": 144.0,
          "value": 0.0593
        },
        {
          "hour": 168.0,
          "value": 0.0614
        }
      ],
      "observed_168h": 0.0614,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 15,
        "board_position": 31,
        "grid_row": 4,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000184",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.20694,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.01597,
        "robust_deviation_score": 2.1565,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.22233653068542478,
        "prediction_lower": 0.0,
        "prediction_upper": 0.5293269754722822,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.02589886076748371,
              "feature_value": 2.15652567427339
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.024283982813358307,
              "feature_value": 0.01006532665871428
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.019976580515503883,
              "feature_value": 0.09835978508085715
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.017449934035539627,
              "feature_value": -0.20959492987341952
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.015913648530840874,
              "feature_value": 0.9016402149191429
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6311,
        "headroom_fraction": 0.9016,
        "limit_fraction": 0.0984
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.21,
        "slope_batch_robust_z": 2.157,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0618,
      "latest_value": 0.0689,
      "last_observation_hour": 24.0,
      "absolute_change": 0.007,
      "percent_change": 0.1133,
      "percent_change_available": true,
      "slope_per_hour": 0.00029,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0618
        },
        {
          "hour": 24.0,
          "value": 0.0689
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0452
        },
        {
          "hour": 72.0,
          "value": 0.051
        },
        {
          "hour": 96.0,
          "value": 0.0778
        },
        {
          "hour": 120.0,
          "value": 0.0447
        },
        {
          "hour": 144.0,
          "value": 0.0486
        },
        {
          "hour": 168.0,
          "value": 0.0668
        }
      ],
      "observed_168h": 0.0668,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 16,
        "board_position": 32,
        "grid_row": 4,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000197",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.0608,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 7e-05,
        "robust_deviation_score": 0.7626,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1969828948378563,
        "prediction_lower": 0.0,
        "prediction_upper": 0.7671080065848774,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.05209504812955856,
              "feature_value": -0.7626134650554581
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.03373166546225548,
              "feature_value": 0.08611416509538461
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.032028790563344955,
              "feature_value": 0.9138858349046154
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.031436674296855927,
              "feature_value": 0.001679072429230772
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.020123571157455444,
              "feature_value": 0.08443509266615384
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1881,
        "headroom_fraction": 0.9139,
        "limit_fraction": 0.0861
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.763,
        "slope_batch_robust_z": 0.64,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1098,
      "latest_value": 0.1119,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0022,
      "percent_change": 0.02,
      "percent_change_available": true,
      "slope_per_hour": 9e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1098
        },
        {
          "hour": 24.0,
          "value": 0.1119
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1041
        },
        {
          "hour": 72.0,
          "value": 0.1081
        },
        {
          "hour": 96.0,
          "value": 0.0934
        },
        {
          "hour": 120.0,
          "value": 0.1083
        },
        {
          "hour": 144.0,
          "value": 0.1042
        },
        {
          "hour": 168.0,
          "value": 0.1099
        }
      ],
      "observed_168h": 0.1099,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 1,
        "board_position": 33,
        "grid_row": 5,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000203",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.07658,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00025,
        "robust_deviation_score": 1.0103,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.20177703350782394,
        "prediction_lower": 0.0,
        "prediction_upper": 0.7719021452548451,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.03851420059800148,
              "feature_value": -1.0102861504607288
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.031837448477745056,
              "feature_value": 0.076577766276
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.028722595423460007,
              "feature_value": -0.01600232701784615
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.02823927439749241,
              "feature_value": 0.923422233724
            },
            {
              "feature": "percent_change",
              "contribution_ua": -0.02734340727329254,
              "feature_value": -0.1728484650264425
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.2004,
        "headroom_fraction": 0.9234,
        "limit_fraction": 0.0766
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.01,
        "slope_batch_robust_z": -0.259,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1204,
      "latest_value": 0.0996,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0208,
      "percent_change": -0.1728,
      "percent_change_available": true,
      "slope_per_hour": -0.00087,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1204
        },
        {
          "hour": 24.0,
          "value": 0.0996
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0911
        },
        {
          "hour": 72.0,
          "value": 0.1038
        },
        {
          "hour": 96.0,
          "value": 0.1258
        },
        {
          "hour": 120.0,
          "value": 0.1227
        },
        {
          "hour": 144.0,
          "value": 0.118
        },
        {
          "hour": 168.0,
          "value": 0.1038
        }
      ],
      "observed_168h": 0.1038,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 2,
        "board_position": 34,
        "grid_row": 5,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000273",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.07546,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 1e-05,
        "robust_deviation_score": 0.9942,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.07079150527715683,
        "prediction_lower": 0.0,
        "prediction_upper": 0.18043094984389166,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.009018282406032085,
              "feature_value": 0.576708842607
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.006987780332565308,
              "feature_value": -0.5056421959357396
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.006268954370170832,
              "feature_value": 0.09568675096
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.00604643952101469,
              "feature_value": 0.90431324904
            },
            {
              "feature": "current_dissipation_factor_pct",
              "contribution_ua": 0.005658977665007114,
              "feature_value": 0.633728023389
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2261,
        "headroom_fraction": 0.9043,
        "limit_fraction": 0.0957
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.506,
        "slope_batch_robust_z": 0.994,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0233,
      "latest_value": 0.0239,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0006,
      "percent_change": 0.0258,
      "percent_change_available": true,
      "slope_per_hour": 3e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0233
        },
        {
          "hour": 24.0,
          "value": 0.0239
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0225
        },
        {
          "hour": 72.0,
          "value": 0.0199
        },
        {
          "hour": 96.0,
          "value": 0.0208
        },
        {
          "hour": 120.0,
          "value": 0.0261
        },
        {
          "hour": 144.0,
          "value": 0.02
        },
        {
          "hour": 168.0,
          "value": 0.0218
        }
      ],
      "observed_168h": 0.0218,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 3,
        "board_position": 35,
        "grid_row": 5,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000281",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.14389,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.14389,
        "robust_deviation_score": 1.2596,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.24790090769529344,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8180260194423146,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "percent_change",
              "contribution_ua": -0.04950613155961037,
              "feature_value": -0.2501200903744515
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.038781359791755676,
              "feature_value": -0.03565924103384615
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.03371540084481239,
              "feature_value": 0.531176094633
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.025214506313204765,
              "feature_value": 0.8930907613069231
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.024587830528616905,
              "feature_value": 0.10690923869307692
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.161,
        "headroom_fraction": 0.8931,
        "limit_fraction": 0.1069
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.223,
        "slope_batch_robust_z": -1.26,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1853,
      "latest_value": 0.139,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0464,
      "percent_change": -0.2504,
      "percent_change_available": true,
      "slope_per_hour": -0.00193,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1853
        },
        {
          "hour": 24.0,
          "value": 0.139
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1454
        },
        {
          "hour": 72.0,
          "value": 0.1707
        },
        {
          "hour": 96.0,
          "value": 0.1722
        },
        {
          "hour": 120.0,
          "value": 0.1574
        },
        {
          "hour": 144.0,
          "value": 0.1605
        },
        {
          "hour": 168.0,
          "value": 0.1808
        }
      ],
      "observed_168h": 0.1808,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 4,
        "board_position": 36,
        "grid_row": 5,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000285",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.07111,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 4e-05,
        "robust_deviation_score": 0.9303,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.05274307355284691,
        "prediction_lower": 0.0,
        "prediction_upper": 0.16238251811958174,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.007803403306752443,
              "feature_value": -0.6597436544048815
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.007064865902066231,
              "feature_value": 0.0898543349616
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.006537716835737228,
              "feature_value": 0.9101456650384
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.006142251193523407,
              "feature_value": 0.0017911035864000002
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.003659092588350177,
              "feature_value": 0.0880632313752
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2275,
        "headroom_fraction": 0.9101,
        "limit_fraction": 0.0899
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.66,
        "slope_batch_robust_z": 0.93,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.022,
      "latest_value": 0.0225,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0004,
      "percent_change": 0.0182,
      "percent_change_available": true,
      "slope_per_hour": 2e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.022
        },
        {
          "hour": 24.0,
          "value": 0.0225
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0233
        },
        {
          "hour": 72.0,
          "value": 0.0245
        },
        {
          "hour": 96.0,
          "value": 0.0291
        },
        {
          "hour": 120.0,
          "value": 0.0374
        },
        {
          "hour": 144.0,
          "value": 0.0485
        },
        {
          "hour": 168.0,
          "value": 0.0646
        }
      ],
      "observed_168h": 0.0646,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 5,
        "board_position": 37,
        "grid_row": 5,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000302",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.06148,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00021,
        "robust_deviation_score": 0.7743,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.2727417305111885,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8428668422582096,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.039811160415410995,
              "feature_value": -0.026122549108461523
            },
            {
              "feature": "percent_change",
              "contribution_ua": -0.028191102668642998,
              "feature_value": -0.15720661045688988
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.017783256247639656,
              "feature_value": 0.88629276476
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.014839494600892067,
              "feature_value": 15.7058373795
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.011508327908813953,
              "feature_value": 31.2789215518
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1179,
        "headroom_fraction": 0.86,
        "limit_fraction": 0.14
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.638,
        "slope_batch_robust_z": -0.774,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.216,
      "latest_value": 0.1821,
      "last_observation_hour": 24.0,
      "absolute_change": -0.034,
      "percent_change": -0.1574,
      "percent_change_available": true,
      "slope_per_hour": -0.00141,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.216
        },
        {
          "hour": 24.0,
          "value": 0.1821
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1104
        },
        {
          "hour": 72.0,
          "value": 0.1318
        },
        {
          "hour": 96.0,
          "value": 0.1201
        },
        {
          "hour": 120.0,
          "value": 0.1281
        },
        {
          "hour": 144.0,
          "value": 0.1305
        },
        {
          "hour": 168.0,
          "value": 0.1371
        }
      ],
      "observed_168h": 0.1371,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 6,
        "board_position": 38,
        "grid_row": 5,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000318",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.09348,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00088,
        "robust_deviation_score": 1.2281,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.0853935495018959,
        "prediction_lower": 0.0,
        "prediction_upper": 0.3923839942887534,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.02920772321522236,
              "feature_value": 0.06500507588114286
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.02298280969262123,
              "feature_value": -1.2281430878634305
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.019674142822623253,
              "feature_value": -0.085986836756
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.016417240723967552,
              "feature_value": -0.0025381482045714276
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.015897078439593315,
              "feature_value": 0.9349949241188572
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6545,
        "headroom_fraction": 0.935,
        "limit_fraction": 0.065
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.228,
        "slope_batch_robust_z": 0.708,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0473,
      "latest_value": 0.0455,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0018,
      "percent_change": -0.0381,
      "percent_change_available": true,
      "slope_per_hour": -7e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0473
        },
        {
          "hour": 24.0,
          "value": 0.0455
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0446
        },
        {
          "hour": 72.0,
          "value": 0.0409
        },
        {
          "hour": 96.0,
          "value": 0.0404
        },
        {
          "hour": 120.0,
          "value": 0.0431
        },
        {
          "hour": 144.0,
          "value": 0.0431
        },
        {
          "hour": 168.0,
          "value": 0.0406
        }
      ],
      "observed_168h": 0.0406,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 7,
        "board_position": 39,
        "grid_row": 5,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000327",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.03399,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.153,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.22443830966949463,
        "prediction_lower": 0.0,
        "prediction_upper": 0.7945634214165158,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.04564294219017029,
              "feature_value": -0.08692235627300005
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.032031744718551636,
              "feature_value": -0.011289779380000014
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.029493391513824463,
              "feature_value": 0.890413872516923
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.026744598522782326,
              "feature_value": 0.10958612748307692
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.013730854727327824,
              "feature_value": 0.809903207378
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1575,
        "headroom_fraction": 0.8904,
        "limit_fraction": 0.1096
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.153,
        "slope_batch_robust_z": -0.02,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1571,
      "latest_value": 0.1425,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0147,
      "percent_change": -0.0935,
      "percent_change_available": true,
      "slope_per_hour": -0.00061,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1571
        },
        {
          "hour": 24.0,
          "value": 0.1425
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.141
        },
        {
          "hour": 72.0,
          "value": 0.1446
        },
        {
          "hour": 96.0,
          "value": 0.1412
        },
        {
          "hour": 120.0,
          "value": 0.1437
        },
        {
          "hour": 144.0,
          "value": 0.1405
        },
        {
          "hour": 168.0,
          "value": 0.1413
        }
      ],
      "observed_168h": 0.1413,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 8,
        "board_position": 40,
        "grid_row": 5,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000346",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.07306,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.9594,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.13432281315326688,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4413132579401244,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.02915176935493946,
              "feature_value": -0.9594472847035564
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.019330549985170364,
              "feature_value": 0.07380413983042858
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.017757654190063477,
              "feature_value": 0.9261958601695714
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.015706511214375496,
              "feature_value": -0.0051818068050000065
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.009646001271903515,
              "feature_value": 0.07898594663542859
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6483,
        "headroom_fraction": 0.9262,
        "limit_fraction": 0.0738
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.959,
        "slope_batch_robust_z": 0.404,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0553,
      "latest_value": 0.0517,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0036,
      "percent_change": -0.0651,
      "percent_change_available": true,
      "slope_per_hour": -0.00015,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0553
        },
        {
          "hour": 24.0,
          "value": 0.0517
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0492
        },
        {
          "hour": 72.0,
          "value": 0.0505
        },
        {
          "hour": 96.0,
          "value": 0.0498
        },
        {
          "hour": 120.0,
          "value": 0.0479
        },
        {
          "hour": 144.0,
          "value": 0.0519
        },
        {
          "hour": 168.0,
          "value": 0.0513
        }
      ],
      "observed_168h": 0.0513,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 9,
        "board_position": 41,
        "grid_row": 6,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000372",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.14907,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.1192,
        "robust_deviation_score": 1.7581,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.05289364457130432,
        "prediction_lower": 0.0002667111792716037,
        "prediction_upper": 0.10552057796333704,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.0067315963096916676,
              "feature_value": 0.017449469766666663
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.0039833043701946735,
              "feature_value": 1.7581050303406007
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0029003769159317017,
              "feature_value": 0.995600247908
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.0018239801283925772,
              "feature_value": 1.4472175639064604
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": 0.0015888625057414174,
              "feature_value": -0.00039435702400005825
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1029,
        "headroom_fraction": 0.8576,
        "limit_fraction": 0.1424
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.447,
        "slope_batch_robust_z": 1.758,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.015,
      "latest_value": 0.0171,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0021,
      "percent_change": 0.1401,
      "percent_change_available": true,
      "slope_per_hour": 9e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.015
        },
        {
          "hour": 24.0,
          "value": 0.0171
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0205
        },
        {
          "hour": 72.0,
          "value": 0.023
        },
        {
          "hour": 96.0,
          "value": 0.0262
        },
        {
          "hour": 120.0,
          "value": 0.0298
        },
        {
          "hour": 144.0,
          "value": 0.0339
        },
        {
          "hour": 168.0,
          "value": 0.0366
        }
      ],
      "observed_168h": 0.0366,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 10,
        "board_position": 42,
        "grid_row": 6,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000395",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.11176,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00287,
        "robust_deviation_score": 1.4271,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.08929843455553055,
        "prediction_lower": 0.0,
        "prediction_upper": 0.19893787912226538,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": 0.003133315360173583,
              "feature_value": 47.5991259498
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.002583110239356756,
              "feature_value": 0.1521320097284
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.0025633317418396473,
              "feature_value": 0.9857289103544777
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.002449618885293603,
              "feature_value": 0.723513814902
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.002079510362818837,
              "feature_value": 0.007572980116799993
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.212,
        "headroom_fraction": 0.8479,
        "limit_fraction": 0.1521
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.986,
        "slope_batch_robust_z": 1.427,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0361,
      "latest_value": 0.038,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0019,
      "percent_change": 0.0526,
      "percent_change_available": true,
      "slope_per_hour": 8e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0361
        },
        {
          "hour": 24.0,
          "value": 0.038
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0326
        },
        {
          "hour": 72.0,
          "value": 0.0339
        },
        {
          "hour": 96.0,
          "value": 0.0343
        },
        {
          "hour": 120.0,
          "value": 0.0347
        },
        {
          "hour": 144.0,
          "value": 0.034
        },
        {
          "hour": 168.0,
          "value": 0.032
        }
      ],
      "observed_168h": 0.032,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 11,
        "board_position": 43,
        "grid_row": 6,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000397",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05848,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 2e-05,
        "robust_deviation_score": 0.7212,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.03158548235893249,
        "prediction_lower": 0.0,
        "prediction_upper": 0.0842124157509652,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": 0.0028731597121804953,
              "feature_value": -0.05890081806399994
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0027928513009101152,
              "feature_value": 0.10837122943666667
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.00266071199439466,
              "feature_value": 0.8916287705633333
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.002518682973459363,
              "feature_value": 0.995600247908
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0024311223533004522,
              "feature_value": 0.0027264129525000035
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.107,
        "headroom_fraction": 0.8916,
        "limit_fraction": 0.1084
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.336,
        "slope_batch_robust_z": 0.721,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0127,
      "latest_value": 0.013,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0003,
      "percent_change": 0.0237,
      "percent_change_available": true,
      "slope_per_hour": 1e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0127
        },
        {
          "hour": 24.0,
          "value": 0.013
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.012
        },
        {
          "hour": 72.0,
          "value": 0.0126
        },
        {
          "hour": 96.0,
          "value": 0.0127
        },
        {
          "hour": 120.0,
          "value": 0.0129
        },
        {
          "hour": 144.0,
          "value": 0.0121
        },
        {
          "hour": 168.0,
          "value": 0.0121
        }
      ],
      "observed_168h": 0.0121,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 12,
        "board_position": 44,
        "grid_row": 6,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000413",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.08273,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 4e-05,
        "robust_deviation_score": 1.0942,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.0281842839717865,
        "prediction_lower": 0.0,
        "prediction_upper": 0.08081121736381922,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.0042721545323729515,
              "feature_value": -1.0941913264616472
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.003453390207141638,
              "feature_value": 0.06459192903533334
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.003168614814057946,
              "feature_value": -0.0053489863354166615
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0028953058645129204,
              "feature_value": 0.9354080709646666
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0027570610400289297,
              "feature_value": 0.995600247908
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1122,
        "headroom_fraction": 0.9354,
        "limit_fraction": 0.0646
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.094,
        "slope_batch_robust_z": 0.152,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0084,
      "latest_value": 0.0078,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0006,
      "percent_change": -0.0715,
      "percent_change_available": true,
      "slope_per_hour": -3e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0084
        },
        {
          "hour": 24.0,
          "value": 0.0078
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0076
        },
        {
          "hour": 72.0,
          "value": 0.0076
        },
        {
          "hour": 96.0,
          "value": 0.0075
        },
        {
          "hour": 120.0,
          "value": 0.0072
        },
        {
          "hour": 144.0,
          "value": 0.0079
        },
        {
          "hour": 168.0,
          "value": 0.0074
        }
      ],
      "observed_168h": 0.0074,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 13,
        "board_position": 45,
        "grid_row": 6,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000434",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05058,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.5678,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.05152398347854614,
        "prediction_lower": 0.0,
        "prediction_upper": 0.16116342804528097,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.006312795914709568,
              "feature_value": -0.00893601137439999
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.006022614426910877,
              "feature_value": -0.5678060059290642
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.005895824637264013,
              "feature_value": 0.9066660184656
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0054649715311825275,
              "feature_value": 0.0933339815344
            },
            {
              "feature": "measurement_temperature_c",
              "contribution_ua": 0.0026226441841572523,
              "feature_value": 26.5854332302
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2267,
        "headroom_fraction": 0.9067,
        "limit_fraction": 0.0933
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.568,
        "slope_batch_robust_z": 0.009,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0256,
      "latest_value": 0.0233,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0022,
      "percent_change": -0.086,
      "percent_change_available": true,
      "slope_per_hour": -9e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0256
        },
        {
          "hour": 24.0,
          "value": 0.0233
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0223
        },
        {
          "hour": 72.0,
          "value": 0.0258
        },
        {
          "hour": 96.0,
          "value": 0.0233
        },
        {
          "hour": 120.0,
          "value": 0.0227
        },
        {
          "hour": 144.0,
          "value": 0.0241
        },
        {
          "hour": 168.0,
          "value": 0.0238
        }
      ],
      "observed_168h": 0.0238,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 14,
        "board_position": 46,
        "grid_row": 6,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000458",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.06093,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.7649,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.331390118598938,
        "prediction_lower": 0.0,
        "prediction_upper": 0.9015152303459592,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.03031191974878311,
              "feature_value": -0.015487549835384605
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.013396413065493107,
              "feature_value": 15.7058373795
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.00886586494743824,
              "feature_value": 0.7649127849951087
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.008474881760776043,
              "feature_value": 24.7453377238
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.008397789672017097,
              "feature_value": 0.680164991355
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1116,
        "headroom_fraction": 0.8551,
        "limit_fraction": 0.1449
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.765,
        "slope_batch_robust_z": -0.233,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.2085,
      "latest_value": 0.1884,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0201,
      "percent_change": -0.0964,
      "percent_change_available": true,
      "slope_per_hour": -0.00084,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.2085
        },
        {
          "hour": 24.0,
          "value": 0.1884
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.2562
        },
        {
          "hour": 72.0,
          "value": 0.3775
        },
        {
          "hour": 96.0,
          "value": 0.5374
        },
        {
          "hour": 120.0,
          "value": 0.6863
        },
        {
          "hour": 144.0,
          "value": 0.9867
        },
        {
          "hour": 168.0,
          "value": 1.2788
        }
      ],
      "observed_168h": 1.2788,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 15,
        "board_position": 47,
        "grid_row": 6,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000478",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05796,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.7118,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1745743602514267,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4815648050382842,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.01786370761692524,
              "feature_value": -0.004506302986857126
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.012578318826854229,
              "feature_value": 0.551813714292
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.010379387065768242,
              "feature_value": 0.1285322064454286
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.005656222812831402,
              "feature_value": 0.8714677935545714
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": -0.005520936567336321,
              "feature_value": 0.003341697159999967
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.61,
        "headroom_fraction": 0.8715,
        "limit_fraction": 0.1285
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.712,
        "slope_batch_robust_z": 0.482,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0931,
      "latest_value": 0.09,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0032,
      "percent_change": -0.0344,
      "percent_change_available": true,
      "slope_per_hour": -0.00013,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0931
        },
        {
          "hour": 24.0,
          "value": 0.09
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0869
        },
        {
          "hour": 72.0,
          "value": 0.0867
        },
        {
          "hour": 96.0,
          "value": 0.0976
        },
        {
          "hour": 120.0,
          "value": 0.0968
        },
        {
          "hour": 144.0,
          "value": 0.086
        },
        {
          "hour": 168.0,
          "value": 0.0945
        }
      ],
      "observed_168h": 0.0945,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 16,
        "board_position": 48,
        "grid_row": 6,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000484",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04985,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.5523,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.026654407382011414,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07928134077404413,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.002876169513911009,
              "feature_value": 0.8939256662241667
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.002795265521854162,
              "feature_value": 0.10607433377583333
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.002679133554920554,
              "feature_value": -0.015356866552500004
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0020719862077385187,
              "feature_value": 0.995600247908
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": 0.0009370862971991301,
              "feature_value": 49.8284621484
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1073,
        "headroom_fraction": 0.8939,
        "limit_fraction": 0.1061
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.261,
        "slope_batch_robust_z": -0.552,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0146,
      "latest_value": 0.0127,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0018,
      "percent_change": -0.1235,
      "percent_change_available": true,
      "slope_per_hour": -8e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0146
        },
        {
          "hour": 24.0,
          "value": 0.0127
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0129
        },
        {
          "hour": 72.0,
          "value": 0.0136
        },
        {
          "hour": 96.0,
          "value": 0.0124
        },
        {
          "hour": 120.0,
          "value": 0.0126
        },
        {
          "hour": 144.0,
          "value": 0.0127
        },
        {
          "hour": 168.0,
          "value": 0.0136
        }
      ],
      "observed_168h": 0.0136,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 1,
        "board_position": 49,
        "grid_row": 7,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000506",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.08648,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0149,
        "robust_deviation_score": 1.1426,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1124693214893341,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4194597662761916,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.029116623103618622,
              "feature_value": -1.1030591605265625
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.021034615114331245,
              "feature_value": 0.06910123764742858
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.01698402129113674,
              "feature_value": 0.00124202669285715
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.016240715980529785,
              "feature_value": 0.9308987623525714
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.008932766504585743,
              "feature_value": 0.06785921095457143
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6516,
        "headroom_fraction": 0.9309,
        "limit_fraction": 0.0691
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.103,
        "slope_batch_robust_z": 1.143,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0475,
      "latest_value": 0.0484,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0009,
      "percent_change": 0.0189,
      "percent_change_available": true,
      "slope_per_hour": 4e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0475
        },
        {
          "hour": 24.0,
          "value": 0.0484
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0926
        },
        {
          "hour": 72.0,
          "value": 0.1452
        },
        {
          "hour": 96.0,
          "value": 0.1867
        },
        {
          "hour": 120.0,
          "value": 0.2646
        },
        {
          "hour": 144.0,
          "value": 0.2618
        },
        {
          "hour": 168.0,
          "value": 0.3937
        }
      ],
      "observed_168h": 0.3937,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 2,
        "board_position": 50,
        "grid_row": 7,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000571",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.03601,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.2126,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.23897281140089036,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8090979231479115,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.028170425444841385,
              "feature_value": -0.012234940393846153
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.02568468078970909,
              "feature_value": 0.12366284443230768
            },
            {
              "feature": "current_capacitance_fraction",
              "contribution_ua": -0.02402082271873951,
              "feature_value": 0.9291149353893617
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.0159623920917511,
              "feature_value": 0.755986083651
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.01433589681982994,
              "feature_value": 15.7058373795
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1392,
        "headroom_fraction": 0.8763,
        "limit_fraction": 0.1237
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.213,
        "slope_batch_robust_z": -0.068,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1767,
      "latest_value": 0.1608,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0159,
      "percent_change": -0.09,
      "percent_change_available": true,
      "slope_per_hour": -0.00066,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1767
        },
        {
          "hour": 24.0,
          "value": 0.1608
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1755
        },
        {
          "hour": 72.0,
          "value": 0.1524
        },
        {
          "hour": 96.0,
          "value": 0.1453
        },
        {
          "hour": 120.0,
          "value": 0.1303
        },
        {
          "hour": 144.0,
          "value": 0.1578
        },
        {
          "hour": 168.0,
          "value": 0.1118
        }
      ],
      "observed_168h": 0.1118,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 3,
        "board_position": 51,
        "grid_row": 7,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000573",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.19167,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00017,
        "robust_deviation_score": 2.0608,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.2335255593061447,
        "prediction_lower": 0.0,
        "prediction_upper": 0.5405160040930022,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": 0.022341575473546982,
              "feature_value": 2.0608158246121424
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.01969909481704235,
              "feature_value": -0.011079802174285737
            },
            {
              "feature": "temperature_c",
              "contribution_ua": 0.0102908406406641,
              "feature_value": 121.604512709
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.0077552031725645065,
              "feature_value": 0.82729037698
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.006836335640400648,
              "feature_value": 0.605376936569
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.5791,
        "headroom_fraction": 0.8273,
        "limit_fraction": 0.1727
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 2.061,
        "slope_batch_robust_z": -0.273,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1287,
      "latest_value": 0.1209,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0078,
      "percent_change": -0.0606,
      "percent_change_available": true,
      "slope_per_hour": -0.00032,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1287
        },
        {
          "hour": 24.0,
          "value": 0.1209
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1143
        },
        {
          "hour": 72.0,
          "value": 0.1126
        },
        {
          "hour": 96.0,
          "value": 0.1201
        },
        {
          "hour": 120.0,
          "value": 0.115
        },
        {
          "hour": 144.0,
          "value": 0.1274
        },
        {
          "hour": 168.0,
          "value": 0.1161
        }
      ],
      "observed_168h": 0.1161,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 4,
        "board_position": 52,
        "grid_row": 7,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000597",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.14708,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.13933,
        "robust_deviation_score": 1.7423,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.018463811874389648,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07109074526642237,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.005601124372333288,
              "feature_value": 0.044750960715833336
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.004252053331583738,
              "feature_value": 0.995600247908
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0035577884409576654,
              "feature_value": 0.9552490392841666
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.0035556359216570854,
              "feature_value": -0.08699270548299998
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.0031809010542929173,
              "feature_value": -1.7422982299431673
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1146,
        "headroom_fraction": 0.9552,
        "limit_fraction": 0.0448
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.742,
        "slope_batch_robust_z": 0.407,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0056,
      "latest_value": 0.0054,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0002,
      "percent_change": -0.0359,
      "percent_change_available": true,
      "slope_per_hour": -1e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0056
        },
        {
          "hour": 24.0,
          "value": 0.0054
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0057
        },
        {
          "hour": 72.0,
          "value": 0.006
        },
        {
          "hour": 96.0,
          "value": 0.0056
        },
        {
          "hour": 120.0,
          "value": 0.0058
        },
        {
          "hour": 144.0,
          "value": 0.0059
        },
        {
          "hour": 168.0,
          "value": 0.0059
        }
      ],
      "observed_168h": 0.0059,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 5,
        "board_position": 53,
        "grid_row": 7,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000628",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04447,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.4325,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.27006443291902543,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8401895446660466,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.029635481536388397,
              "feature_value": -0.00693833697000001
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.027994472533464432,
              "feature_value": 0.09882491862846153
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.026939185336232185,
              "feature_value": 0.9011750813715385
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.012016752734780312,
              "feature_value": 15.7058373795
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.011348236352205276,
              "feature_value": 39.2679209172
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1715,
        "headroom_fraction": 0.9012,
        "limit_fraction": 0.0988
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.432,
        "slope_batch_robust_z": 0.202,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1375,
      "latest_value": 0.1285,
      "last_observation_hour": 24.0,
      "absolute_change": -0.009,
      "percent_change": -0.0655,
      "percent_change_available": true,
      "slope_per_hour": -0.00038,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1375
        },
        {
          "hour": 24.0,
          "value": 0.1285
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1179
        },
        {
          "hour": 72.0,
          "value": 0.1219
        },
        {
          "hour": 96.0,
          "value": 0.1251
        },
        {
          "hour": 120.0,
          "value": 0.1193
        },
        {
          "hour": 144.0,
          "value": 0.1305
        },
        {
          "hour": 168.0,
          "value": 0.1206
        }
      ],
      "observed_168h": 0.1206,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 6,
        "board_position": 54,
        "grid_row": 7,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000669",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04835,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.5202,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.31004577577114106,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8801708875181622,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.026226576417684555,
              "feature_value": -0.01541837907076923
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": 0.018960870802402496,
              "feature_value": -0.04952213645600001
            },
            {
              "feature": "capacitance_change_fraction",
              "contribution_ua": 0.016294078901410103,
              "feature_value": -0.0009505019765957184
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.015269946306943893,
              "feature_value": 0.13550761727076924
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.015038087964057922,
              "feature_value": 15.7058373795
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1238,
        "headroom_fraction": 0.8645,
        "limit_fraction": 0.1355
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.52,
        "slope_batch_robust_z": -0.23,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.1962,
      "latest_value": 0.1762,
      "last_observation_hour": 24.0,
      "absolute_change": -0.02,
      "percent_change": -0.1019,
      "percent_change_available": true,
      "slope_per_hour": -0.00084,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.1962
        },
        {
          "hour": 24.0,
          "value": 0.1762
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1698
        },
        {
          "hour": 72.0,
          "value": 0.1678
        },
        {
          "hour": 96.0,
          "value": 0.1711
        },
        {
          "hour": 120.0,
          "value": 0.1693
        },
        {
          "hour": 144.0,
          "value": 0.1798
        },
        {
          "hour": 168.0,
          "value": 0.1735
        }
      ],
      "observed_168h": 0.1735,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 7,
        "board_position": 55,
        "grid_row": 7,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 98.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000683",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.1107,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00844,
        "robust_deviation_score": 1.4164,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.1426091969013214,
        "prediction_lower": 0.0,
        "prediction_upper": 0.4495996416881789,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.02595156989991665,
              "feature_value": -0.10014940362200003
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.023898687213659286,
              "feature_value": -1.4163809317936036
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.021768424659967422,
              "feature_value": 0.058840793421428575
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.02146156132221222,
              "feature_value": 0.490798148814
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.018218308687210083,
              "feature_value": -0.00862890974085714
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6588,
        "headroom_fraction": 0.9412,
        "limit_fraction": 0.0588
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -1.416,
        "slope_batch_robust_z": 0.008,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0472,
      "latest_value": 0.0412,
      "last_observation_hour": 24.0,
      "absolute_change": -0.006,
      "percent_change": -0.127,
      "percent_change_available": true,
      "slope_per_hour": -0.00025,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0472
        },
        {
          "hour": 24.0,
          "value": 0.0412
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0396
        },
        {
          "hour": 72.0,
          "value": 0.0407
        },
        {
          "hour": 96.0,
          "value": 0.0409
        },
        {
          "hour": 120.0,
          "value": 0.0461
        },
        {
          "hour": 144.0,
          "value": 0.0419
        },
        {
          "hour": 168.0,
          "value": 0.0411
        }
      ],
      "observed_168h": 0.0411,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 8,
        "board_position": 56,
        "grid_row": 7,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000685",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.06853,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.8905,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.31477856487035755,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8849036766173787,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.03001224435865879,
              "feature_value": -0.015390622134615381
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.014864163473248482,
              "feature_value": 15.7058373795
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.014170168898999691,
              "feature_value": 0.807501695686
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": 0.012894961051642895,
              "feature_value": 0.14976555469076921
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.012436436489224434,
              "feature_value": 38.4094966503
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.1053,
        "headroom_fraction": 0.8502,
        "limit_fraction": 0.1498
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.89,
        "slope_batch_robust_z": -0.228,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.2147,
      "latest_value": 0.1947,
      "last_observation_hour": 24.0,
      "absolute_change": -0.02,
      "percent_change": -0.0932,
      "percent_change_available": true,
      "slope_per_hour": -0.00083,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.2147
        },
        {
          "hour": 24.0,
          "value": 0.1947
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.1864
        },
        {
          "hour": 72.0,
          "value": 0.1816
        },
        {
          "hour": 96.0,
          "value": 0.1806
        },
        {
          "hour": 120.0,
          "value": 0.1771
        },
        {
          "hour": 144.0,
          "value": 0.1801
        },
        {
          "hour": 168.0,
          "value": 0.177
        }
      ],
      "observed_168h": 0.177,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 9,
        "board_position": 57,
        "grid_row": 8,
        "grid_col": 1,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 99.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000708",
      "batch_id": "MLCC_B023",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_4U7_16V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.09381,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 1.232,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.30054838955402374,
        "prediction_lower": 0.0,
        "prediction_upper": 0.8706735013010449,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.3767493963241577,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.030079687014222145,
              "feature_value": -0.011770301222307681
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.02987019531428814,
              "feature_value": -0.064260246081
            },
            {
              "feature": "measurement_voltage_v",
              "contribution_ua": -0.015008418820798397,
              "feature_value": 15.7058373795
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": 0.014196638017892838,
              "feature_value": 0.8370846397446154
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.012151102535426617,
              "feature_value": 35.7997692063
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 1.3,
        "applicable_limit": 1.3,
        "headroom": 1.0882,
        "headroom_fraction": 0.8371,
        "limit_fraction": 0.1629
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 1.232,
        "slope_batch_robust_z": -0.044,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.2271,
      "latest_value": 0.2118,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0153,
      "percent_change": -0.0674,
      "percent_change_available": true,
      "slope_per_hour": -0.00064,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.2271
        },
        {
          "hour": 24.0,
          "value": 0.2118
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.2136
        },
        {
          "hour": 72.0,
          "value": 0.2121
        },
        {
          "hour": 96.0,
          "value": 0.2018
        },
        {
          "hour": 120.0,
          "value": 0.1967
        },
        {
          "hour": 144.0,
          "value": 0.2062
        },
        {
          "hour": 168.0,
          "value": 0.2115
        }
      ],
      "observed_168h": 0.2115,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-04",
        "tester_id": "TESTER_3",
        "tester_channel": 10,
        "board_position": 58,
        "grid_row": 8,
        "grid_col": 2,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 100.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 2.6
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000729",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.05865,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 5e-05,
        "robust_deviation_score": 0.7242,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.025068281292915343,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07769521468494806,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0033339345827698708,
              "feature_value": 0.995600247908
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.003056139452382922,
              "feature_value": 0.09875713738
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0027751994784921408,
              "feature_value": 0.90124286262
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0027620168402791023,
              "feature_value": 0.002768772519166661
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.0018317780923098326,
              "feature_value": 27.6183062223
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1081,
        "headroom_fraction": 0.9012,
        "limit_fraction": 0.0988
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.022,
        "slope_batch_robust_z": 0.724,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0115,
      "latest_value": 0.0119,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0003,
      "percent_change": 0.026,
      "percent_change_available": true,
      "slope_per_hour": 1e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0115
        },
        {
          "hour": 24.0,
          "value": 0.0119
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0088
        },
        {
          "hour": 72.0,
          "value": 0.0095
        },
        {
          "hour": 96.0,
          "value": 0.0089
        },
        {
          "hour": 120.0,
          "value": 0.0087
        },
        {
          "hour": 144.0,
          "value": 0.011
        },
        {
          "hour": 168.0,
          "value": 0.0088
        }
      ],
      "observed_168h": 0.0088,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 11,
        "board_position": 59,
        "grid_row": 8,
        "grid_col": 3,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 101.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.7
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000733",
      "batch_id": "MLCC_B002",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_100N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.43066,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.43066,
        "robust_deviation_score": 2.9447,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.11003170907497406,
        "prediction_lower": 0.00039226450823923176,
        "prediction_upper": 0.2196711536417089,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.07245180755853653,
          "top_contributions": [
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": 0.030082035809755325,
              "feature_value": 0.025235683780800003
            },
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.009780802763998508,
              "feature_value": 2.9446635707014557
            },
            {
              "feature": "current_batch_robust_z",
              "contribution_ua": -0.00814246665686369,
              "feature_value": -0.3080905255392512
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.007260692771524191,
              "feature_value": 0.567629017216
            },
            {
              "feature": "initial_fraction_of_limit",
              "contribution_ua": 0.005420898087322712,
              "feature_value": 0.0779279822868
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.25,
        "applicable_limit": 0.25,
        "headroom": 0.2242,
        "headroom_fraction": 0.8968,
        "limit_fraction": 0.1032
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.308,
        "slope_batch_robust_z": 2.945,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0195,
      "latest_value": 0.0258,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0063,
      "percent_change": 0.3234,
      "percent_change_available": true,
      "slope_per_hour": 0.00026,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0195
        },
        {
          "hour": 24.0,
          "value": 0.0258
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0186
        },
        {
          "hour": 72.0,
          "value": 0.0206
        },
        {
          "hour": 96.0,
          "value": 0.0179
        },
        {
          "hour": 120.0,
          "value": 0.0163
        },
        {
          "hour": 144.0,
          "value": 0.0177
        },
        {
          "hour": 168.0,
          "value": 0.0174
        }
      ],
      "observed_168h": 0.0174,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-02",
        "tester_id": "TESTER_3",
        "tester_channel": 12,
        "board_position": 60,
        "grid_row": 8,
        "grid_col": 4,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 102.2,
        "dissipation_factor_pct": 0.71,
        "insulation_resistance_gohm": 2.8
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000747",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.03635,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.2225,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.03838970303535461,
        "prediction_lower": 0.0,
        "prediction_upper": 0.09101663642738733,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": 0.005982731003314257,
              "feature_value": 0.375480872956
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.004103928338736296,
              "feature_value": 0.995600247908
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0030249517876654863,
              "feature_value": 0.09956065510916667
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0027600456960499287,
              "feature_value": 0.9004393448908334
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0025146990083158016,
              "feature_value": -0.0043541538966666675
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1081,
        "headroom_fraction": 0.9004,
        "limit_fraction": 0.0996
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": 0.048,
        "slope_batch_robust_z": 0.223,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0125,
      "latest_value": 0.0119,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0005,
      "percent_change": -0.0401,
      "percent_change_available": true,
      "slope_per_hour": -2e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0125
        },
        {
          "hour": 24.0,
          "value": 0.0119
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0114
        },
        {
          "hour": 72.0,
          "value": 0.0109
        },
        {
          "hour": 96.0,
          "value": 0.0106
        },
        {
          "hour": 120.0,
          "value": 0.0106
        },
        {
          "hour": 144.0,
          "value": 0.0109
        },
        {
          "hour": 168.0,
          "value": 0.01
        }
      ],
      "observed_168h": 0.01,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 13,
        "board_position": 61,
        "grid_row": 8,
        "grid_col": 5,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.0,
        "dissipation_factor_pct": 0.55,
        "insulation_resistance_gohm": 2.9
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000764",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.03824,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.2751,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.027162596583366394,
        "prediction_lower": 0.0,
        "prediction_upper": 0.0797895299753991,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.0031037635635584593,
              "feature_value": 0.995600247908
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0029393716249614954,
              "feature_value": -0.009195706565833324
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.0028952457942068577,
              "feature_value": 0.9103332144983334
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.002825516974553466,
              "feature_value": 0.08966678550166668
            },
            {
              "feature": "prior_storage_humidity_pct",
              "contribution_ua": -0.0021382716950029135,
              "feature_value": 19.5810562633
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1092,
        "headroom_fraction": 0.9103,
        "limit_fraction": 0.0897
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.275,
        "slope_batch_robust_z": -0.118,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0119,
      "latest_value": 0.0108,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0011,
      "percent_change": -0.0927,
      "percent_change_available": true,
      "slope_per_hour": -5e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0119
        },
        {
          "hour": 24.0,
          "value": 0.0108
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0143
        },
        {
          "hour": 72.0,
          "value": 0.0181
        },
        {
          "hour": 96.0,
          "value": 0.026
        },
        {
          "hour": 120.0,
          "value": 0.0334
        },
        {
          "hour": 144.0,
          "value": 0.0443
        },
        {
          "hour": 168.0,
          "value": 0.054
        }
      ],
      "observed_168h": 0.054,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 14,
        "board_position": 62,
        "grid_row": 8,
        "grid_col": 6,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 95.8,
        "dissipation_factor_pct": 0.59,
        "insulation_resistance_gohm": 3.0
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000765",
      "batch_id": "MLCC_B018",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_1U_25V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.15994,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.00359,
        "robust_deviation_score": 1.8413,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.17008852660655974,
        "prediction_lower": 0.0,
        "prediction_upper": 0.47707897139341726,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.20286506414413452,
          "top_contributions": [
            {
              "feature": "slope_batch_robust_z",
              "contribution_ua": 0.028132373467087746,
              "feature_value": 1.8413232733348996
            },
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.016220035031437874,
              "feature_value": 0.10197488430900001
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.015389181673526764,
              "feature_value": 0.898025115691
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.013063430786132812,
              "feature_value": 0.007322429633857145
            },
            {
              "feature": "initial_dissipation_factor_pct",
              "contribution_ua": -0.009769119322299957,
              "feature_value": 0.599498104189
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.7,
        "applicable_limit": 0.7,
        "headroom": 0.6286,
        "headroom_fraction": 0.898,
        "limit_fraction": 0.102
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.099,
        "slope_batch_robust_z": 1.841,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0663,
      "latest_value": 0.0714,
      "last_observation_hour": 24.0,
      "absolute_change": 0.0051,
      "percent_change": 0.077,
      "percent_change_available": true,
      "slope_per_hour": 0.00021,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0663
        },
        {
          "hour": 24.0,
          "value": 0.0714
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0643
        },
        {
          "hour": 72.0,
          "value": 0.0698
        },
        {
          "hour": 96.0,
          "value": 0.0747
        },
        {
          "hour": 120.0,
          "value": 0.0563
        },
        {
          "hour": 144.0,
          "value": 0.0566
        },
        {
          "hour": 168.0,
          "value": 0.06
        }
      ],
      "observed_168h": 0.06,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-03",
        "tester_id": "TESTER_1",
        "tester_channel": 15,
        "board_position": 63,
        "grid_row": 8,
        "grid_col": 7,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 96.6,
        "dissipation_factor_pct": 0.63,
        "insulation_resistance_gohm": 3.1
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    },
    {
      "component_id": "MLCC_C000828",
      "batch_id": "MLCC_B029",
      "component_family": "MLCC_X7R",
      "measurement_name": "leakage_ua",
      "profile_id": "SIM_X7R_10N_50V",
      "recommendation": "ACCEPT",
      "recommendation_reasons": [],
      "recommendation_basis": "anomaly_and_forecast",
      "data_quality_warning": null,
      "anomaly": {
        "status": "available",
        "score": 0.04253,
        "is_anomaly": false,
        "score_kind": "ranking score, not failure probability",
        "model_score": 0.0,
        "robust_deviation_score": 0.3859,
        "reason_codes": [],
        "method": "median_mad+isolation_forest"
      },
      "forecast": {
        "status": "available",
        "predicted_final_value": 0.026347321271896363,
        "prediction_lower": 0.0,
        "prediction_upper": 0.07897425466392907,
        "target_hour": 168.0,
        "model_version": "xgboost_v2",
        "interval_nominal_coverage": 0.8,
        "upper_bound_nominal_level": 0.9,
        "interval_method": "stratified_asymmetric_split_conformal_signed_residual",
        "interval_warning": "Nominal coverage; actual field accuracy subject to production verification.",
        "predicted_to_cross_limit": false,
        "prediction_readiness": "ready",
        "out_of_training_range_features": [],
        "xgboost_explanation": {
          "explains": "Unclipped XGBoost candidate forecast; associations, not physical causes",
          "is_active_forecast": true,
          "base_value_ua": 0.03477686643600464,
          "top_contributions": [
            {
              "feature": "limit_fraction",
              "contribution_ua": -0.0029284863267093897,
              "feature_value": 0.09676437030083333
            },
            {
              "feature": "distance_fraction_to_upper_limit",
              "contribution_ua": -0.002884208457544446,
              "feature_value": 0.9032356296991666
            },
            {
              "feature": "delta_fraction_of_limit",
              "contribution_ua": -0.0026157184038311243,
              "feature_value": -0.012993066505833338
            },
            {
              "feature": "voltage_stress_ratio",
              "contribution_ua": 0.002378766890615225,
              "feature_value": 0.995600247908
            },
            {
              "feature": "dissipation_factor_change_pct",
              "contribution_ua": -0.0020669433288276196,
              "feature_value": -0.0664365579559999
            }
          ]
        }
      },
      "limits": {
        "direction": "upper",
        "upper_limit": 0.12,
        "applicable_limit": 0.12,
        "headroom": 0.1084,
        "headroom_fraction": 0.9032,
        "limit_fraction": 0.0968
      },
      "peers": {
        "sample_size": 200,
        "sufficient": true,
        "status": "available",
        "current_batch_robust_z": -0.043,
        "slope_batch_robust_z": -0.386,
        "warning": null
      },
      "measurement_unit": "uA",
      "initial_value": 0.0132,
      "latest_value": 0.0116,
      "last_observation_hour": 24.0,
      "absolute_change": -0.0016,
      "percent_change": -0.1215,
      "percent_change_available": true,
      "slope_per_hour": -6e-05,
      "early_trajectory": [
        {
          "hour": 0.0,
          "value": 0.0132
        },
        {
          "hour": 24.0,
          "value": 0.0116
        }
      ],
      "outcome_trajectory": [
        {
          "hour": 48.0,
          "value": 0.0109
        },
        {
          "hour": 72.0,
          "value": 0.0106
        },
        {
          "hour": 96.0,
          "value": 0.0116
        },
        {
          "hour": 120.0,
          "value": 0.0125
        },
        {
          "hour": 144.0,
          "value": 0.0118
        },
        {
          "hour": 168.0,
          "value": 0.0127
        }
      ],
      "observed_168h": 0.0127,
      "crossed_applicable_limit": false,
      "within_limit_but_unusual": false,
      "context": {
        "part_number": "FICTIONAL-MLCC-01",
        "tester_id": "TESTER_3",
        "tester_channel": 16,
        "board_position": 64,
        "grid_row": 8,
        "grid_col": 8,
        "temperature_c": 125.0,
        "applied_voltage_v": 45.7,
        "rated_voltage_v": 50.0,
        "package_code": "0805",
        "prior_storage_humidity_pct": 55.4,
        "capacitance_nf": 97.4,
        "dissipation_factor_pct": 0.67,
        "insulation_resistance_gohm": 2.5
      },
      "data_source": "synthetic",
      "provenance": "synthetic"
    }
  ],
  "unscored_records": [],
  "warnings": [
    {
      "code": "SYNTHETIC_TRAINING_DATA",
      "message": "Models trained on synthetic MLCC data for demonstration pipeline.",
      "count": null
    },
    {
      "code": "SYNTHETIC_DATA",
      "message": "The uploaded dataset is marked synthetic. This is not measured hardware data.",
      "count": null
    }
  ]
};

export default DEMO_DATASET;
