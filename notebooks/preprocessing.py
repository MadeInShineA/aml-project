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

    return Path, kagglehub, mo, pickle, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the dataset
    """)


@app.cell
def _(kagglehub):
    dataset_path: str = kagglehub.dataset_download(
        "mohamedasem318/wesad-full-dataset"
    )
    dataset_path
    return (dataset_path,)


@app.cell
def _(pickle, pl):
    def load_subject(pkl_path: str) -> pl.DataFrame:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f, encoding="latin1")

        label = data["label"]
        chest = data["signal"]["chest"]
        wrist = data["signal"]["wrist"]

        n = len(label)
        return pl.DataFrame(
            {
                "label": label,
                "chest_ecg": chest["ECG"][:n, 0],
                "chest_eda": chest["EDA"][:n, 0],
                "chest_emg": chest["EMG"][:n, 0],
                "chest_resp": chest["Resp"][:n, 0],
                "chest_temp": chest["Temp"][:n, 0],
            }
        )

    return (load_subject,)


@app.cell
def _(Path, dataset_path: str, load_subject, pl):
    df: pl.DataFrame = load_subject(str(Path(dataset_path) / "WESAD" / "S2" / "S2.pkl"))
    print(df.head())
    print(df.shape)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
