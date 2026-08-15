from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import polars as pl
from polars._typing import SchemaDict

from replenish.config.settings import FavoritaFiles, ProjectPaths


class DataLoader(Protocol):
    def load(self) -> pl.DataFrame:
        """Read one source into a Polars dataframe."""


@dataclass(frozen=True)
class CsvLoader:
    path: Path
    schema_overrides: SchemaDict

    def load(self) -> pl.DataFrame:
        return pl.read_csv(
            self.path,
            try_parse_dates=True,
            schema_overrides=self.schema_overrides,
        )


@dataclass(frozen=True)
class FavoritaTrainLoader:
    paths: ProjectPaths
    files: FavoritaFiles

    def load(self) -> pl.DataFrame:
        loader = CsvLoader(
            self.paths.raw_favorita / self.files.train,
            {"date": pl.Date, "store_nbr": pl.Int64, "family": pl.Utf8},
        )
        return loader.load()


@dataclass(frozen=True)
class StoresLoader:
    paths: ProjectPaths
    files: FavoritaFiles

    def load(self) -> pl.DataFrame:
        loader = CsvLoader(
            self.paths.raw_favorita / self.files.stores,
            {"store_nbr": pl.Int64, "city": pl.Utf8, "state": pl.Utf8},
        )
        return loader.load()


@dataclass(frozen=True)
class OilLoader:
    paths: ProjectPaths
    files: FavoritaFiles

    def load(self) -> pl.DataFrame:
        loader = CsvLoader(
            self.paths.raw_favorita / self.files.oil,
            {"date": pl.Date, "dcoilwtico": pl.Float64},
        )
        return loader.load()


@dataclass(frozen=True)
class HolidaysLoader:
    paths: ProjectPaths
    files: FavoritaFiles

    def load(self) -> pl.DataFrame:
        loader = CsvLoader(
            self.paths.raw_favorita / self.files.holidays,
            {"date": pl.Date, "type": pl.Utf8, "transferred": pl.Boolean},
        )
        return loader.load()


@dataclass(frozen=True)
class TransactionsLoader:
    paths: ProjectPaths
    files: FavoritaFiles

    def load(self) -> pl.DataFrame:
        loader = CsvLoader(
            self.paths.raw_favorita / self.files.transactions,
            {"date": pl.Date, "store_nbr": pl.Int64, "transactions": pl.Int64},
        )
        return loader.load()
