"""Leakage guards for the batch-level evaluation split.

Two failures would silently invalidate every downstream number: dividing a
batch across training and evaluation, and letting an observation after the
early-warning hour reach a feature. Both are tested here directly.
"""

from __future__ import annotations

import pandas as pd
import pytest

from sih26170.features import build_component_features
from sih26170.splitting import (
    BatchHoldout,
    LeakageError,
    assert_components_are_disjoint,
    assert_features_respect_as_of_hour,
    assert_split_is_leakage_safe,
    build_split_features,
    split_batches,
)
from sih26170.synthetic import generate_burn_in_dataset

AS_OF_HOUR = 24.0


@pytest.fixture(scope="module")
def dataset():
    return generate_burn_in_dataset(seed=101, n_batches=4, components_per_batch=24)


@pytest.fixture(scope="module")
def split(dataset):
    return split_batches(dataset.readings, test_fraction=0.4, random_state=7)


def _numeric_columns(frame: pd.DataFrame) -> list[str]:
    return [name for name in frame.columns if frame[name].dtype.kind in "fi"]


def test_complete_batches_stay_on_one_side(dataset, split) -> None:
    assert set(split.train_batches).isdisjoint(split.test_batches)
    assert set(split.all_batches) == set(dataset.readings["batch_id"])

    train = split.train_readings(dataset.readings)
    test = split.test_readings(dataset.readings)
    assert len(train) + len(test) == len(dataset.readings)
    for batch_id, group in dataset.readings.groupby("batch_id"):
        in_train = int(train["batch_id"].eq(batch_id).sum())
        in_test = int(test["batch_id"].eq(batch_id).sum())
        assert {in_train, in_test} == {0, len(group)}, f"batch {batch_id} was divided"


def test_components_never_appear_on_both_sides(dataset, split) -> None:
    assert_components_are_disjoint(dataset.readings, split)


def test_split_is_deterministic_for_a_seed(dataset) -> None:
    first = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
    repeat = split_batches(dataset.readings, test_fraction=0.4, random_state=7)
    assert first == repeat


def test_every_evaluation_family_has_a_training_counterpart(dataset, split) -> None:
    train_families = set(split.train_readings(dataset.readings)["component_family"])
    test_families = set(split.test_readings(dataset.readings)["component_family"])
    assert test_families.issubset(train_families)


def test_future_rows_cannot_change_an_early_feature(dataset) -> None:
    """The central leakage guard: rows after the cut-off must be inert."""

    honest = build_component_features(dataset.readings, as_of_hour=AS_OF_HOUR)

    corrupted = dataset.readings.copy()
    later = corrupted["hours"].astype(float) > AS_OF_HOUR
    assert later.any()
    corrupted.loc[later, "measurement_value"] = (
        corrupted.loc[later, "measurement_value"] * 1e6 + 12345.0
    )
    tampered = build_component_features(corrupted, as_of_hour=AS_OF_HOUR)

    columns = _numeric_columns(honest)
    pd.testing.assert_frame_equal(
        honest.sort_values("component_id").reset_index(drop=True)[columns],
        tampered.sort_values("component_id").reset_index(drop=True)[columns],
    )


def test_batch_features_do_not_depend_on_other_batches(dataset, split) -> None:
    """Batch-relative statistics must be computed inside a batch only."""

    everything = build_component_features(dataset.readings, as_of_hour=AS_OF_HOUR)
    _, test_only = build_split_features(dataset.readings, split, as_of_hour=AS_OF_HOUR)

    subset = everything.loc[everything["batch_id"].isin(split.test_batches)]
    columns = _numeric_columns(test_only)
    pd.testing.assert_frame_equal(
        subset.sort_values("component_id").reset_index(drop=True)[columns],
        test_only.sort_values("component_id").reset_index(drop=True)[columns],
    )


def test_leakage_guard_rejects_a_late_observation(dataset) -> None:
    features = build_component_features(dataset.readings, as_of_hour=AS_OF_HOUR)
    assert_features_respect_as_of_hour(features, as_of_hour=AS_OF_HOUR)

    tampered = features.copy()
    tampered.loc[tampered.index[0], "last_observed_hour"] = AS_OF_HOUR + 1.0
    with pytest.raises(LeakageError, match="after hour"):
        assert_features_respect_as_of_hour(tampered, as_of_hour=AS_OF_HOUR)


def test_leakage_guard_rejects_a_shared_batch() -> None:
    with pytest.raises(LeakageError, match="both sides"):
        BatchHoldout(
            train_batches=("B01", "B02"),
            test_batches=("B02",),
            test_fraction=0.4,
            random_state=7,
        )


def test_leakage_guard_rejects_an_uncovered_batch(dataset, split) -> None:
    assert_split_is_leakage_safe(dataset.readings, split, as_of_hour=AS_OF_HOUR)

    partial = BatchHoldout(
        train_batches=split.train_batches[:1],
        test_batches=split.test_batches,
        test_fraction=split.test_fraction,
        random_state=split.random_state,
    )
    with pytest.raises(LeakageError, match="missing from the split"):
        assert_split_is_leakage_safe(dataset.readings, partial, as_of_hour=AS_OF_HOUR)


def test_an_impossible_test_fraction_is_rejected(dataset) -> None:
    with pytest.raises(ValueError, match="test_fraction"):
        split_batches(dataset.readings, test_fraction=0.0)
    with pytest.raises(ValueError, match="test_fraction"):
        split_batches(dataset.readings, test_fraction=1.0)
