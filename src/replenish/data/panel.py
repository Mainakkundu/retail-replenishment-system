from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from replenish.config.settings import DataQualityConfig


@dataclass(frozen=True)
class PanelBuildResult:
    panel: pl.DataFrame
    all_zero_series_count: int
    leading_zero_rows_dropped: int


def forward_fill_oil(oil: pl.DataFrame) -> pl.DataFrame:
    return oil.sort("date").with_columns(
        pl.col("dcoilwtico").forward_fill().backward_fill()
    )


def count_all_zero_series(train: pl.DataFrame) -> int:
    return (
        train.group_by(["store_nbr", "family"])
        .agg(pl.col("sales").sum().alias("total_sales"))
        .filter(pl.col("total_sales") == 0)
        .height
    )


def drop_all_zero_series(train: pl.DataFrame) -> pl.DataFrame:
    active_series = (
        train.group_by(["store_nbr", "family"])
        .agg(pl.col("sales").sum().alias("total_sales"))
        .filter(pl.col("total_sales") > 0)
        .select(["store_nbr", "family"])
    )
    return train.join(active_series, on=["store_nbr", "family"], how="inner")


def truncate_leading_zeros(train: pl.DataFrame) -> tuple[pl.DataFrame, int]:
    marked = (
        train.sort(["store_nbr", "family", "date"])
        .with_columns(
            pl.col("sales")
            .cum_sum()
            .over(["store_nbr", "family"])
            .alias("cumulative_sales")
        )
        .with_columns((pl.col("cumulative_sales") > 0).alias("is_launched"))
    )
    truncated = marked.filter(pl.col("is_launched")).drop(
        ["cumulative_sales", "is_launched"]
    )
    return truncated, marked.height - truncated.height


def reindex_daily(train: pl.DataFrame, config: DataQualityConfig) -> pl.DataFrame:
    series = train.select(["store_nbr", "family"]).unique()
    calendar = pl.date_range(
        pl.lit(config.calendar_start).str.strptime(pl.Date),
        pl.lit(config.calendar_end).str.strptime(pl.Date),
        interval="1d",
        eager=True,
    ).alias("date")
    grid = series.join(pl.DataFrame({"date": calendar}), how="cross")
    return (
        grid.join(train, on=["store_nbr", "family", "date"], how="left")
        .with_columns(
            pl.col("sales").fill_null(0.0),
            pl.col("onpromotion").fill_null(0),
        )
        .sort(["store_nbr", "family", "date"])
    )


def build_panel(train: pl.DataFrame, config: DataQualityConfig) -> PanelBuildResult:
    all_zero_series_count = count_all_zero_series(train)
    active = drop_all_zero_series(train)
    reindexed = reindex_daily(active, config)
    truncated, leading_zero_rows_dropped = truncate_leading_zeros(reindexed)
    return PanelBuildResult(
        panel=truncated,
        all_zero_series_count=all_zero_series_count,
        leading_zero_rows_dropped=leading_zero_rows_dropped,
    )
