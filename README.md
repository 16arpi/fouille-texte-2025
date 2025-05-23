# Intro Fouille de Texte - 2024/2025

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

End of term project, text classification by date.

## Project Organization

```
├── LICENSE             <- Open-source license if one is chosen
├── Makefile            <- Makefile with convenience commands like `make data` or `make train`
├── README.md           <- The top-level README for developers using this project.
├── data
│   ├── external        <- Data from third party sources.
│   ├── interim         <- Intermediate data that has been transformed.
│   ├── processed       <- The final, canonical data sets for modeling.
│   ├── raw             <- The original, immutable data dump.
│   ├── make_dataset.sh <- Initial data ingest pipeline.
│   └── extract_data.py <- Main data wrangling logic.
│
├── pyproject.toml      <- Project configuration file with package metadata for
│                          fouille and configuration for tools like black
│
├── references          <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports             <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures         <- Generated graphics and figures to be used in reporting
│
├── requirements.txt    <- The requirements file for reproducing the analysis environment, e.g.
│                          generated with `pip freeze > requirements.txt`
│
├── setup.cfg           <- Configuration file for flake8
│
└── fouille   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes fouille a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling
    │   ├── __init__.py
    │   └── models.py           <- Code to train models & run model inference with them
    │
    └── plots.py                <- Code to create visualizations
```

--------

## [Final Report](reports/compte-rendu.md)
