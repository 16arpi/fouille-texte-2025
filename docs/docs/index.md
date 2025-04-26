# Intro Fouille de Texte - 2024/2025 documentation!

## Description

End of term project

## Commands

The Makefile contains the central entry points for common tasks related to this project.

### Syncing data to cloud storage

* `make sync_data_up` will use `aws s3 sync` to recursively sync files in `data/` up to `s3://tal-m1-fouille/data/`.
* `make sync_data_down` will use `aws s3 sync` to recursively sync files from `s3://tal-m1-fouille/data/` to `data/`.


