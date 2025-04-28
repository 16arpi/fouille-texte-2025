#!/usr/bin/env python3
#
# Initial data extraction pass.
# NOTE: Beware, this will take *a while* (~30 minutes).
#

from io import RawIOBase
import marshal
from pathlib import Path
from typing import Iterator

import pandas as pd
import re
import rich.progress
from rich.pretty import pprint
import wikitextparser as wtp
import zstandard as zstd

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
		# NOTE: We want these ones:
		#       they contain the actual data that gets dynamically embedded via Page templates and <pages/> elements...
		# "Page:",
		"Discussion Page:",
		"Portail:",
		"Discussion Portail:",
		"Livre:",
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

# NOTE: That's not enough to get rid of most of the ToC pages...
PAGE_LEN_THRESHOLD = 384


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
	pprint(title)
	# Skip every page w/ a namespace
	for ns in WS_FR_NAMESPACES:
		if title.startswith(ns):
			print("Unwanted namespace")
			return None

	if page["revision"]["format"] != "text/x-wiki":
		# e.g., CSS
		print("Not a wikitext page")
		return None

	if "#text" not in page["revision"]["text"]:
		# e.g., :?
		print("No text")
		return None

	text = page["revision"]["text"]["#text"]
	# Skip redirs
	if text.startswith("#REDIRECTION"):
		print("Is a redirection")
		return None

	# TODO: Unify dates
	# TODO: Try to quantify freqs of cats

	# Pull title & raw text
	data = {
		"title": title,
		"text": text,
	}

	return data


def parse_page(data: dict) -> dict:
	parsed = wtp.parse(data["text"])

	# Skip pages that are dynamically generated from single djvu pages...
	if "<pages " in parsed.string:
		print("Embeds content via the pages element")
		return None

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

		key, value = elts[0].lower(), elts[1]
		if key == "catégorie" or key == "category":
			categories.add(value)

		# Drop the links from the actual text. This is obviously particularly critical for the categories, lol ;).
		text = text.replace(f"{key}:{value}", "")
		# NOTE: In the same vein, some front-matter or ToC may include dates, that might be a problem for us...
		# NOTE: So can the title, for that matter...

	# TODO: Do we want to keep stuff that doesn't have a category?
	#       We obviously can't use it for training, but it cooouuuld maybe be useful during inference?

	# Skip smol pages
	if len(text) < PAGE_LEN_THRESHOLD:
		print("Is below the length threshold")
		return None

	# Check templates for TextQuality
	quality = None
	for template in parsed.templates:
		# Much like the HTML variant above, skip pages that use a template to dynamically embded single djvu pages...
		if template.name.lower() == "page":
			print("Embeds content via the Page template")
			return None

		if template.name.lower() != "textquality":
			continue

		value = template.arguments[0].value
		# c.f., https://fr.wikisource.org/wiki/Aide:Qualit%C3%A9_des_textes
		if value == "Textes validés":
			quality = 100
		else:
			# Strip the %
			quality = int(value[:-1])

	# Check the pagequality element, too...
	# NOTE: Possibly only if data["model"] is "proofread-page"?
	#       (We don't currently save that field in page_extract, though ;)).
	if not quality:
		if "<pagequality " in parsed.string:
			m = PQ_RE.search(parsed.string)
			if m:
				m = PQ_LEVEL_RE.search(m.group(0))
				if m:
					# Scale is 0 to 4, make it match TextQuality
					quality = int(group(1)) * 25

	# Skip unknown quality (because it's often disambiguation pages)
	if not quality:
		print("Low TextQuality")
		return None

	page = {
		"title": data["title"],
		"categories": categories,
		"quality": quality,
		"text": text,
	}
	return page


def main() -> None:
	pages = []
	with rich.progress.open(PAGE_ARTICLES_PATH, "rb") as fh:
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
					pprint(f"Extracted {page["title"]}")
	print(f"Extracted {len(pages)} pages")

	# Convert to a DataFrame
	print("Building a dataframe...")
	df = pd.DataFrame(pages)

	# Use appropriate datatypes...
	df["title"] = df["title"].astype("string")
	# NOTE: This a set, not a single value :/
	# df["categories"] = df["categories"].astype("category")
	df["quality"] = pd.to_numeric(df["quality"], downcast="unsigned")
	df["text"] = df["text"].astype("string")

	# Store in parquet
	print("Dumping to disk...")
	df.to_parquet(RAW_PARQUET_PATH)


if __name__ == "__main__":
	main()
