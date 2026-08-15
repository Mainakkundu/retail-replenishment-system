# Handoff

## Current state

- Branch: `p0-setup`
- Current phase: P0 setup and data foundation
- Remote: `https://github.com/Mainakkundu/retail-replenishment-system.git`
- Do not read, edit, or write `decisions.md` unless the user explicitly changes
  the repo rules.

## What is done

- Git repository initialized.
- Remote `origin` configured.
- Branch `p0-setup` pushed to GitHub.
- Commit identity corrected to `Mainak Kundu <mainakmarket@gmail.com>`.
- P0 scaffold added:
  - package skeleton under `src/replenish/`
  - typed config in `src/replenish/config/settings.py`
  - data loaders, validators, and panel builder in `src/replenish/data/`
  - tests under `tests/`
  - README with Kaggle download instructions
- Constitution updated to allow pandas, NumPy, Polars, and DuckDB.
- Favorita archive placed under `data/raw/favorita/` and extracted locally.
- P0 panel built at `data/interim/panel.parquet`.
- Oil handling fixed for the leading null on `2013-01-01` by filling from the
  first known oil value after forward-fill.
- Raw oil null-count validator added so the expected 43 nulls are checked before
  fill, and zero nulls are checked after fill.
- Build command now prints P0 validator/count summaries.

## Verification already run

```text
.venv/bin/python -m pytest
.venv/bin/ruff check src tests
.venv/bin/mypy src
PYTHONPATH=src .venv/bin/python -m replenish.data.build_panel
```

All passed after the latest local changes.

Real-data P0 validation observed:

```
raw_train_rows=3000888
all_zero_series_count=53
leading_zero_rows_dropped=468052
oil_nulls_before_fill=43
oil_nulls_after_fill=0
panel_rows=2450500
panel_series=1729
panel_sha256=0cea9827f4c70895182c29d53df2cf272f57a1c0201ae1f9b7fc293aa7188f72
```

Two consecutive panel builds produced the same SHA-256 hash.

## Next step

Report the P0 exit criteria status and ask whether to push `p0-setup`. After the
user approves moving on, create/switch to `p1-ts-eda` and start
`notebooks/01_eda_features.ipynb` § time series only.

## Git workflow reminder

Work on one branch per phase. Do not merge into `main` without user review and
explicit approval.
