#!/usr/bin/env python3

from pathlib import Path
import time

from loguru import logger
import polars as pl
import typer

from fouille.config import RAW_DATASET, PROCESSED_DATA_DIR, RAW_DATA_DIR

app = typer.Typer()


def extract_gold_classes():
	logger.info("Extracting gold classes from raw data...")

	lf = pl.scan_parquet(RAW_DATASET)

	lf.select(
		pl.col("categories")
		.list.eval(pl.element().str.extract_all(r"(\d{4})")  # Extract *all* dates from each str element in categories (into a List[str] per element)
			.flatten()  # Flatten the List[List[str]] extract_all created back into a List[str]
			.cast(pl.UInt16)  # Cast it to a List[UInt16]
		).list.max()  #  Keep the largest date (i.e., the latest publication date)
	).collect()

@app.command()
def main() -> None:
	extract_gold_classes()


if __name__ == "__main__":
	app()
