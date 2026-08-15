from __future__ import annotations

from pathlib import Path

from replenish.config.settings import Settings, default_settings
from replenish.data.loaders import FavoritaTrainLoader, OilLoader
from replenish.data.panel import build_panel, forward_fill_oil
from replenish.data.validators import (
    AllZeroSeriesValidator,
    DailyCalendarValidator,
    LeadingZeroTruncationValidator,
    OilNullValidator,
    TrainRowCountValidator,
    Validator,
)


def run(settings: Settings) -> None:
    train = FavoritaTrainLoader(settings.paths, settings.files).load()
    oil = OilLoader(settings.paths, settings.files).load()
    filled_oil = forward_fill_oil(oil)
    result = build_panel(train, settings.data_quality)

    validators: list[Validator] = [
        TrainRowCountValidator(train, settings.data_quality),
        AllZeroSeriesValidator(train, settings.data_quality),
        OilNullValidator(filled_oil),
        DailyCalendarValidator(result.panel),
        LeadingZeroTruncationValidator(result.panel),
    ]
    results = [item.validate() for item in validators]
    failures = [result for result in results if not result.passed]
    if failures:
        details = "; ".join(f"{failure.name}: {failure.detail}" for failure in failures)
        raise ValueError(details)

    output_path = Path(settings.paths.panel)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.panel.write_parquet(output_path)


def main() -> None:
    run(default_settings())


if __name__ == "__main__":
    main()
