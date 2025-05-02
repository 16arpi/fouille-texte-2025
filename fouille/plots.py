#!/usr/bin/env python3


from loguru import logger
import polars as pl
import typer

from fouille.config import CLEAN_DATASET, CLEAN_CATEGORIES_VIZ, RAW_CATEGORIES, RAW_CATEGORIES_LIST, RAW_CATEGORIES_VIZ, RAW_DATASET

app = typer.Typer()


def plot_raw_categories_distribution():
	logger.info("Generating categorical distribution plot from raw data...")

	lf = pl.scan_parquet(RAW_DATASET)

	# Unique individual categories
	unique_cats = lf.select("categories").unique().explode("categories").unique().collect()
	unique_cats.write_csv(RAW_CATEGORIES)

	# Unique categories lists
	unique_cats_list = lf.select("categories").unique().collect()
	unique_cats_list.write_json(RAW_CATEGORIES_LIST)
	# Mangle that to make it easier to grep
	unique_cats_str = lf.select(pl.col("categories").list.join(",")).unique().collect()
	unique_cats_str.write_csv(RAW_CATEGORIES_LIST.with_suffix(".csv"))

	# NOTE: It might also be mildly useful to check for rows with no categories:
	# lf.filter(pl.col("categories").list.len() == 0).select(pl.all()).collect()
	# NOTE: As well as extracting specific rows based on the title, to check a specific Book:
	# lf.filter(pl.col("title").str.starts_with("Page:Érasme")).select(pl.col(["title", "categories"])).collect()

	# Per individual category distribution
	distrib = lf.select("categories").explode("categories").group_by("categories").len().collect()

	chart = (
		distrib.plot.bar(
			x="categories",
			y="len",
			color="categories",
		)
		.properties(width=1024, title="Distribution par catégories brutes")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Compte"
	chart.save(RAW_CATEGORIES_VIZ)

	logger.success("Plot generation complete.")


def plot_clean_categories_distribution():
	logger.info("Generating categorical distribution plot from clean data...")

	lf = pl.scan_parquet(CLEAN_DATASET)

	# Per individual category distribution
	distrib = lf.select("pubyear").group_by("pubyear").len().collect()

	chart = (
		distrib.plot.bar(
			x="pubyear",
			y="len",
			color="pubyear",
		)
		.properties(width=1024, title="Distribution par catégories exactes")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Compte"
	chart.save(CLEAN_CATEGORIES_VIZ)

	logger.success("Plot generation complete.")


@app.command()
def main() -> None:
	plot_raw_categories_distribution()
	plot_clean_categories_distribution()


if __name__ == "__main__":
	app()
