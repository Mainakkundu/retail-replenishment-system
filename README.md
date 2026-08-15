# Favorita Replenishment Forecasting

Current phase: P0 setup and data foundation.

The raw data contract is defined in `constitution.md`: Favorita competition CSVs
must live under `data/raw/favorita/`. The `data/` and `outputs/` trees are
gitignored and are never committed.

To download the Kaggle data, place `kaggle.json` in a gitignored config folder:

```bash
mkdir -p data/raw/favorita/.kaggle
cp /path/to/kaggle.json data/raw/favorita/.kaggle/kaggle.json
chmod 600 data/raw/favorita/.kaggle/kaggle.json
KAGGLE_CONFIG_DIR=data/raw/favorita/.kaggle \
  .venv/bin/kaggle competitions download \
  -c store-sales-time-series-forecasting \
  -p data/raw/favorita
```

After unzipping the archive, build the P0 panel:

```bash
.venv/bin/python -m replenish.data.build_panel
```

