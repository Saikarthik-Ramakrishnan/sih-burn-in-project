"""Batch-level splitting and leakage guards for the evaluation harness.

Two rules are enforced here, because both are easy to break silently:

* a manufacturing/test batch is never divided between training and evaluation.
  Components inside one batch share a chamber, a lot history and a
  normalisation group, so a row-level split would let a peer of a component
  train the model that later judges it;
* a feature row may only be built from observations at or before the chosen
  early-warning hour.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .features import build_component_features

BATCH_COLUMN = "batch_id"
COMPONENT_COLUMN = "component_id"


class LeakageError(ValueError):
    """Raised when an evaluation split could leak information."""


@dataclass(frozen=True)
class BatchHoldout:
    """Complete batches assigned to either training or evaluation."""

    train_batches: tuple[str, ...]
    test_batches: tuple[str, ...]
    test_fraction: float
    random_state: int

    def __post_init__(self) -> None:
        overlap = sorted(set(self.train_batches).intersection(self.test_batches))
        if overlap:
            raise LeakageError(f"batches appear on both sides of the split: {', '.join(overlap)}")
        if not self.train_batches:
            raise LeakageError("the split has no training batch")
        if not self.test_batches:
            raise LeakageError("the split has no evaluation batch")

    @property
    def all_batches(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.train_batches) | set(self.test_batches)))

    def select(self, readings: pd.DataFrame, side: str) -> pd.DataFrame:
        if side == "train":
            wanted = self.train_batches
        elif side == "test":
            wanted = self.test_batches
        else:
            raise ValueError("side must be 'train' or 'test'")
        selected = readings.loc[readings[BATCH_COLUMN].astype(str).isin(wanted)]
        return selected.copy()

    def train_readings(self, readings: pd.DataFrame) -> pd.DataFrame:
        return self.select(readings, "train")

    def test_readings(self, readings: pd.DataFrame) -> pd.DataFrame:
        return self.select(readings, "test")

    def to_dict(self) -> dict[str, object]:
        return {
            "train_batches": list(self.train_batches),
            "test_batches": list(self.test_batches),
            "test_fraction": self.test_fraction,
            "random_state": self.random_state,
        }


def split_batches(
    readings: pd.DataFrame,
    *,
    test_fraction: float = 0.4,
    random_state: int = 7,
    stratify_column: str | None = "component_family",
) -> BatchHoldout:
    """Assign whole batches to training or evaluation.

    When ``stratify_column`` is given, the split is balanced inside each
    stratum so that an evaluation family always has a comparable training
    family. A stratum with a single batch stays in training, because a family
    the model has never seen cannot be scored honestly.
    """

    if BATCH_COLUMN not in readings.columns:
        raise ValueError(f"readings must contain a {BATCH_COLUMN} column")
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must sit strictly between 0 and 1")

    frame = readings.copy()
    frame[BATCH_COLUMN] = frame[BATCH_COLUMN].astype(str)
    if stratify_column and stratify_column in frame.columns:
        stratum_of_batch = (
            frame.groupby(BATCH_COLUMN)[stratify_column]
            .agg(lambda values: "|".join(sorted({str(value) for value in values})))
            .to_dict()
        )
    else:
        stratum_of_batch = {batch: "*" for batch in frame[BATCH_COLUMN].unique()}

    strata: dict[str, list[str]] = {}
    for batch, stratum in stratum_of_batch.items():
        strata.setdefault(stratum, []).append(str(batch))

    rng = np.random.default_rng(random_state)
    train: list[str] = []
    test: list[str] = []
    for stratum in sorted(strata):
        batches = sorted(strata[stratum])
        shuffled = [batches[index] for index in rng.permutation(len(batches))]
        if len(shuffled) == 1:
            train.extend(shuffled)
            continue
        n_test = int(round(test_fraction * len(shuffled)))
        n_test = min(max(n_test, 1), len(shuffled) - 1)
        test.extend(shuffled[:n_test])
        train.extend(shuffled[n_test:])

    if not test:
        raise LeakageError(
            "no batch could be held out; provide at least two batches in one stratum"
        )
    return BatchHoldout(
        train_batches=tuple(sorted(train)),
        test_batches=tuple(sorted(test)),
        test_fraction=test_fraction,
        random_state=random_state,
    )


def assert_components_are_disjoint(readings: pd.DataFrame, split: BatchHoldout) -> None:
    """Raise when a component identifier appears on both sides of the split."""

    train_components = set(split.train_readings(readings)[COMPONENT_COLUMN].astype(str))
    test_components = set(split.test_readings(readings)[COMPONENT_COLUMN].astype(str))
    shared = sorted(train_components.intersection(test_components))
    if shared:
        raise LeakageError(
            f"{len(shared)} component(s) appear in both splits, first: {shared[0]}"
        )


def assert_features_respect_as_of_hour(features: pd.DataFrame, *, as_of_hour: float) -> None:
    """Raise when a feature row was built from an observation after the cut-off."""

    if "last_observed_hour" not in features.columns:
        raise ValueError("features must contain last_observed_hour")
    late = features.loc[features["last_observed_hour"].astype(float) > float(as_of_hour)]
    if not late.empty:
        raise LeakageError(
            f"{len(late)} feature row(s) used observations after hour {as_of_hour}"
        )


def assert_split_is_leakage_safe(
    readings: pd.DataFrame,
    split: BatchHoldout,
    *,
    as_of_hour: float,
    minimum_observations: int = 2,
) -> None:
    """Run every leakage guard used by the evaluation harness."""

    assert_components_are_disjoint(readings, split)
    covered = set(split.all_batches)
    present = set(readings[BATCH_COLUMN].astype(str))
    missing = sorted(present.difference(covered))
    if missing:
        raise LeakageError(f"batches missing from the split: {', '.join(missing)}")
    train_features, test_features = build_split_features(
        readings, split, as_of_hour=as_of_hour, minimum_observations=minimum_observations
    )
    assert_features_respect_as_of_hour(train_features, as_of_hour=as_of_hour)
    assert_features_respect_as_of_hour(test_features, as_of_hour=as_of_hour)


def build_split_features(
    readings: pd.DataFrame,
    split: BatchHoldout,
    *,
    as_of_hour: float,
    minimum_observations: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build early-warning features separately for each side of the split.

    Building each side on its own keeps the batch-relative statistics of an
    evaluation batch independent of the training batches.
    """

    train_features = build_component_features(
        split.train_readings(readings),
        as_of_hour=as_of_hour,
        minimum_observations=minimum_observations,
    )
    test_features = build_component_features(
        split.test_readings(readings),
        as_of_hour=as_of_hour,
        minimum_observations=minimum_observations,
    )
    return train_features, test_features
