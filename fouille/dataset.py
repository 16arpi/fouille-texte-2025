#!/usr/bin/env python3


from loguru import logger
import polars as pl
from polars_splitters import split_into_train_eval
import typer

from fouille.config import CLEAN_DATASET, RAW_DATASET, FULL_DATASET, TRAIN_DATASET, TEST_DATASET, DEV_DATASET

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


def label_gold_classes():
	logger.info("Labelling clean data w/ gold classes...")

	lf = pl.scan_parquet(CLEAN_DATASET)

	lf = (
		lf.with_columns(
			# Chop things up in 50 years periods
			# (by rounding pubyear down to the nearest multiple of 50)
			semicentury=pl.col("pubyear") // 50 * 50
		)
	)
	# NOTE: Confirm groupings w/ lf.group_by("semicentury").agg(pl.all()).collect()

	# Dump to disk
	logger.info("Dumping to disk...")
	lf.sink_parquet(FULL_DATASET)


def split_dataset():
	logger.info("Stratified split on gold class...")

	lf = pl.scan_parquet(FULL_DATASET)

	# Start with a 80/20 split
	lf_train, lf_eval = split_into_train_eval(
		lf,
		eval_rel_size=0.2,
		stratify_by="semicentury",
		shuffle=True,
		seed=42,
		validate=True,
		as_lazy=False,  # NYI?
		rel_size_deviation_tolerance=0.1,
	)

	# And split the 20 in half for an 80/10/10
	lf_test, lf_dev = split_into_train_eval(
		lf_eval,
		eval_rel_size=0.5,
		stratify_by="semicentury",
		shuffle=True,
		seed=42,
		validate=True,
		as_lazy=False,  # NYI?
		rel_size_deviation_tolerance=0.1,
	)

	# Dump to disk
	logger.info("Dumping to disk...")
	lf_train.write_parquet(TRAIN_DATASET)
	lf_test.write_parquet(TEST_DATASET)
	lf_dev.write_parquet(DEV_DATASET)


@app.command()
def main() -> None:
	extract_gold_classes()
	label_gold_classes()
	split_dataset()


if __name__ == "__main__":
	app()
