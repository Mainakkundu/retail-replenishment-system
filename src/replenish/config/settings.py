from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FavoritaFiles:
    train: str = "train.csv"
    stores: str = "stores.csv"
    oil: str = "oil.csv"
    holidays: str = "holidays_events.csv"
    transactions: str = "transactions.csv"


@dataclass(frozen=True)
class DataQualityConfig:
    expected_train_rows: int = 3_000_888
    expected_all_zero_series: int = 53
    expected_oil_nulls_before_fill: int = 43
    calendar_start: str = "2013-01-01"
    calendar_end: str = "2017-08-15"
    christmas_month: int = 12
    christmas_day: int = 25


@dataclass(frozen=True)
class ReproducibilityConfig:
    seed: int = 20260815


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = Path(".")
    raw_favorita: Path = Path("data/raw/favorita")
    interim: Path = Path("data/interim")
    processed: Path = Path("data/processed")
    panel: Path = Path("data/interim/panel.parquet")


@dataclass(frozen=True)
class Settings:
    paths: ProjectPaths = ProjectPaths()
    files: FavoritaFiles = FavoritaFiles()
    data_quality: DataQualityConfig = DataQualityConfig()
    reproducibility: ReproducibilityConfig = ReproducibilityConfig()


def default_settings() -> Settings:
    return Settings()

