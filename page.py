#!/usr/bin/env python3

import marshal
import wikitextparser as wtp
import rich.progress
import zstandard as zstd

from io import RawIOBase
from pathlib import Path
from rich.pretty import pprint
from typing import Iterator

BASE_DIR = Path(__file__).parent.resolve()
PAGE_ARTICLES_PATH = BASE_DIR / "frwikisource-current.dicts.zst"

def page_gen(f: RawIOBase) -> Iterator[dict]:
	try:
		while True:
			_, page = marshal.load(f)
			yield page
	except EOFError:
		pass

def page_extract(page: dict) -> dict | None:
	#pprint(page)

	if "title" not in page:
		# e.g., First item
		return None

	title = page["title"]
	# TODO: Skip every page w/ a namespace?
	if title.startswith("Utilisateur:"):
		return None

	if page["revision"]["format"] != "text/x-wiki":
		# e.g., CSS
		return None

	if "#text" not in page["revision"]["text"]:
		# e.g., :?
		return None

	text = page["revision"]["text"]["#text"]
	# Skip redirs
	if text.startswith("#REDIRECTION"):
		return None

	# TODO: Unify dates
	# TODO: Skip text below a certain length
	# TODO: Check for TextQuality in templates
	# TODO: Try to quantify freqs of cats

	# Pull title & raw text
	data = {
		"title": title,
		"text": text,
	}

	return data

def parse_page(data: dict) -> dict:
	parsed = wtp.parse(data["text"])

	categories = set()
	# Check links for Categories
	for link in parsed.wikilinks:
		elts = link.title.split(":")
		if len(elts) < 2:
			continue

		key, value = elts[0], elts[1]
		if key == "Catégorie" or key == "Catégorie":
			categories.add(value)

	# Convert to plain text
	text = parsed.plain_text()
	# NOTE: Still includes some syntax elements (markdown-esque, as well as the link titles, without the special markup)

	page = {
		"title": data["title"],
		"categories": categories,
		"text": text,
	}
	return page


def main() -> None:
	with rich.progress.open(PAGE_ARTICLES_PATH, "rb") as fh:
		dctx = zstd.ZstdDecompressor()
		with dctx.stream_reader(fh) as reader:
			i = 0
			for page in page_gen(reader):
				data = page_extract(page)
				if not data:
					#pprint(page)
					continue

				#pprint(page)
				#pprint(data)
				page = parse_page(data)
				pprint(page)

				i+=1
				if i > 200:
					break

if __name__ == "__main__":
	main()
