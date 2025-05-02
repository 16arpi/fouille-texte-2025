#!/usr/bin/env python3


from loguru import logger
import polars as pl
import typer

from fouille.config import CLEAN_DATASET, RAW_DATASET

app = typer.Typer()


def extract_gold_classes():
	logger.info("Extracting exact gold classes from raw data...")

	lf = pl.scan_parquet(RAW_DATASET)

	lf = (
		lf.with_columns(
			pubyear=pl.col("categories")
			.list.eval(
				# Skip over the "Domaine public en YYYY" categories
				pl.when(~pl.element().str.starts_with("Domaine public en"))
				.then(
					# Extract *all* dates from each str element in categories (into a List[str] per element)
					# (ignore > 2999, because there are typos in the data -_-" (5793 & 5796))
					pl.element().str.extract_all(r"([1-2]\d{3})")
				)
				# Flatten the List[List[str]] extract_all created back into a List[str]
				.flatten()
				# Cast it to a List[UInt16]
				.cast(pl.UInt16)
			)
			# Only keep the most recent date (i.e., the latest publication date)
			# NOTE: This is important because translations may have been published much later than their source
			.list.max()
		)
		# Drop rows with no pubyear
		.drop_nulls(subset=["pubyear"])
		# Reorder columns (dropping the original categories column in the process)
		.select("title", "pubyear", "quality", "text")
	)
	# c.f., lf.describe() to confirm we no longer have bogus max values

	# Dump to disk
	logger.info("Dumping to disk...")
	lf.sink_parquet(CLEAN_DATASET)


@app.command()
def main() -> None:
	extract_gold_classes()


if __name__ == "__main__":
	app()
