from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import polars as pl

from replenish.config.settings import DataQualityConfig


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    detail: str


class Validator(Protocol):
    def validate(self) -> ValidationResult:
        """Return a validation result without mutating source data."""


@dataclass(frozen=True)
class TrainRowCountValidator:
    train: pl.DataFrame
    config: DataQualityConfig

    def validate(self) -> ValidationResult:
        observed_rows = self.train.height
        passed = observed_rows == self.config.expected_train_rows
        detail = f"observed={observed_rows}, expected={self.config.expected_train_rows}"
        return ValidationResult("train_row_count", passed, detail)


@dataclass(frozen=True)
class OilNullValidator:
    oil: pl.DataFrame

    def validate(self) -> ValidationResult:
        remaining_nulls = self.oil.select(pl.col("dcoilwtico").null_count()).item()
        passed = remaining_nulls == 0
        detail = f"remaining_nulls={remaining_nulls}"
        return ValidationResult("oil_zero_nulls_after_fill", passed, detail)


@dataclass(frozen=True)
class OilRawNullCountValidator:
    oil: pl.DataFrame
    config: DataQualityConfig

    def validate(self) -> ValidationResult:
        observed_nulls = self.oil.select(pl.col("dcoilwtico").null_count()).item()
        passed = observed_nulls == self.config.expected_oil_nulls_before_fill
        detail = (
            f"observed={observed_nulls}, "
            f"expected={self.config.expected_oil_nulls_before_fill}"
        )
        return ValidationResult("oil_raw_null_count", passed, detail)


@dataclass(frozen=True)
class DailyCalendarValidator:
    panel: pl.DataFrame

    def validate(self) -> ValidationResult:
        broken = (
            self.panel.group_by(["store_nbr", "family"])
            .agg(
                pl.col("date").min().alias("start_date"),
                pl.col("date").max().alias("end_date"),
                pl.col("date").n_unique().alias("observed_days"),
            )
            .with_columns(
                (pl.col("end_date") - pl.col("start_date"))
                .dt.total_days()
                .add(1)
                .alias("expected_days")
            )
            .filter(pl.col("observed_days") != pl.col("expected_days"))
        )
        passed = broken.height == 0
        detail = f"broken_series={broken.height}"
        return ValidationResult("unbroken_daily_index", passed, detail)


@dataclass(frozen=True)
class AllZeroSeriesValidator:
    train: pl.DataFrame
    config: DataQualityConfig

    def validate(self) -> ValidationResult:
        all_zero_count = (
            self.train.group_by(["store_nbr", "family"])
            .agg(pl.col("sales").sum().alias("total_sales"))
            .filter(pl.col("total_sales") == 0)
            .height
        )
        passed = all_zero_count == self.config.expected_all_zero_series
        detail = (
            f"observed={all_zero_count}, "
            f"expected={self.config.expected_all_zero_series}"
        )
        return ValidationResult("all_zero_series_count", passed, detail)


@dataclass(frozen=True)
class LeadingZeroTruncationValidator:
    panel: pl.DataFrame

    def validate(self) -> ValidationResult:
        invalid_rows = (
            self.panel.sort(["store_nbr", "family", "date"])
            .with_columns(
                pl.col("sales")
                .cum_sum()
                .over(["store_nbr", "family"])
                .alias("cumulative_sales")
            )
            .filter((pl.col("cumulative_sales") == 0) & (pl.col("sales") == 0))
            .height
        )
        passed = invalid_rows == 0
        detail = f"pre_launch_zero_rows_remaining={invalid_rows}"
        return ValidationResult("leading_zero_truncation", passed, detail)
