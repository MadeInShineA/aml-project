import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import kagglehub
    import polars as pl
    from pathlib import Path
    import pickle
    import shutil
    import tempfile
    import numpy as np

    return Path, kagglehub, mo, np, pickle, pl, shutil, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Load data

    Load the raw WESAD data and save it as 4 Parquet files, one per sampling rate, in `data/processed/`.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Download the dataset
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Download WESAD from Kaggle into `data/WESAD`, skipped if it's already there.
    """)


@app.cell
def _(Path, kagglehub, mo, shutil, tempfile):
    def download_wasf_dataset() -> Path:
        # pyrefly: ignore[missing-attribute]
        data_dir = mo.notebook_dir().parent / "data"

        # If the data doesn't exist
        if not (data_dir / "WESAD").exists():
            # Create a temporaty directory where to download the data (so kaggle doesn't complain about non-empty dir)
            with tempfile.TemporaryDirectory(dir=data_dir) as tmp:
                kagglehub.dataset_download(
                    "mohamedasem318/wesad-full-dataset",
                    output_dir=tmp,
                )

                # Move only the subject data to /data/WESAD
                shutil.move(Path(tmp) / "WESAD", data_dir / "WESAD")

            dataset_path: Path = data_dir / "WESAD"

        dataset_path: Path = data_dir / "WESAD"
        return dataset_path

    return (download_wasf_dataset,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading functions
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Signals and sampling rates, per the [dataset documentation](https://archive.ics.uci.edu/dataset/465/wearable+stress+and+affect+detection):

    | Signals | Sampling rate |
    |---|---:|
    | Chest ACC (3-axis), ECG, EMG, EDA, temperature, respiration, labels | 700 Hz |
    | Wrist ACC (3-axis) | 32 Hz |
    | Wrist BVP | 64 Hz |
    | Wrist EDA, temperature | 4 Hz |
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Load one subject into 4 Polars DataFrames, one per sampling rate, each with a `time_s` column.
    """)


@app.cell
def _(Path, np, pickle, pl):
    def _as_1d(values: np.ndarray) -> np.ndarray:
        """Convert a one-channel signal to shape (n,)."""
        values = np.asarray(values)

        if values.ndim == 1:
            return values

        if values.ndim == 2 and values.shape[1] == 1:
            return values[:, 0]

        raise ValueError(
            f"Expected a one-channel signal with shape (n,) or (n, 1), "
            f"got {values.shape}"
        )

    def _make_frame(
        signals: dict[str, np.ndarray],
        sampling_rate: float,
        subject_id: str,
    ) -> pl.DataFrame:
        """Create one DataFrame for signals sharing a sampling rate."""
        lengths = {name: len(signal) for name, signal in signals.items()}

        if len(set(lengths.values())) != 1:
            raise ValueError(
                f"Cannot combine unequal signal lengths: {lengths}"
            )

        n_rows = next(iter(lengths.values()))

        df = pl.DataFrame(
            {
                "time_s": np.arange(n_rows, dtype=np.float64) / sampling_rate,
                **signals,
            }
        )

        return df.with_columns(pl.lit(subject_id).alias("subject_id")).select(
            ["subject_id", "time_s", *signals.keys()]
        )

    def load_subject(
        data_path: Path, subject_id: str
    ) -> dict[str, pl.DataFrame]:
        with open(data_path / subject_id / f"{subject_id}.pkl", "rb") as f:
            data = pickle.load(f, encoding="latin1")

        chest = data["signal"]["chest"]
        wrist = data["signal"]["wrist"]

        chest_acc = np.asarray(chest["ACC"])
        wrist_acc = np.asarray(wrist["ACC"])

        chest_df = _make_frame(
            {
                "label": _as_1d(data["label"]),
                "chest_acc_x": chest_acc[:, 0],
                "chest_acc_y": chest_acc[:, 1],
                "chest_acc_z": chest_acc[:, 2],
                "chest_ecg": _as_1d(chest["ECG"]),
                "chest_emg": _as_1d(chest["EMG"]),
                "chest_eda": _as_1d(chest["EDA"]),
                "chest_temp": _as_1d(chest["Temp"]),
                "chest_resp": _as_1d(chest["Resp"]),
            },
            sampling_rate=700.0,
            subject_id=subject_id,
        )

        wrist_acc_df = _make_frame(
            {
                "wrist_acc_x": wrist_acc[:, 0],
                "wrist_acc_y": wrist_acc[:, 1],
                "wrist_acc_z": wrist_acc[:, 2],
            },
            sampling_rate=32.0,
            subject_id=subject_id,
        )

        wrist_bvp_df = _make_frame(
            {
                "wrist_bvp": _as_1d(wrist["BVP"]),
            },
            sampling_rate=64.0,
            subject_id=subject_id,
        )

        wrist_eda_temp_df = _make_frame(
            {
                "wrist_eda": _as_1d(wrist["EDA"]),
                "wrist_temp": _as_1d(wrist["TEMP"]),
            },
            sampling_rate=4.0,
            subject_id=subject_id,
        )

        return {
            "chest": chest_df,
            "wrist_acc": wrist_acc_df,
            "wrist_bvp": wrist_bvp_df,
            "wrist_eda_temp": wrist_eda_temp_df,
        }

    return (load_subject,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Load every subject and concatenate them into the same 4 DataFrames.
    """)


@app.cell
def _(Path, load_subject, pl):
    def load_datasets(
        dataset_path: Path,
    ) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:

        subject_ids: list[str] = sorted(
            (
                p.name
                for p in Path(dataset_path).iterdir()
                if p.is_dir()
                and p.name.startswith("S")
                and (p / f"{p.name}.pkl").exists()
            ),
            key=lambda s: int(s[1:]),
        )

        frames: dict[str, list[pl.DataFrame]] = {
            "chest": [],
            "wrist_acc": [],
            "wrist_bvp": [],
            "wrist_eda_temp": [],
        }

        for subject_id in subject_ids:
            subject = load_subject(Path(dataset_path), subject_id)
            for name, df in subject.items():
                frames[name].append(df)

        chest_df: pl.DataFrame = pl.concat(frames["chest"], how="vertical")
        wrist_acc_df: pl.DataFrame = pl.concat(
            frames["wrist_acc"], how="vertical"
        )
        wrist_bvp_df: pl.DataFrame = pl.concat(
            frames["wrist_bvp"], how="vertical"
        )
        wrist_eda_temp_df: pl.DataFrame = pl.concat(
            frames["wrist_eda_temp"], how="vertical"
        )

        return chest_df, wrist_acc_df, wrist_bvp_df, wrist_eda_temp_df

    return (load_datasets,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Save the 4 DataFrames as Parquet files in `data/processed/`.
    """)


@app.cell
def _(Path, pl):
    def save_datasets(datasets: dict[str, pl.DataFrame], output_path: Path):

        for name, df in datasets.items():
            df.write_parquet(
                output_path / f"{name}.parquet", compression="zstd"
            )

    return (save_datasets,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load and cache the raw data

    Reads the cached Parquet files if all 4 exist, otherwise rebuilds them from the raw pickles.
    """)


@app.cell
def _(download_wasf_dataset):
    dataset_path = download_wasf_dataset()
    return (dataset_path,)


@app.cell
def _(Path, dataset_path):
    processed_dir: Path = Path(dataset_path).parent / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    dataset_names: tuple[str, ...] = ("chest", "wrist_acc", "wrist_bvp", "wrist_eda_temp")

    processed_exists: bool = all(
        (processed_dir / f"{name}.parquet").exists() for name in dataset_names
    )
    return dataset_names, processed_dir, processed_exists


@app.cell
def _(
    dataset_names: tuple[str, ...],
    dataset_path,
    load_datasets,
    pl,
    processed_dir: "Path",
    processed_exists: bool,
    save_datasets,
):
    if processed_exists:
        datasets = {
            name: pl.read_parquet(processed_dir / f"{name}.parquet")
            for name in dataset_names
        }
    else:
        chest_df, wrist_acc_df, wrist_bvp_df, wrist_eda_temp_df = load_datasets(
            dataset_path
        )

        datasets = {
            "chest": chest_df,
            "wrist_acc": wrist_acc_df,
            "wrist_bvp": wrist_bvp_df,
            "wrist_eda_temp": wrist_eda_temp_df,
        }

        save_datasets(datasets, processed_dir)
    return (datasets,)


@app.cell
def _(datasets, mo):
    mo.ui.tabs(
        {
            name: mo.vstack([mo.md(f"Shape: **{df.shape[0]:,} × {df.shape[1]}**"), df.head()])
            for name, df in datasets.items()
        }
    )


if __name__ == "__main__":
    app.run()
