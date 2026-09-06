"""Core anomaly-detection tools for the SIH26170 prototype."""

from .anomaly import BatchAwareAnomalyDetector, apply_robust_baseline
from .contracts import AnomalyResult, PredictionResult
from .decision import build_screening_record, recommend_action
from .evaluation import (
    BatchSplit,
    EvaluationReport,
    evaluate_repeated_splits,
    evaluate_synthetic_dataset,
    evaluate_time_sweep,
    make_batch_split,
    summarize_repeated_splits,
    write_evaluation_report,
)
from .evaluation_harness import (
    ScreeningConfig,
    evaluate_screening,
    run_early_warning_ladder,
    run_holdout_evaluation,
    run_parameter_sweep,
    screen_components,
)
from .features import MODEL_FEATURE_COLUMNS, build_component_features
from .splitting import (
    BatchHoldout,
    LeakageError,
    assert_split_is_leakage_safe,
    build_split_features,
    split_batches,
)
from .synthetic import (
    DEFAULT_FAMILIES,
    DEFAULT_HOURS,
    FamilySpec,
    SyntheticDataset,
    generate_burn_in_dataset,
)
from .validation import DataValidationError, validate_readings

__all__ = [
    "AnomalyResult",
    "apply_robust_baseline",
    "assert_split_is_leakage_safe",
    "BatchAwareAnomalyDetector",
    "BatchHoldout",
    "BatchSplit",
    "build_component_features",
    "build_screening_record",
    "build_split_features",
    "DataValidationError",
    "DEFAULT_FAMILIES",
    "DEFAULT_HOURS",
    "evaluate_repeated_splits",
    "evaluate_screening",
    "evaluate_synthetic_dataset",
    "evaluate_time_sweep",
    "EvaluationReport",
    "FamilySpec",
    "generate_burn_in_dataset",
    "LeakageError",
    "make_batch_split",
    "MODEL_FEATURE_COLUMNS",
    "PredictionResult",
    "recommend_action",
    "run_early_warning_ladder",
    "run_holdout_evaluation",
    "run_parameter_sweep",
    "screen_components",
    "ScreeningConfig",
    "split_batches",
    "summarize_repeated_splits",
    "SyntheticDataset",
    "validate_readings",
    "write_evaluation_report",
]
