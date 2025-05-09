#!/usr/bin/env python3


import altair as alt
from loguru import logger
import polars as pl
import typer

from fouille.config import (
	CLEAN_CATEGORIES_VIZ,
	CLEAN_DATASET,
	FULL_DATASET,
	GOLD_CATEGORIES_VIZ,
	RAW_CATEGORIES,
	RAW_CATEGORIES_LIST,
	RAW_CATEGORIES_VIZ,
	RAW_DATASET,
)

# Let vegafusion trim the embedded data
# c.f., https://altair-viz.github.io/user_guide/large_datasets.html
# alt.data_transformers.enable("vegafusion")
app = typer.Typer()


def plot_raw_categories_distribution() -> None:
	"""
	Raw category distribution plot.
	The plot itself is extremely unreadable,
	so we also dump a more actionable list of categories in CSV
	"""

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
		.properties(width=1024, title="Distribution par catégorie brute")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Compte"
	chart.save(RAW_CATEGORIES_VIZ)

	logger.success("Plot generation complete.")


def plot_clean_categories_distribution() -> None:
	"""
	Publication year distribution plot
	"""

	logger.info("Generating categorical distribution plot from clean data...")

	lf = pl.scan_parquet(CLEAN_DATASET)

	distrib = (
		# We don't need any other columns
		lf.select("pubyear", "text")
		# Duh'
		.group_by("pubyear")
		# Compute the amount of rows per group (i.e., pages)
		# Then the the amount of characters per group (each group is an aggregate of rows)
		.agg(pl.len().alias("pages"), pl.col("text").str.len_chars().sum().alias("characters"))
		.collect()
	)

	# Pages (i.e., rows) per individual category distribution
	chart = (
		distrib.plot.bar(
			x="pubyear",
			y="pages",
			color="pubyear",
		)
		.properties(width=1024, title="Distribution par catégorie exacte")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Pages"
	chart.save(CLEAN_CATEGORIES_VIZ)

	# Maybe slightly more telling, *characters* per category
	chart = (
		distrib.plot.bar(
			x="pubyear",
			y="characters",
			color="pubyear",
		)
		.properties(width=1024, title="Distribution par catégorie exacte")
		.configure_scale(zero=False)
		.configure_axisX(tickMinStep=1)
	)
	chart.encoding.x.title = "Catégorie"
	chart.encoding.y.title = "Signes"
	chart.save(CLEAN_CATEGORIES_VIZ.with_stem(CLEAN_CATEGORIES_VIZ.stem + "-chars"))

	logger.success("Plot generation complete.")


def plot_gold_categories_distribution() -> None:
	"""
	Class distribution plot (i.e., publication year, in 50 year intervals)
	"""

	logger.info("Generating categorical distribution plot from final data...")

	lf = pl.scan_parquet(FULL_DATASET)

	distrib = (
		# We don't need any other columns
		lf.select("semicentury", "text")
		# Duh'
		.group_by("semicentury")
		# Compute the amount of rows per group (i.e., pages)
		# Then the the amount of characters per group (each group is an aggregate of rows)
		.agg(pl.len().alias("pages"), pl.col("text").str.len_chars().sum().alias("characters"))
		.collect()
	)

	# Pages (i.e., rows) per individual category distribution
	chart = (
		alt.Chart(distrib)
		.encode(
			x="pages:Q",
			y="semicentury:N",
			text="pages:Q",
		)
		.properties(
			title="Distribution par classe",
		)
	)
	chart.encoding.x.title = "Nombre d'articles"
	chart.encoding.y.title = "Classe"
	chart = chart.mark_bar(tooltip=True) + chart.mark_text(align="left", dx=2)
	chart.save(GOLD_CATEGORIES_VIZ)

	# Maybe slightly more telling, *characters* per category
	chart = (
		alt.Chart(distrib)
		.encode(
			x="characters:Q",
			y="semicentury:N",
			text="characters:Q",
		)
		.properties(
			title="Distribution par classe",
		)
	)
	chart.encoding.x.title = "Signes"
	chart.encoding.y.title = "Classe"
	chart = chart.mark_bar(tooltip=True) + chart.mark_text(align="left", dx=2)
	chart.save(CLEAN_CATEGORIES_VIZ.with_stem(GOLD_CATEGORIES_VIZ.stem + "-chars"))

	logger.success("Plot generation complete.")


@app.command()
def main() -> None:
	plot_raw_categories_distribution()
	plot_clean_categories_distribution()
	plot_gold_categories_distribution()


if __name__ == "__main__":
	app()
