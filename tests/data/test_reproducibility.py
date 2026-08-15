from __future__ import annotations

from datetime import date

import polars as pl

from replenish.config.settings import DataQualityConfig
from replenish.data.panel import build_panel


def test_panel_build_is_deterministic() -> None:
    train = pl.DataFrame(
        {
            "date": [
                date(2020, 1, 2),
                date(2020, 1, 1),
                date(2020, 1, 3),
                date(2020, 1, 1),
            ],
            "store_nbr": [1, 1, 1, 2],
            "family": ["A", "A", "A", "B"],
            "sales": [2.0, 0.0, 3.0, 0.0],
            "onpromotion": [1, 0, 0, 0],
        }
    )
    config = DataQualityConfig(
        expected_train_rows=4,
        expected_all_zero_series=1,
        expected_oil_nulls_before_fill=0,
        calendar_start="2020-01-01",
        calendar_end="2020-01-03",
    )

    first = build_panel(train, config).panel.write_json()
    second = build_panel(train, config).panel.write_json()

    assert first == second

