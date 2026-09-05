"""Config-driven generic gateway for simple competitions.

This lets hosts deploy Hearth competitions for simple use cases (e.g. the
Playground Series) without writing any custom gateway code. Instead of shipping a
custom `*gateway.py` in `deployed/`, a competition can include an optional
`gateway_config.json` in its dataset and rely on `StandardGateway` from the
`kaggle_evaluation` package.
"""

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

import kaggle_evaluation.core.templates
from kaggle_evaluation.core.base_gateway import GatewayRuntimeError, GatewayRuntimeErrorType

# Extensions we know how to load.
_SUPPORTED_EXTENSIONS = {'.csv', '.parquet', '.pq'}

_PACKAGE_DIR = Path(__file__).resolve().parent
_CONFIG_FILENAME = 'gateway_config.json'

# Recognized config keys. Anything else is a likely typo and raises loudly.
_ALLOWED_CONFIG_KEYS = frozenset({'row_id_column', 'target_column', 'timeout_seconds', 'files'})


def _load_dataframe(path: Path) -> pl.DataFrame:
    """Load a CSV or parquet file."""
    suffix = path.suffix.lower()
    if suffix == '.csv':
        # High infer_schema_length prevents bad type inference on large files.
        return pl.read_csv(path, infer_schema_length=10**5)
    if suffix in ('.parquet', '.pq'):
        return pl.read_parquet(path)
    raise GatewayRuntimeError(
        GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
        f'Unsupported file extension {suffix} for {path}; expected one of {sorted(_SUPPORTED_EXTENSIONS)}',
    )


def _is_sample_submission(path: Path) -> bool:
    """Return True if a file looks like a sample submission."""
    stem = path.stem.lower()
    return stem.startswith(('sample_submission', 'sample-submission'))


def _is_test_or_sample_submission(path: Path) -> bool:
    """Return True if a file or directory looks like a test file or a sample submission.

    A file qualifies as a test file if its stem is exactly ``test``, starts with
    ``test_``, ends with ``_test``, or it lives under a directory named ``test``.
    Requiring the underscore delimiter avoids false positives on names like
    ``testimonials.csv`` or ``latest.csv``.
    """
    if _is_sample_submission(path):
        return True
    stem = path.stem.lower()
    if stem == 'test' or stem.startswith('test_') or stem.endswith('_test'):
        return True
    return 'test' in [part.lower() for part in path.parts]


def _load_config(config_path: str | Path | None = None) -> tuple[Path | None, dict[str, Any]]:
    """Discover, read, and validate the gateway config.

    If ``config_path`` is not provided, auto-discovers ``gateway_config.json``
    inside the ``kaggle_evaluation/`` package directory. Returns ``(resolved_path, config_dict)``.
    The config dict is empty when no config file exists.

    An explicitly provided ``config_path`` that does not exist raises, so typos fail
    loudly. A missing auto-discovered config is silently treated as no config.
    """
    explicit = config_path is not None
    if config_path is None:
        candidate = _PACKAGE_DIR.parent / _CONFIG_FILENAME
        if candidate.exists():
            config_path = candidate

    if config_path is not None:
        config_path = Path(config_path)

    config: dict[str, Any] = {}
    if config_path is not None and config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    elif explicit:
        raise GatewayRuntimeError(
            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
            f'Config path {config_path} was provided but does not exist.',
        )

    unknown_keys = set(config) - _ALLOWED_CONFIG_KEYS
    if unknown_keys:
        raise GatewayRuntimeError(
            GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
            f'Unknown config keys: {sorted(unknown_keys)}. Allowed keys: {sorted(_ALLOWED_CONFIG_KEYS)}.',
        )

    return config_path, config


class StandardGateway(kaggle_evaluation.core.templates.Gateway):
    """A generic gateway for simple competitions, driven by a JSON config.

    Config fields (all optional, with sensible defaults):
        - row_id_column (str): The column to batch on. Defaults to the leftmost column
          shared across all files.
        - target_column (str): Expected column name for predictions in the submission
          file. Defaults to 'prediction'.
        - timeout_seconds (int): Per-prediction response timeout. Defaults to 300.
        - files (list of str): File paths to load, relative to the data directory.
          Defaults to auto-discovering test files and sample submissions.
    """

    def __init__(self, config_path: str | Path | None = None, competition_data_folder: str | Path | None = None, file_share_dir: str | None = None):
        self.config_path, self.config = _load_config(config_path)

        # Fall back to the config file's directory when no explicit data folder is given.
        if not competition_data_folder and self.config_path is not None:
            competition_data_folder = self.config_path.parent

        super().__init__(competition_data_folder=competition_data_folder, file_share_dir=file_share_dir)

        self.row_id_column_name = self.config.get('row_id_column')
        self._explicit_target_column = 'target_column' in self.config
        self.target_column_name = self.config.get('target_column', 'prediction')
        self._numeric_prediction_columns: list[str] = []
        self.set_response_timeout_seconds(self.config.get('timeout_seconds', 60 * 5))

    def _resolve_file_paths(self) -> list[Path]:
        """Resolve the list of data files to load from config, or auto-discover them.

        When auto-discovering (no explicit ``files`` in config), only test files and
        sample submissions are included. A file qualifies as a test file if its stem
        starts or ends with ``test`` or it lives under a directory named ``test``.
        """
        # The base gateway always resolves competition_data_folder to a concrete Path.
        data_folder = self.competition_data_folder
        assert data_folder is not None

        configured_files = self.config.get('files')
        if configured_files:
            return [data_folder / f for f in configured_files]

        return sorted(
            p for p in data_folder.rglob('*') if p.is_file() and p.suffix.lower() in _SUPPORTED_EXTENSIONS and _is_test_or_sample_submission(p)
        )

    def _infer_row_id_column(self, dataframes: list[pl.DataFrame]) -> str:
        """Infer the row ID column as the leftmost column shared across all files."""
        common_columns = set(dataframes[0].columns)
        for df in dataframes[1:]:
            common_columns &= set(df.columns)
        if not common_columns:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                'Could not infer a row ID column: the loaded files share no common columns.',
            )
        return next(column for column in dataframes[0].columns if column in common_columns)

    def _validate_row_id_column(self, row_id_column: str, dataframes: list[pl.DataFrame], paths: list[Path]) -> None:
        """Validate that row_id_column is present, non-null, and type/value-consistent across all files."""
        missing = [str(paths[i]) for i, df in enumerate(dataframes) if row_id_column not in df.columns]
        if missing:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'Row ID column {row_id_column!r} not found in: {missing}',
            )

        null_files = [str(paths[i]) for i, df in enumerate(dataframes) if df[row_id_column].null_count() > 0]
        if null_files:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'Row ID column {row_id_column!r} contains nulls in: {null_files}',
            )

        dtypes = {str(paths[i]): df[row_id_column].dtype for i, df in enumerate(dataframes)}
        if len(set(dtypes.values())) > 1:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'Row ID column {row_id_column!r} has mismatched types across files: {dtypes}',
            )

        reference_keys = set(dataframes[0][row_id_column].to_list())
        for i, df in enumerate(dataframes[1:], start=1):
            other_keys = set(df[row_id_column].to_list())
            if reference_keys != other_keys:
                only_in_first = reference_keys - other_keys
                only_in_other = other_keys - reference_keys
                parts = []
                if only_in_first:
                    parts.append(f'missing from {paths[i]}: {sorted(only_in_first)[:5]}')
                if only_in_other:
                    parts.append(f'extra in {paths[i]}: {sorted(only_in_other)[:5]}')
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                    f'Row ID column {row_id_column!r} values differ between {paths[0]} and {paths[i]}. {"; ".join(parts)}',
                )

    def generate_data_batches(self) -> Generator[tuple[tuple[pl.DataFrame, ...], Any]]:
        file_paths = self._resolve_file_paths()
        if not file_paths:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'No data files found in {self.competition_data_folder}',
            )

        dataframes = [_load_dataframe(p) for p in file_paths]

        # If a sample submission is present and no explicit target_column was configured,
        # clear the default so the base gateway uses whatever columns the competitor returns.
        # This supports multi-target competitions without requiring config changes.
        sample_sub_paths = [p for p in file_paths if _is_sample_submission(p)]
        if len(sample_sub_paths) > 1:
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.GATEWAY_RAISED_EXCEPTION,
                f'Expected at most one sample submission file but found {len(sample_sub_paths)}: {sample_sub_paths}',
            )
        if sample_sub_paths and not self._explicit_target_column:
            self.target_column_name = None

        row_id_column = self.row_id_column_name or self._infer_row_id_column(dataframes)
        self._validate_row_id_column(row_id_column, dataframes, file_paths)
        self.row_id_column_name = row_id_column

        # If the sample submission's non-key columns are all numeric, enable
        # numeric validation (finite, non-null) on predictions.
        self._numeric_prediction_columns = []
        if sample_sub_paths:
            sample_sub_df = dataframes[file_paths.index(sample_sub_paths[0])]
            non_key_cols = [c for c in sample_sub_df.columns if c != row_id_column]
            if non_key_cols and all(sample_sub_df[c].dtype.is_numeric() for c in non_key_cols):
                self._numeric_prediction_columns = non_key_cols

        # Partition each file by the row ID column once (linear) rather than filtering
        # per key (quadratic). Missing keys in a given file yield an empty DataFrame.
        key_values = dataframes[0][row_id_column].unique(maintain_order=True).to_list()
        partitions = [df.partition_by(row_id_column, as_dict=True, maintain_order=True) for df in dataframes]
        empty_frames = [df.clear() for df in dataframes]
        for key_value in key_values:
            batch = tuple(partition.get((key_value,), empty_frames[i]) for i, partition in enumerate(partitions))
            yield (batch, key_value)

    def _validate_numeric(self, series: pl.Series, label: str) -> None:
        if not series.dtype.is_numeric():
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.INVALID_SUBMISSION,
                f'{label} must be numeric but got {series.dtype}.',
            )
        if series.is_null().any() or series.is_nan().any():
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.INVALID_SUBMISSION,
                f'{label} contains null or NaN values.',
            )
        if series.is_infinite().any():
            raise GatewayRuntimeError(
                GatewayRuntimeErrorType.INVALID_SUBMISSION,
                f'{label} contains non-finite values.',
            )

    def competition_specific_validation(
        self,
        prediction_batch: Any,
        row_ids: pl.DataFrame | pl.Series | pd.DataFrame | pd.Series,
        data_batch: Any,
    ) -> None:
        if not self._numeric_prediction_columns:
            return

        if isinstance(prediction_batch, (int, float)):
            if len(self._numeric_prediction_columns) != 1:
                raise GatewayRuntimeError(
                    GatewayRuntimeErrorType.INVALID_SUBMISSION,
                    f'Scalar prediction is only valid when there is exactly one target column, but expected {len(self._numeric_prediction_columns)}.',
                )
            self._validate_numeric(pl.Series([prediction_batch]), 'Prediction')
            return

        if isinstance(prediction_batch, pd.DataFrame):
            prediction_batch = pl.from_pandas(prediction_batch)
        if not isinstance(prediction_batch, pl.DataFrame):
            return

        for col in self._numeric_prediction_columns:
            if col not in prediction_batch.columns:
                continue
            self._validate_numeric(prediction_batch[col], f'Column {col!r}')
