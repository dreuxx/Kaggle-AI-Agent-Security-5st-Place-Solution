# Standard Gateways

Standard gateways let you deploy Hearth competitions without writing custom gateway code. When no custom `*gateway.py` file is found, the gateway runner falls back to `StandardGateway`. It works out of the box with no config file if your dataset has test files (or sample submissions) with a shared row ID column. For more control, include a `gateway_config.json` to customize column names, file selection, timeouts, etc.

## Quick start

The simplest setup requires no config at all -- just make sure your dataset contains test files (named with `test` prefix/suffix, or in a `test/` directory) and a shared row ID column.

To customize behavior:

1. Copy `gateway_config_template.json` from this directory into your competition's `kaggle_evaluation/` package directory (alongside `core/` and `standard_gateways/`).
2. Edit the config to match your competition's data files and column names.
3. Remove any fields you don't need -- all fields are optional and have sensible defaults.

### Config file location

If used, the config file must be placed at `kaggle_evaluation/gateway_config.json` -- i.e., inside the `kaggle_evaluation/` package directory, not in the dataset root. On Kaggle this means the full path is `/kaggle/input/<competition_slug>/kaggle_evaluation/gateway_config.json`. Auto-discovery looks for the config relative to the package, so it works regardless of the competition slug.

## Config reference

All fields are optional. A completely empty `{}` config (or no config file at all) will work if your dataset contains CSV or Parquet files with a shared row ID column.

| Field | Type | Default | Description |
|---|---|---|---|
| `row_id_column` | string | *(auto-inferred)* | Column used to batch rows and join across files. If omitted, the first file's leftmost column that is also present in every other file is used (so file order matters). |
| `target_column` | string | `"prediction"` | Expected column name for predictions in the submission file. Used to structure the output file; does not affect scoring. |
| `timeout_seconds` | integer | `300` | Per-prediction response timeout in seconds. |
| `files` | array of strings | *(auto-discovered)* | Explicit list of data file paths to load, relative to the config file's directory. |

### File auto-discovery

When `files` is omitted, the gateway auto-discovers CSV and Parquet files (`.csv`, `.parquet`, `.pq`) in the dataset directory. Only test files and sample submissions are loaded:

- Files whose name is exactly `test`, starts with `test_`, or ends with `_test`, or that live under a `test/` directory (e.g. `test.csv`, `X_test.parquet`)
- Files named `sample_submission.*`

All other files (e.g. `train.csv`) are excluded. If you need to load files that don't match these patterns, list them explicitly in `files`.

The `test_`/`_test` match is a simple heuristic. It intentionally requires an underscore delimiter to avoid false positives on names like `testimonials.csv` or `latest.csv`, but it will still match any file named `something_test.csv`. If auto-discovery picks up the wrong files, list your data files explicitly via `files`.

### Row ID column validation

The row ID column (whether configured or inferred) is validated at startup:

- Must be present in every loaded file
- Must contain no null values
- Must have the same data type across all files
- Must contain the same set of values across all files

### Example config

**Multiple files:**

```json
{
    "row_id_column": "id",
    "target_column": "score",
    "files": ["test.csv", "test_metadata.parquet"]
}
```
