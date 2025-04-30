#!/usr/bin/env python3

from pathlib import Path

from loguru import logger
import polars as pl
import typer

from fouille.config import RAW_DATASET, RAW_CATEGORIES, RAW_CATEGORIES_VIZ, FIGURES_DIR

app = typer.Typer()


def plot_raw_categories_distribution():
	logger.info("Generating categorical distribution plot from raw data...")

	lf = pl.read_parquet(RAW_DATASET).lazy()

	# Unique individual categories
	unique_cats = lf.select("categories").unique().explode("categories").unique().collect()
	unique_cats.write_csv(RAW_CATEGORIES)

	# NOTE: It might also be mildloy useful to check for rows with no categories:
	# lf.filter(pl.col("categories").list.len() == 0).select(pl.all()).collect()

	# Per individual category distribution
	distrib = lf.select("categories").explode("categories").group_by("categories").len().collect()

	chart = (
		distrib.plot.bar(
			x="categories",
			y="len",
			color="categories",
		)
		.properties(title="Distribution par catégories brutes")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Compte"
	chart.save(RAW_CATEGORIES_VIZ)

	logger.success("Plot generation complete.")


@app.command()
def main() -> None:
	plot_raw_categories_distribution()


if __name__ == "__main__":
	app()
