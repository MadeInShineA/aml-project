# AML Project

## Setup with Nix

1. Install [Nix](https://nixos.org/download/) with flakes enabled, and optionally [direnv](https://direnv.net/).
2. Enter the dev shell: `direnv allow` (or `nix develop`). It provides uv, Python, Quarto and the other tools.
3. Install the Python dependencies: `uv sync`
4. Open a notebook: `uv run marimo edit notebooks/<notebook>.py`

## Setup without Nix

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Quarto](https://quarto.org/docs/get-started/).
2. Install Python and the dependencies: `uv sync` (uv picks the Python version from `.python-version`)
3. Open a notebook: `uv run marimo edit notebooks/<notebook>.py`

## Website

The notebooks are published as a [Quarto](https://quarto.org) website on GitHub Pages, so results can be read in the browser without running anything.

- `main` is deployed at the root of the site.
- Every pull request gets its own preview at `pr-preview/pr-<number>/`, and its link is posted as a comment on the PR. The preview is removed when the PR closes.

The notebooks are exported to HTML locally and committed, because CI doesn't have the dataset.

## Opening a pull request

Create a branch from `main`, make your changes, then follow the case that matches your PR.

### If it touches a notebook

1. Export every notebook you changed:
   `uv run marimo export html notebooks/<notebook>.py -o site/notebooks/<notebook>.html`
2. For a new notebook, add it to the `Notebooks` menu in `_quarto.yml`.
3. Commit the notebook **and** its HTML export (plus `_quarto.yml` for a new notebook), push and open the PR.
4. Check the notebook in the preview link the bot comments on the PR.

### If it touches the website

For changes to `_quarto.yml` or `site/`:

1. Preview the site locally with `quarto preview`.
2. Push and open the PR.
3. Check the preview link the bot comments on the PR.

### If it touches neither

Push and open the PR. Nothing needs to be exported, and the preview will look the same as `main`.
