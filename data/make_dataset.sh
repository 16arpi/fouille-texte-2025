#!/usr/bin/env bash
#
# Download a Wikisource dump, convert each page to a Python dictionary, then marshall and compress the whole thing.
# Beware: requires ~24GB of RAM.
#

# Sanity check
if [[ -z "${VIRTUAL_ENV}" ]] ; then
	>&2 echo "!! Not in a venv"
	exit 1
fi

for tool in wget bzcat zstd ; do
	if ! command -v "${tool}" ; then
		>&2 echo "!! ${tool} is not available"
		exit 1
	fi
done

# We want our paths to be relative to *this* script
# NOTE: Funky syntax to behave when *sourced* by ZSH (not that we do that here...)
SCRIPT_NAME="${BASH_SOURCE[0]-${(%):-%x}}"
SCRIPT_DIR="$(readlink -f "${SCRIPT_NAME%/*}")"

DATA_DIR="${SCRIPT_DIR}"
RAW_DATA_DIR="${DATA_DIR}/raw"
mkdir -p "${RAW_DATA_DIR}"

# Date of the dump (c.f., https://dumps.wikimedia.org/frwikisource/)
DUMP_DATE="20250320"

# Path to the XMLTODICT CLI script
XMLTODICT=".venv/lib/python3.12/site-packages/xmltodict.py"

# Do everything in one pass, the only thing that should touch local storage is the final step.
wget "https://dumps.wikimedia.org/frwikisource/${DUMP_DATE}/frwikisource-${DUMP_DATE}-pages-meta-current.xml.bz2" -O - \
| bzcat - \
| python "${XMLTODICT}" 2 \
| zstd > "${RAW_DATA_DIR}/frwikisource-current.dicts.zst"
