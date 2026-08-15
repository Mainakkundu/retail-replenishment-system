from __future__ import annotations

from datetime import date

import polars as pl

from replenish.config.settings import DataQualityConfig
from replenish.data.validators import (
    AllZeroSeriesValidator,
    DailyCalendarValidator,
    LeadingZeroTruncationValidator,
    OilNullValidator,
    TrainRowCountValidator,
)


def test_train_row_count_validator_passes_expected_count() -> None:
    train = pl.DataFrame({"sales": [1.0, 2.0]})
    result = TrainRowCountValidator(
        train,
        DataQualityConfig(expected_train_rows=2),
    ).validate()

    assert result.passed


def test_oil_null_validator_fails_when_nulls_remain() -> None:
    oil = pl.DataFrame({"dcoilwtico": [50.0, None]})
    result = OilNullValidator(oil).validate()

    assert not result.passed


def test_daily_calendar_validator_detects_gap() -> None:
    panel = pl.DataFrame(
        {
            "store_nbr": [1, 1],
            "family": ["A", "A"],
            "date": [date(2020, 1, 1), date(2020, 1, 3)],
        }
    )
    result = DailyCalendarValidator(panel).validate()

    assert not result.passed


def test_all_zero_series_validator_counts_zero_series() -> None:
    train = pl.DataFrame(
        {
            "store_nbr": [1, 1, 2, 2],
            "family": ["A", "A", "B", "B"],
            "sales": [1.0, 0.0, 0.0, 0.0],
        }
    )
    result = AllZeroSeriesValidator(
        train,
        DataQualityConfig(expected_all_zero_series=1),
    ).validate()

    assert result.passed


def test_leading_zero_truncation_validator_detects_prelaunch_zero() -> None:
    panel = pl.DataFrame(
        {
            "store_nbr": [1, 1],
            "family": ["A", "A"],
            "date": [date(2020, 1, 1), date(2020, 1, 2)],
            "sales": [0.0, 1.0],
        }
    )
    result = LeadingZeroTruncationValidator(panel).validate()

    assert not result.passed

