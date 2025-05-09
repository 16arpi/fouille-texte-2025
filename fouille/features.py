#!/usr/bin/env python3


from pathlib import Path
import re

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
import tiktoken as tk
import typer

from fouille.config import PROCESSED_DATA_DIR

app = typer.Typer()

# Arguments
# $1 : csv file of text and semicenturies

TIKTOKEN = tk.get_encoding("o200k_base")
REGEXP = re.compile(r"[^\s\.;,]+")


def anal(str):
	return TIKTOKEN.encode(str)


def regex(str):
	return [a for a in REGEXP.finditer(str)]


def vectorize(input_csv: Path) -> None:
	folder = PROCESSED_DATA_DIR

	print("reading csv")
	data = pd.read_csv(input_csv)
	texts = data["text"]
	cats = data["semicentury"]

	vectorizer = CountVectorizer(analyzer=regex, min_df=0.05)

	print("vectorizing")
	X = vectorizer.fit_transform(texts)

	# data_frame = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
	columns = [TIKTOKEN.decode([m]) for m in vectorizer.get_feature_names_out()]
	columns = vectorizer.get_feature_names_out()

	print("to train/test")
	X_train, X_test, y_train, y_test = train_test_split(X, cats, test_size=0.2, random_state=0)

	print("to csv")
	pd.DataFrame(X_train.toarray(), columns=columns).to_csv(f"{folder}/X_train.csv", index=False)
	pd.DataFrame(X_test.toarray(), columns=columns).to_csv(f"{folder}/X_test.csv", index=False)
	pd.DataFrame(y_train, columns=["semicentury"]).to_csv(f"{folder}/y_train.csv", index=False)
	pd.DataFrame(y_test, columns=["semicentury"]).to_csv(f"{folder}/y_test.csv", index=False)


@app.command()
def main(input_csv: Path) -> None:
	vectorize(input_csv)


if __name__ == "__main__":
	app()
