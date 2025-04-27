#!/usr/bin/env python3

from io import RawIOBase
import marshal
from pathlib import Path
import re
from typing import Iterator

from rich.pretty import pprint
import rich.progress
import wikitextparser as wtp
import zstandard as zstd

BASE_DIR = Path(__file__).parent.resolve()
PAGE_ARTICLES_PATH = BASE_DIR / "raw" / "frwikisource-current.dicts.zst"

NAMESPACE_RE = re.compile(r"^\w+:")


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
	# Skip every page w/ a namespace
	if NAMESPACE_RE.match(title):
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

	# Check templates for TextQuality
	quality = None
	for template in parsed.templates:
		if template.name != "TextQuality":
			continue

		# Strip the %
		value = template.arguments[0].value
		# c.f., https://fr.wikisource.org/wiki/Aide:Qualit%C3%A9_des_textes
		if value == "Textes validés":
			quality = 100
		else:
			quality = value[:-1]

	# Convert to plain text
	# NOTE: This may be a *tad* aggressive... ;'(
	text = parsed.plain_text()

	# Some page have actual content between comment tags... >_<"
	# for comment in parsed.comments:
	# 	pprint(comment)
	# NOTE: Still includes some syntax elements (markdown-esque, as well as the link titles, without the special markup)

	page = {
		"title": data["title"],
		"categories": categories,
		"quality": quality,
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
					# pprint(page)
					continue

				# pprint(page)
				# pprint(data)
				page = parse_page(data)
				pprint(page)

				i += 1
				if i > 200:
					break


if __name__ == "__main__":
	main()
