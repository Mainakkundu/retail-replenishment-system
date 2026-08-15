from __future__ import annotations

from datetime import date

import polars as pl

from replenish.config.settings import DataQualityConfig
from replenish.data.panel import build_panel, forward_fill_oil


def test_forward_fill_oil_removes_middle_nulls() -> None:
    oil = pl.DataFrame(
        {
            "date": [date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3)],
            "dcoilwtico": [50.0, None, 52.0],
        }
    )

    filled = forward_fill_oil(oil)

    assert filled["dcoilwtico"].to_list() == [50.0, 50.0, 52.0]


def test_forward_fill_oil_removes_leading_nulls() -> None:
    oil = pl.DataFrame(
        {
            "date": [date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3)],
            "dcoilwtico": [None, 50.0, 52.0],
        }
    )

    filled = forward_fill_oil(oil)

    assert filled["dcoilwtico"].to_list() == [50.0, 50.0, 52.0]


def test_build_panel_drops_all_zero_and_truncates_prelaunch_zeros() -> None:
    train = pl.DataFrame(
        {
            "date": [
                date(2020, 1, 1),
                date(2020, 1, 2),
                date(2020, 1, 3),
                date(2020, 1, 1),
                date(2020, 1, 2),
                date(2020, 1, 3),
            ],
            "store_nbr": [1, 1, 1, 2, 2, 2],
            "family": ["A", "A", "A", "B", "B", "B"],
            "sales": [0.0, 3.0, 4.0, 0.0, 0.0, 0.0],
            "onpromotion": [0, 0, 1, 0, 0, 0],
        }
    )
    config = DataQualityConfig(
        expected_train_rows=6,
        expected_all_zero_series=1,
        expected_oil_nulls_before_fill=0,
        calendar_start="2020-01-01",
        calendar_end="2020-01-03",
    )

    result = build_panel(train, config)

    assert result.all_zero_series_count == 1
    assert result.leading_zero_rows_dropped == 1
    assert result.panel.select("store_nbr").unique().item() == 1
    assert result.panel["date"].to_list() == [date(2020, 1, 2), date(2020, 1, 3)]
