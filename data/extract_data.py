#!/usr/bin/env python3
#
# Initial data extraction pass.
# NOTE: Beware, this will take *a while* (~30 minutes, at least twice that with verbose logging).
#

from collections import defaultdict
from io import RawIOBase
import marshal
from pathlib import Path
import re
from typing import Iterator

from loguru import logger
import numpy as np
import pandas as pd
from rich.console import Console
from rich.pretty import pprint
import rich.progress
from rich.progress import track
from rich.text import Text
import wikitextparser as wtp
from wikitextparser._wikitext import WikiText
import zstandard as zstd

# Enable CoW in Pandas
pd.options.mode.copy_on_write = True

BASE_DIR = Path(__file__).parent.resolve()
PAGE_ARTICLES_PATH = BASE_DIR / "raw" / "frwikisource-current.dicts.zst"
RAW_PARQUET_PATH = BASE_DIR / "interim" / "frwikisource-current.parquet"

# c.f., the namespaces element at the top of the XML dump
WS_FR_NAMESPACES = set(
	{
		"Média:",
		"Spécial:",
		"Discussion:",
		"Utilisateur:",
		"Discussion utilisateur:",
		"Wikisource:",
		"Discussion Wikisource:",
		"Fichier:",
		"Discussion fichier:",
		"MediaWiki:",
		"Discussion MediaWiki:",
		"Modèle:",
		"Discussion modèle:",
		"Aide:",
		"Discussion aide:",
		"Catégorie:",
		"Discussion catégorie:",
		"Transwiki:",
		"Discussion Transwiki:",
		"Auteur:",
		"Discussion Auteur:",
		# NOTE: We want these:
		#       they contain the actual data that gets dynamically embedded via Page templates and <pages/> elements...
		#       i.e., model is proofread-page
		# "Page:",
		"Discussion Page:",
		"Portail:",
		"Discussion Portail:",
		# model is proofread-index
		# NOTE: We also want to pull the publication date from these...
		#       (Possibly tag it differently (e.g., Pub_$date), in case it conflicts with the existing categories?)
		# "Livre:",
		"Discussion Livre:",
		"TimedText:",
		"TimedText talk:",
		"Module:",
		"Discussion module:",
		"Sujet:",
	}
)

PQ_RE = re.compile(r"<pagequality [^>]+/>")
PQ_LEVEL_RE = re.compile(r"level=\"(\d)\"")
PAGES_RE = re.compile(r"<pages [^>]+/>")
PAGES_INDEX_RE = re.compile(r"index=\"([^\"]+)\"")
# NOTE: ranges are not uncommon (and can span a few centuries :/), so allow that...
PUBYEAR_RE = re.compile(r"(\d{4})(-\d{4})?")

# NOTE: That's not enough to get rid of most of the ToC pages...
PAGE_LEN_THRESHOLD = 384

# Pages under the Page: namespace do *not* have categories, so we try to stitch things back together...
BOOK_CATEGORIES: dict[str, set[str]] = defaultdict(set)


def page_gen(f: RawIOBase) -> Iterator[dict]:
	try:
		while True:
			_, page = marshal.load(f)
			yield page
	except EOFError:
		pass


def page_extract(page: dict) -> dict | None:
	# pprint(page)

	if "title" not in page:
		# e.g., First item
		return None

	title = page["title"]
	logger.opt(colors=True).info(f"Processing <blue>{title}</blue>")

	# Skip every page w/ a namespace
	for ns in WS_FR_NAMESPACES:
		if title.startswith(ns):
			logger.warning("Unwanted namespace")
			return None

	if page["revision"]["format"] != "text/x-wiki":
		# e.g., CSS
		logger.warning("Not a wikitext page")
		return None

	if "#text" not in page["revision"]["text"]:
		# e.g., :?
		logger.warning("No text")
		return None

	text = page["revision"]["text"]["#text"]
	# Skip redirs
	if text.startswith("#REDIRECTION"):
		logger.warning("Is a redirection")
		return None

	# TODO: Unify dates
	# TODO: Try to quantify freqs of cats

	# Pull title & raw text
	data = {
		"title": title,
		"text": text,
	}

	return data


def parse_livre(parsed: WikiText, book_title: str) -> None:
	for template in parsed.templates:
		key = template.name.lower()
		if "proofreadpage_index_template" not in key:
			continue

		for argument in template.arguments:
			# Annee: Année d’édition
			# Publication: Publication originale
			if argument.name not in ("Annee", "Publication"):
				continue

			# Extract numerical values only...
			m = PUBYEAR_RE.search(argument.value)
			if m:
				logger.opt(colors=True).info(f"Pulled a publication date from <red>{book_title}</red>")
				BOOK_CATEGORIES[book_title].add(m.group(0))


def parse_page(data: dict) -> dict:
	parsed = wtp.parse(data["text"])
	title = data["title"]

	# Convert to plain text
	# NOTE: This may be a *tad* aggressive... ;'(
	text = parsed.plain_text()

	# Some page have actual content between comment tags... >_<"
	# for comment in parsed.comments:
	# 	pprint(comment)
	# NOTE: Still includes some syntax elements (markdown-esque, as well as the link titles, without the special markup)

	categories = set()
	# Check links for Categories
	for link in parsed.wikilinks:
		elts = link.title.split(":")
		if len(elts) < 2:
			continue

		key, value = elts[0], elts[1]
		ci_key = key.lower()
		if ci_key == "catégorie" or ci_key == "category":
			value = value.strip()
			if value:
				categories.add(value.strip())

		# Drop the links from the actual text. This is obviously particularly critical for the categories, lol ;).
		text = text.replace(f"{key}:{value}", "")
		# NOTE: In the same vein, some front-matter or ToC may include dates, that might be a problem for us...
		# NOTE: So can the title, for that matter...

	# TODO: Do we want to keep stuff that doesn't have a category?
	#       We obviously can't use it for training, but it cooouuuld maybe be useful during inference?

	# Handle proofread-index pages (to pickup the publication date)
	if title.startswith("Livre:"):
		return parse_livre(parsed, title[6:])

	# Skip pages that are dynamically generated from single djvu pages...
	if "<pages " in parsed.string:
		logger.warning("Embeds content via the pages element")
		# NOTE: Try to use the actual index value, which should match the Page: pages...
		m = PAGES_RE.search(parsed.string)
		if m:
			m = PAGES_INDEX_RE.search(m.group(0))
			if m:
				book_title = m.group(1)

				# Avoid purely numeric titles (this should be much less prone to bogus entries than Page templates)
				if book_title.isnumeric():
					book_title = title
				logger.opt(colors=True).info(f"From <red>{book_title}</red>")
				BOOK_CATEGORIES[book_title] |= categories
		return None

	# Check templates for TextQuality
	quality = None
	for template in parsed.templates:
		key = template.name.lower()
		# Much like the HTML variant above, skip pages that use a template to dynamically embded single djvu pages...
		if key == "page":
			logger.warning("Embeds content via the Page template")
			book_title = template.arguments[0].value

			# Avoid purely numeric titles (in particular, there's a bogus {{Page:24}} somewhere...)
			if book_title.isnumeric():
				book_title = title
			logger.opt(colors=True).info(f"From <red>{book_title}</red>")
			BOOK_CATEGORIES[book_title] |= categories
			return None

		if key != "textquality":
			continue

		value = template.arguments[0].value
		# c.f., https://fr.wikisource.org/wiki/Aide:Qualit%C3%A9_des_textes
		if value == "Textes validés":
			quality = 100
		else:
			# Strip the %
			quality = int(value[:-1])

	# Skip smol pages
	if len(text) < PAGE_LEN_THRESHOLD:
		logger.warning("Is below the length threshold")
		return None

	# Check the pagequality element, too...
	# NOTE: Possibly only if data["model"] is "proofread-page"?
	#       (We don't currently save that field in page_extract, though ;)).
	#       You should only find proofread-page models in the Page namespace, anyway.
	#       (Conversely, proofread-index models are in the Livre namespace, which we skip already).
	if not quality:
		if "<pagequality " in parsed.string:
			m = PQ_RE.search(parsed.string)
			if m:
				m = PQ_LEVEL_RE.search(m.group(0))
				if m:
					# Scale is 0 to 4, make it match TextQuality
					quality = int(m.group(1)) * 25

	# Skip unknown quality (because it's often disambiguation pages)
	if not quality:
		logger.warning("Low TextQuality")
		return None

	# Try to restore categories on Page: pages...
	if title.startswith("Page:"):
		for book_title, cats in BOOK_CATEGORIES.items():
			if title[5:].startswith(book_title):
				logger.opt(colors=True).info(f"Restored categories from <cyan>{book_title}</cyan>")
				categories |= cats
				break

	# Warn if we found no categories...
	if not bool(categories):
		logger.warning("No categories were found!")

	page = {
		"title": data["title"],
		"categories": categories,
		"quality": quality,
		"text": text,
	}
	return page


def main() -> None:
	pages = []
	with rich.progress.open(PAGE_ARTICLES_PATH, "rb", console=console) as fh:
		dctx = zstd.ZstdDecompressor()
		with dctx.stream_reader(fh) as reader:
			for page in page_gen(reader):
				data = page_extract(page)
				if not data:
					# pprint(page)
					continue

				# pprint(page)
				# pprint(data)
				page = parse_page(data)
				if page:
					# pprint(page)
					pages.append(page)
					logger.opt(colors=True).info(f"Extracted <green>{page['title']}</green>")
	logger.info(f"Extracted {len(pages)} pages")

	# NOTE: Given that we cannot guarantee the order in which we parse pages,
	#       we need to do another pass to restore categories from BOOK_CATEGORIES...
	#       i.e., We're likely to have seen most of the Page: pages *before*
	#       we saw the page that embeds them from which we could pull categories...
	logger.info("Restoring categories on Page: pages...")
	for page in track(pages, console=console, description="Processing..."):
		title = page["title"]
		if not title.startswith("Page:"):
			continue

		categories = page["categories"]
		for book_title, cats in BOOK_CATEGORIES.items():
			if title[5:].startswith(book_title):
				logger.opt(colors=True).info(
					f"Restored categories to <green>{title}</green> from <cyan>{book_title}</cyan>"
				)
				categories |= cats
				break

	# Convert to a DataFrame
	logger.info("Building a dataframe...")
	df = pd.DataFrame(pages)

	# Use appropriate datatypes...
	# NOTE: We miiiight actually want to keep everything except quality as native Python objects, we'll see...
	df = df.astype(
		{
			"title": "string",
			"quality": np.uint8,  # "category",
			"text": "string",
		}
	)
	# This feels stupid... Then again, pd.array doesn't handle sets as input anyway...
	# NOTE: This apparently confuses PyArrow during the parquet dump later :?
	# df["categories"] = df["categories"].apply(lambda x: pd.array(list(x), dtype="string"))
	# NOTE: Sets also happen to be mutable, so unhashable, which is annoying for unique()...
	#       Consider using a tuple instead:
	#       df["categories"] = df["categories"].apply(lambda x: tuple(x))
	# NOTE: Thankfully, this doesn't matter much, because we switch to Polars for the rest of the project,
	#       and Polars generally tends towards the One Obvious Way to do stuff
	#       (in this particular case, it groks this as a List of strrings without jumping through any hoops).

	pprint(df)

	# Store in parquet
	logger.info("Dumping to disk...")
	df.to_parquet(RAW_PARQUET_PATH, compression="zstd")


# c.f., https://github.com/Delgan/loguru/issues/444#issuecomment-2507148185
console = Console(stderr=True)
logger.configure(
	handlers=[
		{
			"sink": lambda s: console.print(Text.from_ansi(s)),
			# TODO: Make the logging level configurable...
			"level": "ERROR",
			"colorize": console.is_terminal,
		}
	]
)


if __name__ == "__main__":
	main()
